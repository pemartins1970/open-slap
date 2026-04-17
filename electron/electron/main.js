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

// Paths — resolves correctly for dev and packaged app
const backendPath = app.isPackaged
  ? path.join(process.resourcesPath, 'backend')
  : path.join(app.getAppPath(), '..', 'backend');

const pythonScriptPath = path.join(backendPath, 'main_auth.py');

let mainWindow, splashWindow, backendProcess;

function log(msg) {
  console.log(`[${new Date().toLocaleTimeString()}] ${msg}`);
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
        if (!err && !found) found = cmd;
        if (checked === candidates.length) resolve(found);
      });
    });
  });
}

async function checkPythonVersion(pythonCmd) {
  return new Promise((resolve) => {
    exec(`${pythonCmd} --version`, (err, stdout) => {
      if (err) return resolve(null);
      const match = stdout.match(/Python (\d+\.\d+)/);
      resolve(match ? match[1] : null);
    });
  });
}

async function waitForBackend(maxAttempts = 30, delayMs = 1000) {
  for (let i = 0; i < maxAttempts; i++) {
    try {
      await new Promise((resolve, reject) => {
        http.get(HEALTH_CHECK_URL, (res) => {
          res.statusCode === 200 ? resolve() : reject(new Error(`Status ${res.statusCode}`));
        }).on('error', reject);
      });
      return;
    } catch (err) {
      log(`Health check ${i + 1}/${maxAttempts}: ${err.message}`);
      if (i === maxAttempts - 1) throw new Error(`Backend failed to start after ${maxAttempts} attempts.`);
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
}

async function installPythonDependencies(pythonCmd) {
  return new Promise((resolve, reject) => {
    const reqPath = path.join(backendPath, 'requirements.txt');
    if (!fs.existsSync(reqPath)) return reject(new Error(`requirements.txt not found: ${reqPath}`));
    const pipProcess = exec(
      `${pythonCmd} -m pip install -r requirements.txt`,
      { cwd: backendPath, maxBuffer: 10 * 1024 * 1024 },
      (err, stdout, stderr) => {
        if (err) return reject(new Error(`pip install failed:\n${stderr || err.message}`));
        resolve();
      }
    );
    pipProcess.stdout.on('data', (d) => log(`[pip] ${d.toString().trim()}`));
    pipProcess.stderr.on('data', (d) => log(`[pip-err] ${d.toString().trim()}`));
  });
}

async function startBackend(pythonCmd) {
  return new Promise((resolve, reject) => {
    if (!fs.existsSync(pythonScriptPath)) {
      return reject(new Error(`main_auth.py not found: ${pythonScriptPath}`));
    }
    backendProcess = spawn(pythonCmd, [pythonScriptPath], {
      cwd: backendPath,
      env: { ...process.env, OPENSLAP_HOST: BACKEND_HOST, OPENSLAP_PORT: BACKEND_PORT, PYTHONUNBUFFERED: '1' },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    backendProcess.stdout.on('data', (d) => log(`[backend] ${d.toString().trim()}`));
    backendProcess.stderr.on('data', (d) => log(`[backend-err] ${d.toString().trim()}`));
    backendProcess.on('error', (err) => reject(new Error(`Spawn error: ${err.message}`)));
    setTimeout(async () => {
      try { await waitForBackend(); resolve(); }
      catch (err) { reject(err); }
    }, 1500);
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
        detail: 'Version 2.1.1\n\nhttps://github.com/pemartins1970/open-slap',
      });
    }}]},
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

app.on('ready', async () => {
  try {
    createSplashWindow();
    createMenu();

    const updateSplash = (msg) => splashWindow?.webContents.send('startup:status', msg);

    updateSplash('🔍 Procurando Python...');
    const pythonCmd = await findPython();
    if (!pythonCmd) throw new Error('Python não encontrado. Instale Python 3.11+ e adicione ao PATH.');

    const version = await checkPythonVersion(pythonCmd);
    updateSplash(`✓ Python ${version} encontrado`);

    updateSplash('📦 Verificando dependências...');
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

  } catch (err) {
    log(`❌ ${err.message}`);
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    dialog.showErrorBox('Erro ao iniciar Open Slap!', err.message);
    killBackend();
    app.quit();
  }
});

app.on('window-all-closed', () => { if (process.platform !== 'darwin') app.quit(); });
app.on('before-quit', killBackend);

process.on('uncaughtException', (err) => {
  log(`❌ Uncaught: ${err.message}`);
  dialog.showErrorBox('Erro Fatal', err.message);
});
