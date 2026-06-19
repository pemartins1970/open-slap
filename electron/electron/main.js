/**
 * Open Slap! Electron Main Process
 */

const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn, exec, execSync } = require('child_process');
const http = require('http');
const fs = require('fs');

const BACKEND_HOST = '127.0.0.1';
const BACKEND_PORT = 5150;
const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
const HEALTH_CHECK_URL = `${BACKEND_URL}/health`;
const isDev = !app.isPackaged;

// Paths
const backendPath = app.isPackaged
  ? path.join(process.resourcesPath, 'backend')
  : path.join(app.getAppPath(), '..', 'backend');

const pythonScriptPath = path.join(backendPath, 'main_auth.py');

let mainWindow, splashWindow, backendProcess;
let startupLog = [];
let currentPythonCmd = null;

function log(msg) {
  const line = `[${new Date().toLocaleTimeString()}] ${msg}`;
  console.log(line);
  startupLog.push(line);
}

function saveDiagnosticLog() {
  const desktopPath = require('os').homedir() + '/Desktop';
  const logPath = path.join(desktopPath, 'openslap_backend_diagnostic.txt');
  const fullLog = startupLog.join('\n');
  
  try {
    fs.writeFileSync(logPath, fullLog, 'utf8');
    console.log(`Diagnostic log saved to: ${logPath}`);
  } catch (err) {
    console.log(`Failed to save diagnostic log: ${err.message}`);
  }
}

async function findPython() {
  return new Promise((resolve) => {
    const candidates = process.platform === 'win32'
      ? ['python', 'py', 'python3']
      : ['python3', 'python'];
    let found = null, checked = 0;
    candidates.forEach((cmd) => {
      exec(process.platform === 'win32' ? `where ${cmd}` : `which ${cmd}`, (err, stdout) => {
        checked++;
        if (!err && stdout.trim() && !found) found = cmd;
        if (checked === candidates.length) resolve(found);
      });
    });
  });
}

async function checkPythonVersion(pythonCmd) {
  return new Promise((resolve) => {
    exec(`${pythonCmd} --version 2>&1`, (err, stdout, stderr) => {
      const output = stdout || stderr || '';
      const match = output.match(/Python (\d+\.\d+)/);
      resolve(match ? match[1] : 'unknown');
    });
  });
}

async function installPythonDependencies(pythonCmd) {
  return new Promise((resolve, reject) => {
    const reqPath = path.join(backendPath, 'requirements.txt');
    log(`Backend path: ${backendPath}`);
    log(`requirements.txt exists: ${fs.existsSync(reqPath)}`);
    log(`main_auth.py exists: ${fs.existsSync(pythonScriptPath)}`);

    if (!fs.existsSync(reqPath)) {
      return reject(new Error(
        `requirements.txt não encontrado em:\n${reqPath}\n\n` +
        `Backend path: ${backendPath}`
      ));
    }

    log('Iniciando pip install...');
    const projectRoot = path.join(backendPath, '..');
    const pipProcess = exec(
      `${pythonCmd} -m pip install -r backend/requirements.txt --quiet`,
      { cwd: projectRoot, maxBuffer: 20 * 1024 * 1024, timeout: 300000 },
      (err, stdout, stderr) => {
        if (err) {
          return reject(new Error(
            `pip install falhou:\n${stderr || err.message}\n\nBackend: ${backendPath}`
          ));
        }
        log('pip install concluído');
        resolve();
      }
    );
    pipProcess.stdout?.on('data', (d) => log(`[pip] ${d.toString().trim()}`));
    pipProcess.stderr?.on('data', (d) => log(`[pip] ${d.toString().trim()}`));
  });
}

