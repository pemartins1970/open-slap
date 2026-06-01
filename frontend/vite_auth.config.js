/**
 * 🚀 VITE CONFIG AUTH - Configuração do Vite com Autenticação
 * Proxy para backend com autenticação
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const vitePort = Number(process.env.VITE_PORT || process.env.PORT || 3000);
const backendHost = String(process.env.OPENSLAP_HOST || '127.0.0.1').trim();
const backendPort = String(process.env.OPENSLAP_PORT || '5150').trim();
const backendHttp =
  String(process.env.OPENSLAP_BACKEND_URL || '').trim() ||
  `http://${backendHost}:${backendPort}`;
const backendWs = backendHttp.replace(/^http/i, 'ws');

export default defineConfig({
  plugins: [react()],
  
  // Configuração do servidor de desenvolvimento
  server: {
    port: vitePort,
    strictPort: true,
    host: true, // Permite acesso externo
    proxy: {
      // Proxy para API do backend
      '/api': {
        target: backendHttp,
        changeOrigin: true,
        secure: false,
      },
      // Proxy para WebSocket
      '/ws': {
        target: backendWs,
        ws: true,
        changeOrigin: true,
      },
      // Proxy para endpoints de autenticação
      '/auth': {
        target: backendHttp,
        changeOrigin: true,
        secure: false,
      },
      // Proxy para health check
      '/health': {
        target: backendHttp,
        changeOrigin: true,
        secure: false,
      }
    }
  },
  
  // Configuração de build
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['react-router-dom']
        }
      }
    }
  },
  
  // Configurações de otimização
  optimizeDeps: {
    include: ['react', 'react-dom', 'react-router-dom']
  },
  
  // Variáveis de ambiente
  define: {
    __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0')
  }
});
