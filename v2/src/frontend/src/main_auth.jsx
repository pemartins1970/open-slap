/**
 * 🚀 MAIN AUTH - Entry Point com Autenticação
 * Versão principal segundo WINDSURF_AGENT.md
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App_auth.jsx';

// CSS Variables conforme WINDSURF_AGENT.md
const style = document.createElement('style');
style.textContent = `
  /* ── Theme: Deep Space (default) ── */
  :root {
    --bg: #080c0f;
    --bg2: #0e1318;
    --bg3: #141b22;
    --border: #1e2d3d;
    --accent: #f5a623;
    --accent-dim: #b87d1a;
    --amber: #f5a623;
    --amber-dim: #b87d1a;
    --blue: #4a9eff;
    --green: #4ade80;
    --red: #f87171;
    --text: #c8d8e8;
    --text-dim: #5a7a96;
    --text-bright: #e8f4ff;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'IBM Plex Sans', sans-serif;
  }

  /* ── Theme overrides (applied via data-theme on <html>) ── */

  [data-theme="midnight-blue"] {
    --bg: #07080f;
    --bg2: #0d1020;
    --bg3: #131828;
    --border: #1e2a4a;
    --accent: #4a9eff;
    --accent-dim: #2e6bc4;
    --amber: #4a9eff;
    --amber-dim: #2e6bc4;
    --text: #c5d5f0;
    --text-dim: #5070a0;
    --text-bright: #e8f0ff;
  }

  [data-theme="forest"] {
    --bg: #080f09;
    --bg2: #0d1710;
    --bg3: #121f15;
    --border: #1a3020;
    --accent: #4ade80;
    --accent-dim: #22a050;
    --amber: #4ade80;
    --amber-dim: #22a050;
    --text: #c0dcc5;
    --text-dim: #4a7a55;
    --text-bright: #e0f5e5;
  }

  [data-theme="crimson"] {
    --bg: #0f0808;
    --bg2: #1a0d0d;
    --bg3: #221212;
    --border: #3d1a1a;
    --accent: #f87171;
    --accent-dim: #c43030;
    --amber: #f87171;
    --amber-dim: #c43030;
    --text: #e0c5c5;
    --text-dim: #7a4a4a;
    --text-bright: #f5e0e0;
  }

  [data-theme="slate"] {
    --bg: #0c0e12;
    --bg2: #13161e;
    --bg3: #1a1e28;
    --border: #2a2f3d;
    --accent: #9b8cff;
    --accent-dim: #6b5cc4;
    --amber: #9b8cff;
    --amber-dim: #6b5cc4;
    --text: #c8cce0;
    --text-dim: #5a5e78;
    --text-bright: #e8eaff;
  }

  [data-theme="solarized"] {
    --bg: #001b24;
    --bg2: #00262f;
    --bg3: #00303b;
    --border: #004455;
    --accent: #2aa198;
    --accent-dim: #1a7a72;
    --amber: #2aa198;
    --amber-dim: #1a7a72;
    --text: #93a1a1;
    --text-dim: #3d5560;
    --text-bright: #eee8d5;
    --green: #859900;
    --red: #dc322f;
  }

  [data-theme="light"] {
    --bg: #f5f5f5;
    --bg2: #ffffff;
    --bg3: #ececec;
    --border: #d0d0d0;
    --accent: #d97706;
    --accent-dim: #a35200;
    --amber: #d97706;
    --amber-dim: #a35200;
    --text: #1a1a1a;
    --text-dim: #666666;
    --text-bright: #000000;
    --green: #15803d;
    --red: #dc2626;
  }

  [data-theme="paper"] {
    --bg: #f0ebe0;
    --bg2: #faf5ea;
    --bg3: #e8e0d0;
    --border: #c8bca8;
    --accent: #8b4513;
    --accent-dim: #5a2d0c;
    --amber: #8b4513;
    --amber-dim: #5a2d0c;
    --text: #2c1a0e;
    --text-dim: #7a6050;
    --text-bright: #0a0500;
    --green: #2d6a2d;
    --red: #8b1a1a;
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

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.45; }
  }

  /* ── Mobile layout (≤ 640px) ── */
  @media (max-width: 640px) {
    .slap-layout {
      flex-direction: column !important;
    }
    .slap-sidebar {
      width: 100% !important;
      max-height: 48px;
      overflow: hidden;
      flex-direction: row !important;
      align-items: center;
      padding: 0 8px;
      gap: 4px;
    }
    .slap-sidebar.expanded {
      max-height: 100vh;
      flex-direction: column !important;
      align-items: stretch;
    }
    .slap-sidebar-toggle {
      display: flex !important;
    }
    .slap-main {
      flex: 1;
      min-height: 0;
    }
    .slap-input-row {
      flex-wrap: wrap;
    }
    .slap-expert-bar {
      flex-wrap: wrap;
      font-size: 10px;
    }
    .slap-header-title {
      font-size: 13px !important;
      max-width: 180px !important;
    }
    .slap-conn-status {
      display: none;
    }
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