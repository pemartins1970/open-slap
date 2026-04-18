/**
 * Open Slap! Electron Main Process
 */

const { app, BrowserWindow, ipcMain, dialog, Menu } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
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
    { label: 'Help', submenu: [{ label: 'About', click: () => {
      dialog.showMessageBox(mainWindow, {
        type: 'info', title: 'About Open Slap!',
        message: 'Open Slap! Desktop Assistant',
        detail: `Version 2.1.1\n\nBackend: ${backendPath}\n\nhttps://github.com/pemartins1970/open-slap`,
      });
    }}]},
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.on('ready', async () => {
  try {
    createSplashWindow();
    createMenu();

    const updateSplash = (msg) => {
      log(msg);
      splashWindow?.webContents.send('startup:status', msg);
    };

    updateSplash('🔍 Procurando Python...');
    const pythonCmd = await findPython();
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
    dialog.showErrorBox('Erro ao iniciar Open Slap!', err.message + '\n\nLog de diagnóstico salvo em:\n' + require('os').homedir() + '\\Desktop\\openslap_backend_diagnostic.txt');
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
