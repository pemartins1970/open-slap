# Open Slap! — Motor agêntico desktop-local (v2.1)

> Backend: FastAPI (Python) · Frontend: React + Vite · Licença: ver [LICENCE.md](LICENCE.md)

Open Slap! é um assistente **local** (servidor rodando na sua máquina) com chat em tempo real, suporte a múltiplos providers de LLM e automação controlada (execução local com permissões e trilhas de auditoria).

## O que existe em v2.1

| Área | O que existe |
|------|-------------|
| **Chat em tempo real** | WebSocket com streaming incremental e estado de conexão |
| **MoE (experts)** | Seleção de especialista por keywords + heurísticas; override manual disponível |
| **Plan→Build** | Planos estruturados (bloco `plan`) + execução/orquestração incremental |
| **Memória** | SQLite + RAG/FTS + heurísticas (salience, decay, consolidação) |
| **Conectores** | GitHub, Google Drive/Calendar/Gmail, Telegram (opcionais) |
| **Segurança** | JWT + settings de permissões (OS commands, web retrieval, file write, connectors, system profile) |
| **Interface** | Onboarding, boot screen, temas e i18n (PT/EN/ES/AR/ZH) |

## Início rápido (Windows)

```powershell
cd src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item env.example .env
python main_auth.py
```

Em outro terminal:

```powershell
cd src\frontend
npm install
npm run dev
```

- Backend (padrão): `http://127.0.0.1:5150`
- Frontend (padrão): `http://localhost:3000`

Instalação completa: [INSTALLATION.md](INSTALLATION.md)

## Estrutura do projeto (alto nível)

```
src/
  backend/
    main_auth.py
    db.py
    deps.py
    runtime.py
    routes/
  frontend/
    package.json
    src/
docs/
  DEV_JOURNAL.md
  CHANGELOG.md
  LICENCE.md
```

## Configuração

- Providers LLM (backend): `src/backend/env.example` → copiar para `src/backend/.env`
- Router MoE (LLM-first opcional): `.env.example` na raiz (opcional)

## Portas (padrão) e como alterar

- Backend: `127.0.0.1:5150` (ajuste via `OPENSLAP_HOST` / `OPENSLAP_PORT` em `src/backend/.env`)
- Frontend dev: `localhost:3000` (ajuste via `VITE_PORT` ou `src/frontend/vite_auth.config.js`)

## Contribuições

- Issues e PRs são bem-vindos, especialmente para hardening (aprovação por etapa, UX TODO, confiabilidade do software_operator).
- Para decisões e contexto, veja [DEV_JOURNAL.md](DEV_JOURNAL.md).

## Publicação via servidor web (opcional)

- Reverse proxy (IIS/Nginx/Apache): [REVERSE_PROXY.md](REVERSE_PROXY.md)

## Kickoff de projeto (templates)

- Templates Markdown para testes manuais do fluxo “Projeto > Kickoff”: [kickoff_templates/](kickoff_templates/)

## Referências (backlog)

- Projetos externos e ideias para etapas futuras: [EXTERNAL_REFERENCES.md](EXTERNAL_REFERENCES.md)
- Wishlist de recursos e status: [FEATURE_WISHLIST.md](FEATURE_WISHLIST.md)

---
---

# Open Slap! — Desktop-local agentic engine (v2.1)

> Backend: FastAPI (Python) · Frontend: React + Vite · License: see [LICENCE.md](LICENCE.md)

Open Slap! is a **desktop-local** assistant (a server running on your machine) with real-time chat, multi-LLM providers and permissioned local automation.

## Quick start (Windows)

```powershell
cd src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item env.example .env
python main_auth.py
```

Another terminal:

```powershell
cd src\frontend
npm install
npm run dev
```

Full installation: [INSTALLATION.md](INSTALLATION.md)
