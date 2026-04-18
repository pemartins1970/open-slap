# Slap! — Assistente Inteligente Local (v2.2.5)

[![Version](https://img.shields.io/badge/version-2.2.5-blue.svg)](https://github.com/pemartins1970/open-slap)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](docs/LICENCE.md)
[![Status](https://img.shields.io/badge/status-active-brightgreen.svg)](https://github.com/pemartins1970/open-slap)

> Backend: FastAPI (Python) · Frontend: React + Vite · License: [Apache 2.0](docs/LICENCE.md)

Slap! is a **desktop-local** assistant — a server running on your machine — with real-time chat, support for multiple LLM providers (local and free-tiers included), a full agentic team, and local automation with permissions.

---

## What's in v2.1.1

| Area | What exists |
|------|-------------|
| **Real-time chat** | WebSocket with incremental streaming and connection state |
| **MoE (experts)** | Expert selection by keywords + heuristics; override option |
| **Plan→Build** | Structured plans (`plan` block) + incremental execution/orchestration |
| **Memory** | SQLite + RAG/FTS + heuristics (salience, decay, consolidation) |
| **Connectors** | GitHub, Google Drive/Calendar/Gmail, Telegram (optional) |
| **Security** | JWT, permission settings (OS commands, web retrieval, file write, connectors, system profile) |
| **Interface** | Onboarding, boot screen, themes and **i18n** (PT / EN / ES / AR / ZH) |

---

## Repository Structure

```
open-slap/
├── backend/                  # Python/FastAPI server
├── frontend/                 # React + Vite UI
├── docs/                     # Documentation
├── open-slap-electron-windows/  # Desktop app (Electron)
├── .env.example              # Environment variables template
└── README.md
```

---

## Quick Start

### Requirements
- Python 3.11+
- Node.js 18+

### 1) Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Optional: copy env.example to .env and configure a provider
Copy-Item ..\env.example .env

python main_auth.py
```

Server runs at `http://127.0.0.1:5150` (configurable via `OPENSLAP_HOST`/`OPENSLAP_PORT`).

### 2) Frontend (React/Vite)

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 3) Desktop App (Electron)

Download the latest release from the [Releases page](https://github.com/pemartins1970/open-slap/releases):

| Platform | File |
|----------|------|
| Windows (Installer) | `Open Slap! Setup *.exe` |
| Windows (Portable)  | `Open Slap!-*-portable.exe` |
| macOS               | `Open Slap!-*.dmg` |
| Linux               | `Open Slap!-*.AppImage` |

> Requires Python 3.11+ installed and in PATH.

### 3) Desktop App (Electron)

Download the latest release from the [Releases page](https://github.com/pemartins1970/open-slap/releases):
- `Open-Slap-2.1.1-Setup.exe` — Windows installer
- `Open-Slap-2.1.1-portable.exe` — Windows portable (no install)

> Requires Python 3.11+ installed and in PATH.

---

## Environment Variables

Template: [`.env.example`](.env.example) and [`backend/env.example`](backend/env.example)

```env
# LLM Providers (at least one required)
GEMINI_API_KEYS=your_key
GROQ_API_KEYS=your_key
OPENAI_API_KEY=your_key
OLLAMA_URL=http://localhost:11434   # fully local, no key needed

# Provider fallback order
PROVIDER_ORDER=gemini,groq,ollama,openai

# JWT (auto-generated if not set)
JWT_SECRET=replace_with_long_random_string
```

---

## Architecture

### Memory System (SQLite + RAG/FTS)

```
User Query → [FTS5 + Vector + Recent] → [Re-ranking] → LLM → [Memory Extraction] → SQLite
```

**Hybrid:** SQLite (speed) + FTS5 (exact search) + Embeddings (semantic) + Heuristics (salience, decay, consolidation).

### MoE Routing

6 specialist experts selected by keywords + heuristics, with manual override available.

---

## Testing

```powershell
# Backend
cd backend
pytest -q

# Frontend build check
cd frontend
npm run build
```

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Dev Journal](docs/DEV_JOURNAL.md)
- [Changelog](docs/CHANGELOG.md)
- [License](docs/LICENCE.md)

---

## Security Notes

- Never commit `.env`, `node_modules/`, `dist/`, `__pycache__/`, or local databases (`*.db`, `*.sqlite`).
- Credentials must be treated as ephemeral — never in logs, memory, or RAG.
