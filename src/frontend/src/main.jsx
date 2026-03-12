/**
 * 🚀 MAIN - Entry Point Principal
 * Versão corrigida com App.jsx
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

// CSS Variables conforme WINDSURF_AGENT.md
const style = document.createElement('style');
style.textContent = `
  :root {
    --bg: #080c0f;
    --bg2: #0e1318;
    --bg3: #141b22;
    --border: #1e2d3d;
    --amber: #f5a623;
    --amber-dim: #b87d1a;
    --green: #4ade80;
    --red: #f87171;
    --text: #c8d8e8;
    --text-dim: #5a7a96;
    --text-bright: #e8f4ff;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'IBM Plex Sans', sans-serif;
  }

  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: var(--sans);
    background: var(--bg);
    color: var(--text);
    overflow: hidden;
  }

  /* Scrollbar styling */
  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: var(--bg2);
  }

  ::-webkit-scrollbar-thumb {
    background: var(--border);
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: var(--amber-dim);
  }

  /* Font imports */
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
`;
document.head.appendChild(style);

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
