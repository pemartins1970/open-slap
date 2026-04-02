# Open Slap! — Motor agêntico desktop-local (v2.1)

> Backend: FastAPI (Python) · Frontend: React + Vite · Licença: ver [docs/LICENCE.md](docs/LICENCE.md)

Open Slap! é um assistente **local** (servidor rodando na sua máquina) com chat em tempo real, suporte a múltiplos providers de LLM e automação controlada (execução local com permissões e trilhas de auditoria).

---

## O que existe em v2.1

| Área | O que existe |
|------|-------------|
| **Chat em tempo real** | WebSocket com streaming incremental e estado de conexão |
| **MoE (experts)** | Seleção de especialista por keywords + heurísticas; opção de override |
| **Plan→Build** | Planos estruturados (bloco `plan`) + execução/orquestração incremental |
| **Memória** | SQLite + RAG/FTS + heurísticas (salience, decay, consolidação) |
| **Conectores** | GitHub, Google Drive/Calendar/Gmail, Telegram (opcionais) |
| **Segurança** | JWT, settings de permissões (OS commands, web retrieval, file write, connectors, system profile) |
| **Interface** | Onboarding, boot screen, temas e i18n (PT/EN/ES/AR/ZH) |

---

## Estrutura do repositório

```
src/
  backend/   (Python/FastAPI)
  frontend/  (React/Vite)
docs/
  README.md
  INSTALLATION.md
  DEV_JOURNAL.md
  CHANGELOG.md
  LICENCE.md
```

---

## Início rápido (Windows)

### 1) Backend (FastAPI)

```powershell
cd src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# opcional: copiar env.example para .env e configurar um provider
Copy-Item env.example .env

python main_auth.py
```

Servidor (padrão): `http://127.0.0.1:5150` (`OPENSLAP_HOST`/`OPENSLAP_PORT`).

### 2) Frontend (React/Vite)

```powershell
cd src\frontend
npm install
npm run dev
```

Frontend (padrão Vite): `http://localhost:5173`.

Instalação completa: [docs/INSTALLATION.md](docs/INSTALLATION.md)

---

## Variáveis de ambiente

- Template do backend: [src/backend/env.example](src/backend/env.example)
- Template do router (MoE LLM-first opcional): [.env.example](.env.example)

## Portas (padrão) e como alterar

- Backend: `127.0.0.1:5150`  
  - Alterar com `OPENSLAP_HOST` e `OPENSLAP_PORT` (em `src/backend/.env`).
- Frontend (Vite dev): `localhost:3000`  
  - Alterar com `VITE_PORT` (ex.: `set VITE_PORT=5173` antes de `npm run dev`), ou editando `src/frontend/vite_auth.config.js`.

## Modo de desenvolvimento (reload)

- Por padrão o backend roda sem auto-reload (mais estável).
- Para ativar auto-reload: `OPENSLAP_RELOAD=1` (apenas desenvolvimento).

---

## Testes e verificação

Backend:

```powershell
cd src\backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Frontend:

```powershell
cd src\frontend
npm run build
```

---

## Documentação (pública)

- Journal (decisões, incidentes, pendências): [docs/DEV_JOURNAL.md](docs/DEV_JOURNAL.md)
- Changelog (mudanças por versão): [docs/CHANGELOG.md](docs/CHANGELOG.md)
- Guidelines Node (evitar `node_modules` duplicado): [docs/NODE_PROJECT_GUIDELINES.md](docs/NODE_PROJECT_GUIDELINES.md)
- Publicação via servidor web (IIS/Nginx/Apache): [docs/REVERSE_PROXY.md](docs/REVERSE_PROXY.md)

---

## Notas de segurança

- Não versionar `.env`, `node_modules/`, `dist/`, caches (`__pycache__/`) nem bancos locais (`*.db`, `*.sqlite`).
- Credenciais devem ser tratadas como efêmeras e não devem ir para logs, memória ou RAG.

---
---

# Open Slap! — Desktop-local agentic engine (v2.1)

> Backend: FastAPI (Python) · Frontend: React + Vite · License: see [docs/LICENCE.md](docs/LICENCE.md)

Open Slap! is a **desktop-local** assistant (a server running on your machine) with real-time chat, multi-LLM providers and permissioned local automation.

- Public journal: [docs/DEV_JOURNAL.md](docs/DEV_JOURNAL.md)
- Public changelog: [docs/CHANGELOG.md](docs/CHANGELOG.md)
- Full installation: [docs/INSTALLATION.md](docs/INSTALLATION.md)
- Packaging checklist: [docs/PACKAGING.md](docs/PACKAGING.md)
- Memory architecture: [docs/MEMORY_ARCHITECTURE.md](docs/MEMORY_ARCHITECTURE.md)
