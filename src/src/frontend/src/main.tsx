import React from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { io, Socket } from 'socket.io-client';

// Components
import App from './App';
import './index.css';

// Socket connection
const socket: Socket = io('http://localhost:3003', {
  transports: ['websocket'],
  upgrade: false,
});

// React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Loading screen
const loadingElement = document.getElementById('loading');
if (loadingElement) {
  loadingElement.style.display = 'none';
}

// Render app
createRoot(
  document.getElementById('root')!
).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <App socket={socket} />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
