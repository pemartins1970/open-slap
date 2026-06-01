import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

const vitePort = Number(process.env.VITE_PORT || process.env.PORT || 3000);
const backendHost = String(process.env.OPENSLAP_HOST || '127.0.0.1').trim();
const backendPort = String(process.env.OPENSLAP_PORT || '5150').trim();
const backendHttp = String(process.env.OPENSLAP_BACKEND_URL || '').trim() || `http://${backendHost}:${backendPort}`;
const backendWs = backendHttp.replace(/^http/i, 'ws');

export default defineConfig({
  plugins: [react()],
  server: { port: vitePort, strictPort: true, host: true, proxy: { '/api': { target: backendHttp, changeOrigin: true, secure: false }, '/ws': { target: backendWs, ws: true, changeOrigin: true, secure: false }, '/auth': { target: backendHttp, changeOrigin: true, secure: false }, '/health': { target: backendHttp, changeOrigin: true, secure: false } } },
  build: { outDir: 'dist', sourcemap: false, rollupOptions: { input: { auth: resolve('src/App_auth_modular.jsx') }, output: { manualChunks: { vendor: ['react', 'react-dom'], router: ['react-router-dom'] } } } },
  optimizeDeps: { include: ['react', 'react-dom', 'react-router-dom'] },
  define: { __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0') }
});
