const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  splashReady: () => ipcRenderer.send('splash:ready'),
  onStartupStatus: (callback) => ipcRenderer.on('startup:status', (event, status) => callback(status)),
  isElectron: () => true,
  platform: () => process.platform,
  env: () => process.env.NODE_ENV || 'production',
});

console.log('[preload] ✓ Context isolation bridge ready');
