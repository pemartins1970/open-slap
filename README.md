# Open Slap! — Motor Agêntico para Makers

> Versão atual: **v2.0** · Licença: Apache 2.0 · Python 3.10+

**Open Slap!** é um motor agêntico de código aberto, pensado para quem quer construir, estudar e experimentar com IA sem depender de plataformas fechadas, hardware caro ou assinaturas mensais.

Roda em hardware comum. Aceita LLMs locais e remotas. O código está exposto porque deve estar.

---

## Funcionalidades da v2.0

| Área | O que existe |
|------|-------------|
| **Agentes** | 14 skills built-in: CTO, PM, Arquiteto, Backend, Frontend, DevOps, Security, Code Review, Testes, Excel, SEO, Marketing, Chat Assistant, Skill Creator |
| **Plan→Build** | CTO emite plano estruturado → orquestrador executa cada tarefa automaticamente com a skill correta |
| **Memória** | SQLite + RAG · Fases 1-4: escrita heurística, momentum, decay, consolidação por salience |
| **Conectores** | GitHub (repos + issues) · Google Calendar (eventos) · Gmail (e-mails não lidos) · Google Drive (arquivos) |
| **Feedback** | 👍/👎 por mensagem → retroalimenta cache, RAG e rating dos experts |
| **MoE Router** | Seleção automática de expert por keywords + histórico de aprovações · Override manual disponível |
| **Projetos** | Contexto compartilhado entre tarefas de um mesmo projeto |
| **Interface** | 8 temas de cor · 5 idiomas (PT, EN, ES, AR, ZH) · Layout responsivo desktop + mobile |
| **Segurança** | Autenticação JWT · Redação de PII antes da persistência · CORS configurável |
| **Testes** | 50 testes automatizados (pytest) cobrindo DB, MoE, memória, planos, feedback |

---

## Início rápido

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USER/open-slap.git
cd open-slap/src

# 2. Configure o ambiente
cp .env.example .env
# edite .env com pelo menos uma chave de LLM

# 3. Instale as dependências
pip install -r backend/requirements.txt

# 4. Inicie o backend
cd backend
uvicorn backend.main_auth:app --reload --port 8000

# 5. Instale e inicie o frontend (em outro terminal)
cd src/frontend
npm install
npm run dev
```

Acesse `http://localhost:5173` no navegador.  
Documentação de instalação completa: [INSTALLATION.md](INSTALLATION.md)

---

## Estrutura do projeto

```
src/
├── backend/
│   ├── main_auth.py       # Servidor FastAPI + WebSocket + todos os endpoints
│   ├── db.py              # Schema SQLite + 62 métodos de acesso
│   ├── moe_router_simple.py  # Router de especialistas (keyword + histórico)
│   ├── llm_manager_simple.py # Orquestração de LLM providers com fallback
│   ├── auth.py            # Autenticação JWT + gestão de usuários
│   └── tests/             # 50 testes pytest
├── frontend/src/
│   ├── App_auth.jsx       # Interface React principal (4 500+ linhas)
│   ├── main_auth.jsx      # Entry point + CSS vars + temas
│   └── pages/Login.jsx    # Tela de login/registro/recuperação
└── .env.example           # Todas as variáveis documentadas
```

---

## Providers de LLM suportados

- **Gemini** (Google) — gratuito em [aistudio.google.com](https://aistudio.google.com)
- **Groq** — gratuito em [console.groq.com](https://console.groq.com)
- **OpenAI** — e compatíveis (OpenRouter, LM Studio)
- **Ollama** — 100% local, sem internet

---

## Contribuições

Bem-vindas, com critério. Leia [CONTRIBUTING](#) antes de abrir um PR.  
Bugs, melhorias de documentação e casos de uso reais têm prioridade.

---

## Ecossistema

Open Slap! é o core de uma família de produtos em desenvolvimento.   


---

*— Pê Martins*

---
---

# Open Slap! — Agentic Engine for Makers

> Current version: **v2.0** · License: Apache 2.0 · Python 3.10+

**Open Slap!** is an open-source agentic engine built for people who want to build, study, and experiment with AI without depending on closed platforms, expensive hardware, or monthly subscriptions.

Runs on common hardware. Accepts local and remote LLMs. The code is exposed because it should be.

---

## Features in v2.0

| Area | What's here |
|------|------------|
| **Agents** | 14 built-in skills: CTO, PM, Architect, Backend, Frontend, DevOps, Security, Code Review, Tests, Excel, SEO, Marketing, Chat Assistant, Skill Creator |
| **Plan→Build** | CTO emits a structured plan → orchestrator executes each task automatically with the right skill |
| **Memory** | SQLite + RAG · Phases 1-4: heuristic write, momentum, decay, salience-based consolidation |
| **Connectors** | GitHub (repos + issues) · Google Calendar (events) · Gmail (unread emails) · Google Drive (files) |
| **Feedback** | 👍/👎 per message → retrofeeds cache, RAG and expert ratings |
| **MoE Router** | Auto expert selection by keywords + approval history · Manual override available |
| **Projects** | Shared context across tasks within the same project |
| **Interface** | 8 colour themes · 5 languages (PT, EN, ES, AR, ZH) · Responsive desktop + mobile layout |
| **Security** | JWT authentication · PII redaction before persistence · Configurable CORS |
| **Tests** | 50 automated tests (pytest) covering DB, MoE, memory, plans, feedback |

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USER/open-slap.git
cd open-slap/src

# 2. Configure the environment
cp .env.example .env
# edit .env with at least one LLM key

# 3. Install dependencies
pip install -r backend/requirements.txt

# 4. Start the backend
cd backend
uvicorn backend.main_auth:app --reload --port 8000

# 5. Install and start the frontend (another terminal)
cd src/frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.  
Full installation docs: [INSTALLATION.md](INSTALLATION.md)

---

## Project structure

```
src/
├── backend/
│   ├── main_auth.py       # FastAPI server + WebSocket + all endpoints
│   ├── db.py              # SQLite schema + 62 access methods
│   ├── moe_router_simple.py  # Expert router (keyword + history)
│   ├── llm_manager_simple.py # LLM provider orchestration with fallback
│   ├── auth.py            # JWT auth + user management
│   └── tests/             # 50 pytest tests
├── frontend/src/
│   ├── App_auth.jsx       # Main React interface (4 500+ lines)
│   ├── main_auth.jsx      # Entry point + CSS vars + themes
│   └── pages/Login.jsx    # Login/register/recovery screen
└── .env.example           # All variables documented
```

---

## Supported LLM Providers

- **Gemini** (Google) — free at [aistudio.google.com](https://aistudio.google.com)
- **Groq** — free at [console.groq.com](https://console.groq.com)
- **OpenAI** — and compatibles (OpenRouter, LM Studio)
- **Ollama** — 100% local, no internet required

---

## Contributions

Welcome, with criteria. Read [CONTRIBUTING](#) before opening a PR.  
Bugs, documentation improvements, and real use cases take priority.

---

## Ecosystem

Open Slap! is the core of a product family.  
**Slap! PRO** and other commercial derivatives exist and fund the continuity of this open-source project.

---

*— Pê Martins*
