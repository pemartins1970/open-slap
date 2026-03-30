/**
 * 🚀 VITE CONFIG AUTH - Configuração do Vite com Autenticação
 * Proxy para backend com autenticação
 */

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  
  // Configuração do servidor de desenvolvimento
  server: {
    port: 3000,
    host: true, // Permite acesso externo
    proxy: {
      // Proxy para API do backend
      '/api': {
        target: 'http://127.0.0.1:5150',
        changeOrigin: true,
        secure: false,
      },
      // Proxy para WebSocket
      '/ws': {
        target: 'ws://127.0.0.1:5150',
        ws: true,
        changeOrigin: true,
      },
      // Proxy para endpoints de autenticação
      '/auth': {
        target: 'http://127.0.0.1:5150',
        changeOrigin: true,
        secure: false,
      },
      // Proxy para health check
      '/health': {
        target: 'http://127.0.0.1:5150',
        changeOrigin: true,
        secure: false,
      }
    }
  },
  
  // Configuração de build
  build: {
    outDir: 'dist',
    sourcemap: true,
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