async function waitForBackend(maxAttempts = 60, delayMs = 2000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await new Promise((resolve, reject) => {
        const req = http.get(HEALTH_CHECK_URL, (res) => {
          res.statusCode === 200 ? resolve() : reject(new Error(`HTTP ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(3000, () => { req.destroy(); reject(new Error('timeout')); });
      });
      log('Backend health check OK');
      return;
    } catch (err) {
      log(`Health check ${i + 1}/${maxAttempts}: ${err.message}`);
      if (i === maxAttempts - 1) {
        saveDiagnosticLog(); // Salvar log completo na área de trabalho
        throw new Error(
          `Backend não iniciou após ${maxAttempts} tentativas.\n\n` +
          `Últimos logs:\n${startupLog.slice(-10).join('\n')}`
        );
      }
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
}

async function startBackend(pythonCmd) {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(pythonScriptPath)) {
      return reject(new Error(
        `main_auth.py não encontrado em:\n${pythonScriptPath}`
      ));
    }

    // O backend usa imports relativos, precisa ser executado como módulo
    // cwd deve ser o pai do backend (a raiz do projeto)
    const projectRoot = path.join(backendPath, '..');
    
    log(`Project root: ${projectRoot}`);
    log(`Backend path: ${backendPath}`);
    log(`Python script: ${pythonScriptPath}`);
    log(`Spawning: ${pythonCmd} -m backend.main_auth`);
    
    // Verificar se requirements.txt existe
    const reqPath = path.join(backendPath, 'requirements.txt');
    log(`requirements.txt exists: ${fs.existsSync(reqPath)}`);
    
    // Verificar Python path e versão
    log(`Python executable: ${pythonCmd}`);
    log(`Working directory: ${projectRoot}`);
    log(`Environment PYTHONPATH: ${projectRoot}`);
    
    // Listar arquivos no backend
    try {
      const backendFiles = fs.readdirSync(backendPath);
      log(`Backend files: ${backendFiles.slice(0, 10).join(', ')}${backendFiles.length > 10 ? '...' : ''}`);
    } catch (err) {
      log(`Failed to list backend files: ${err.message}`);
    }

    backendProcess = spawn(pythonCmd, ['-m', 'backend.main_auth'], {
      cwd: projectRoot,
      env: {
        ...process.env,
        OPENSLAP_HOST: BACKEND_HOST,
        OPENSLAP_PORT: String(BACKEND_PORT),
        PYTHONUNBUFFERED: '1',
        PYTHONPATH: projectRoot,
      },
      stdio: ['ignore', 'pipe', 'pipe'],
    });

    let stdoutBuffer = '';
    let stderrBuffer = '';

    backendProcess.stdout.on('data', (d) => {
      const data = d.toString().trim();
      stdoutBuffer += data + '\n';
      log(`[backend] ${data}`);
    });
    
    backendProcess.stderr.on('data', (d) => {
      const data = d.toString().trim();
      stderrBuffer += data + '\n';
      log(`[backend-err] ${data}`);
    });

    backendProcess.on('error', (err) => {
      log(`Python process error: ${err.message}`);
      reject(new Error(`Erro ao iniciar Python:\n${err.message}\n\nStderr:\n${stderrBuffer}`));
    });

    backendProcess.on('exit', (code, signal) => {
      log(`Backend process exit - code: ${code}, signal: ${signal}`);
      if (code !== 0 && code !== null) {
        const errorMsg = `Backend saiu com código ${code}\n\nStdout:\n${stdoutBuffer}\n\nStderr:\n${stderrBuffer}`;
        log(errorMsg);
        saveDiagnosticLog(); // Salvar log completo na área de trabalho
        reject(new Error(errorMsg));
      }
    });

    // Aguarda 5s para o processo iniciar, depois começa health checks
    setTimeout(async () => {
      try {
        // Verificar se o processo ainda está rodando
        if (!backendProcess || backendProcess.killed) {
          return reject(new Error('Backend process died during startup\n\nStderr:\n' + stderrBuffer));
        }
        
        await waitForBackend();
        resolve();
      } catch (err) {
        reject(new Error(`${err.message}\n\nStdout:\n${stdoutBuffer}\n\nStderr:\n${stderrBuffer}`));
      }
    }, 5000);
  });
}

function killBackend() {
  if (backendProcess && !backendProcess.killed) {
    if (process.platform === 'win32') {
      exec(`taskkill /PID ${backendProcess.pid} /T /F`);
    } else {
      backendProcess.kill('SIGTERM');
    }
  }
}

// --- Rollback SPEC-RESET-001 Nível 2 ---
function getProjectRoot() {
  return path.join(backendPath, '..');
}

function takeRollbackSnapshot(target) {
  const projectRoot = getProjectRoot();
  const backupRoot = path.join(projectRoot, 'data', 'backups');
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const safeTarget = (target || 'rollback').replace(/[^a-zA-Z0-9_-]/g, '_');
  const backupDir = path.join(backupRoot, `${safeTarget}_${timestamp}`);

  fs.mkdirSync(backupDir, { recursive: true });

  const dbFiles = ['auth.db', 'slap.db', 'memory.db', 'conversations.db'];
  const dataDir = path.join(projectRoot, 'data');
  for (const db of dbFiles) {
    const src = path.join(dataDir, db);
    if (fs.existsSync(src)) fs.copyFileSync(src, path.join(backupDir, db));
  }

  try {
    const head = execSync('git rev-parse HEAD', { cwd: projectRoot }).toString().trim();
    fs.writeFileSync(path.join(backupDir, 'HEAD.txt'), head, 'utf8');
  } catch (_) { /* non-fatal */ }

  try {
    const diff = execSync('git diff --name-only', { cwd: projectRoot }).toString().trim();
    if (diff) fs.writeFileSync(path.join(backupDir, 'UNSTAGED_CHANGES.txt'), diff, 'utf8');
  } catch (_) { /* non-fatal */ }

  log(`📦 Snapshot salvo em: ${backupDir}`);
  return backupDir;
}

async function execGitAsync(args) {
  return new Promise((resolve, reject) => {
    exec(`git ${args}`, { cwd: getProjectRoot(), maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
      if (err) return reject(new Error(stderr || err.message));
      resolve(stdout.trim());
    });
  });
}

async function getCommitInfo(ref) {
  try {
    const hash = (await execGitAsync(`rev-parse --short ${ref}`)).trim();
    const date = (await execGitAsync(`log -1 --format=%ci ${ref}`)).trim();
    const subject = (await execGitAsync(`log -1 --format=%s ${ref}`)).trim();
    return { hash, date, subject };
  } catch (_) {
    return null;
  }
}

async function isWorkingTreeClean() {
  try {
    const status = await execGitAsync('status --porcelain');
    return status.length === 0;
  } catch (_) {
    return false;
  }
}

async function hasSchemaMigration(target) {
  try {
    const out = await execGitAsync(`diff --name-only HEAD "${target}" -- backend/migrations/`);
    return out.length > 0;
  } catch (_) {
    return false;
  }
}

async function hasRequirementsChanged(target) {
  try {
    const out = await execGitAsync(`diff --name-only HEAD "${target}" -- backend/requirements.txt`);
    return out.length > 0;
  } catch (_) {
    return false;
  }
}

async function performRollback(target) {
  const pythonCmd = currentPythonCmd || await findPython();
  if (!pythonCmd) throw new Error('Python não encontrado no PATH.');
  if (!target) throw new Error('Alvo do rollback não especificado (forneça um commit SHA, tag ou ref).');

  // Abort se working tree estiver suja
  log('🔍 Verificando working tree...');
  if (!(await isWorkingTreeClean())) {
    throw new Error(
      'Rollback ABORTADO: há mudanças não commitadas no working tree.\n\n' +
      'Faça commit ou descarte as mudanças antes de executar o rollback.\n' +
      'Um snapshot dos bancos foi salvo em: ' + takeRollbackSnapshot(target)
    );
  }

  log(`🔄 Rollback iniciado para: ${target}`);
  const backupDir = takeRollbackSnapshot(target);

  // Verificar migração de schema — hard abort
  log('🔍 Verificando migrações de schema...');
  if (await hasSchemaMigration(target)) {
    log('❌ Migração de schema detectada — abortando rollback');
    throw new Error(
      `Rollback ABORTADO: migração de schema detectada entre HEAD e ${target}.\n` +
      `Backup salvo em: ${backupDir}\n` +
      `Rollback de código com mudança de schema não é seguro.`
    );
  }

  // Checkout do alvo
  log(`📥 Checkout ${target}...`);
  await execGitAsync(`checkout ${target}`);
  log(`📥 Checkout concluído: ${await execGitAsync('rev-parse HEAD')}`);

  // Reinstalar dependências se requirements.txt mudou
  if (await hasRequirementsChanged(target)) {
    log('📦 requirements.txt mudou — reinstalando dependências...');
    await installPythonDependencies(pythonCmd);
  } else {
    log('✓ requirements.txt inalterado — pulando pip install');
  }

  // Kill + restart backend
  log('🛑 Parando backend...');
  killBackend();
  await new Promise((r) => setTimeout(r, 2000));

  log('🚀 Reiniciando backend...');
  await startBackend(pythonCmd);
  await waitForBackend(60, 2000);

  log(`✅ Rollback concluído para ${target}`);
  const commitInfo = await getCommitInfo(target).catch(() => null);
  return { success: true, backupDir, target, commitInfo };
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 600, height: 400,
    show: false, frame: false,
    backgroundColor: '#1a1a2e',
    webPreferences: {
      nodeIntegration: false, contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  splashWindow.loadURL(`file://${path.join(__dirname, '../splash.html')}`);
  splashWindow.once('ready-to-show', () => splashWindow.show());
}

function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1400, height: 900, minWidth: 1000, minHeight: 600,
    show: false,
    webPreferences: {
      nodeIntegration: false, contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });
  mainWindow.loadURL(BACKEND_URL);
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    if (isDev) mainWindow.webContents.openDevTools();
  });
  mainWindow.on('closed', () => { mainWindow = null; });
}

function createMenu() {
  const template = [
    { label: 'File', submenu: [{ label: 'Exit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }] },
    { label: 'View', submenu: [
      { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: () => mainWindow?.webContents.reload() },
      { label: 'DevTools', accelerator: 'CmdOrCtrl+Shift+I', click: () => mainWindow?.webContents.toggleDevTools() },
    ]},
    { label: 'Rollback', submenu: [
      { label: 'Rollback para commit anterior (HEAD^1)', click: () => {
        const win = BrowserWindow.getFocusedWindow();
        getCommitInfo('HEAD^1').then((info) => {
          const targetLabel = info
            ? `HEAD^1 — ${info.hash} (${info.date.slice(0, 10)})\n"${info.subject}"`
            : 'HEAD^1 (commit anterior)';
          dialog.showMessageBox(win, {
            type: 'warning', buttons: ['Cancelar', 'Rollback'],
            defaultId: 0, cancelId: 0,
            title: 'Rollback de Código',
            message: `Reverter para: ${targetLabel}`,
            detail: '⚠️ V1 — apenas HEAD^1 como alvo.\n' +
              'O backend será parado e reiniciado.\n' +
              'Um snapshot dos bancos será salvo em data/backups/.',
          }).then(({ response }) => {
            if (response !== 1) return;
            performRollback('HEAD^1')
              .then((r) => dialog.showMessageBox(win, {
                type: 'info', title: 'Rollback Concluído',
                message: `✅ Rollback para ${r.target} OK\n` +
                  `Backup: ${r.backupDir}`,
              }))
              .catch((err) => dialog.showErrorBox('Rollback Falhou', err.message));
          });
        });
      }},
    ]},
    { label: 'Help', submenu: [{ label: 'About', click: () => {
      dialog.showMessageBox(mainWindow, {
        type: 'info', title: 'About Slap!',
        message: 'Slap! Desktop Assistant',
        detail: `Version 2.2.3\n\nBackend: ${backendPath}\n\nhttps://github.com/pemartins1970/open-slap`,
      });
    }}]},
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.on('ready', async () => {
  try {
    createSplashWindow();
    createMenu();

    ipcMain.handle('rollback:execute', async (_event, { target }) => {
      try {
        const result = await performRollback(target);
        return result;
      } catch (err) {
        return { success: false, error: err.message };
      }
    });

    const updateSplash = (msg) => {
      log(msg);
      splashWindow?.webContents.send('startup:status', msg);
    };

    updateSplash('🔍 Procurando Python...');
    currentPythonCmd = await findPython();
    const pythonCmd = currentPythonCmd;
    if (!pythonCmd) {
      throw new Error(
        'Python não encontrado no PATH.\n\n' +
        'Instale Python 3.11+ de https://www.python.org/downloads/\n' +
        'e marque "Add Python to PATH" durante a instalação.'
      );
    }

    const version = await checkPythonVersion(pythonCmd);
    updateSplash(`✓ Python ${version} encontrado (${pythonCmd})`);

    updateSplash('📦 Instalando dependências Python...\n(pode demorar alguns minutos na primeira vez)');
    await installPythonDependencies(pythonCmd);
    updateSplash('✓ Dependências prontas');

    updateSplash('🚀 Iniciando backend...');
    await startBackend(pythonCmd);
    updateSplash('✓ Backend pronto');

    await new Promise((r) => setTimeout(r, 500));
    createMainWindow();

    setTimeout(() => {
      if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    }, 2000);

    // Salvar log de diagnóstico de sucesso também (para debug)
    saveDiagnosticLog();
    log(`✅ Startup completo! Log salvo em: ${require('os').homedir()}\\Desktop\\openslap_backend_diagnostic.txt`);

  } catch (err) {
    log(`❌ ${err.message}`);
    saveDiagnosticLog(); // Salvar log completo na área de trabalho
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    dialog.showErrorBox('Erro ao iniciar Slap!', err.message + '\n\nLog de diagnóstico salvo em:\n' + require('os').homedir() + '\\Desktop\\openslap_backend_diagnostic.txt');
    killBackend();
    app.quit();
  }
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', killBackend);

process.on('uncaughtException', (err) => {
  log(`❌ Uncaught: ${err.message}`);
  saveDiagnosticLog(); // Salvar log completo na área de trabalho
  dialog.showErrorBox('Erro Fatal', err.message + '\n\nLog de diagnóstico salvo em:\n' + require('os').homedir() + '\\Desktop\\openslap_backend_diagnostic.txt');
});
