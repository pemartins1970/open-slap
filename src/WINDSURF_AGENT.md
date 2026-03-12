# WINDSURF AGENT — BRIEFING OPERACIONAL
## Projeto: Agêntico v1.0 — Sistema Agêntico Local Open Source

> **Leia este documento inteiro antes de tocar em qualquer arquivo.**
> Este é o único ponto de verdade do projeto.
> **SESSÃO 3 — 2026-03-04 — Estado real mapeado. Docker fora do escopo.**

---

## 1. AMBIENTE REAL DE EXECUÇÃO

- **OS:** Windows (Desktop do usuário)
- **Raiz do projeto:** `C:\Users\pemartins\Desktop\agentic\`
- **Modo de execução:** Dev manual (sem Docker, sem docker-compose)
- **Docker:** Fora do escopo para Etapa 1. Ignorar qualquer menção anterior.
- **Python:** Rodando o backend manualmente via terminal
- **Node/Vite:** Rodando o frontend manualmente via terminal

### Como subir o sistema (modo dev, Windows)

```bash
# Terminal 1 — Backend
cd C:\Users\pemartins\Desktop\agentic\backend
python main.py
# Roda em http://localhost:8000

# Terminal 2 — Frontend
cd C:\Users\pemartins\Desktop\agentic\frontend
npm run dev
# Roda em http://localhost:3000
```

---

## 2. ESTRUTURA REAL DO PROJETO — SESSÃO 3

### Raiz (`C:\Users\pemartins\Desktop\agentic\`)

```
agentic/
├── main.py                  ⚠️  ARQUIVO ANTIGO — SEM AUTH — NÃO USAR
│
├── backend/
│   ├── main_auth.py         ✅  VERSÃO CORRETA — renomear para main.py
│   ├── auth.py              ✅  JWT + registro + login (passlib + python-jose)
│   ├── db.py                ✅  SQLite — users, conversations, messages
│   ├── data/
│   │   └── auth.db          ✅  Banco SQLite (36KB, funcionando)
│   ├── moe_router_simple.py ✅  EM USO — MoE puro Python, sem sklearn
│   ├── llm_manager_simple.py✅  EM USO — LLM manager standalone
│   ├── moe_router.py        ⚠️  ORIGINAL — não está em uso, pode deletar
│   ├── llm_manager.py       ⚠️  ORIGINAL — não está em uso, pode deletar
│   └── requirements.txt     ✅
│
└── frontend/
    ├── App_auth.jsx         ✅  VERSÃO CORRETA — renomear para src/App.jsx
    ├── vite_auth.config.js  ✅  VERSÃO CORRETA — renomear para vite.config.js
    ├── index_auth.html      ✅  VERSÃO CORRETA — renomear para index.html
    ├── src/
    │   ├── App.jsx          ⚠️  VERSÃO ANTIGA — sobrescrever com App_auth.jsx
    │   ├── main.jsx         ✅  Entry point OK
    │   ├── pages/
    │   │   └── Login.jsx    ✅  Tela de login/registro
    │   └── hooks/
    │       └── useAuth.js   ✅  Hook de autenticação
    ├── vite.config.js       ⚠️  VERSÃO ANTIGA — sobrescrever com vite_auth.config.js
    ├── index.html           ⚠️  VERSÃO ANTIGA — sobrescrever com index_auth.html
    └── package.json         ✅
```

---

## 3. PRÓXIMA TAREFA — CONSOLIDAÇÃO DE ARQUIVOS

**Fazer agora, antes de qualquer outra coisa:**

### PASSO 1 — Consolidar backend

```bash
# Opção A: Renomear (recomendado se main.py na raiz não é usado pelo backend)
# O backend/main_auth.py vira o principal:
cd C:\Users\pemartins\Desktop\agentic\backend
copy main_auth.py main.py   # sobrescreve se já existir

# Verificar que main.py importa os módulos corretos:
# from moe_router_simple import MoERouter
# from llm_manager_simple import LLMManager
# (NÃO importar moe_router ou llm_manager sem o sufixo _simple)
```

O `main.py` na raiz (`C:\Users\pemartins\Desktop\agentic\main.py`) é o arquivo legado.
**Não deletar ainda** — renomear para `main_LEGADO.py` para referência.

### PASSO 2 — Consolidar frontend

```bash
cd C:\Users\pemartins\Desktop\agentic\frontend

# Sobrescrever arquivos antigos com versões _auth:
copy App_auth.jsx src\App.jsx
copy vite_auth.config.js vite.config.js
copy index_auth.html index.html

# Após confirmar que funcionam, deletar os _auth:
# del App_auth.jsx
# del vite_auth.config.js
# del index_auth.html
```

### PASSO 3 — Confirmar imports no App.jsx

Verificar que o `src/App.jsx` (após substituição) importa corretamente:

```javascript
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
// (ou AuthPage — verificar o nome real do componente em pages/)
```

### PASSO 4 — Confirmar proxy no vite.config.js

O `vite.config.js` deve ter o proxy apontando para o backend:

```javascript
server: {
  proxy: {
    '/api': 'http://localhost:8000',
    '/auth': 'http://localhost:8000',
    '/ws': {
      target: 'ws://localhost:8000',
      ws: true
    },
    '/health': 'http://localhost:8000'
  }
}
```

Se não tiver `/auth` no proxy, as chamadas de login/registro vão falhar com 404.

### PASSO 5 — Subir e testar

```bash
# Terminal 1
cd C:\Users\pemartins\Desktop\agentic\backend
python main.py

# Terminal 2
cd C:\Users\pemartins\Desktop\agentic\frontend
npm run dev
```

**Checklist de teste:**
```
[ ] http://localhost:8000/health retorna 200
[ ] http://localhost:3000 abre tela de login (não o chat antigo)
[ ] Registrar novo usuário → entra no chat
[ ] Enviar mensagem → resposta em streaming aparece
[ ] Fechar aba → reabrir → ainda logado (token persiste)
[ ] Botão logout → volta para tela de login
```

---

## 4. ESTADO CONFIRMADO — O QUE FUNCIONA

### Backend (confirmado na Sessão 2)

```
URL base: http://localhost:8000

POST /auth/register    → {email, password} → {token, user}
POST /auth/login       → {email, password} → {token, user}
GET  /auth/me          → Bearer token → {id, email}
GET  /api/conversations
POST /api/conversations
GET  /api/conversations/{id}
DELETE /api/conversations/{id}
WS   /ws/{session_id}?token={jwt}
GET  /health
GET  /api/experts
```

### Banco de dados

```
Arquivo: C:\Users\pemartins\Desktop\agentic\backend\data\auth.db
Tamanho: 36.864 bytes (funcionando)
Tabelas: users, conversations, messages
```

### Providers de LLM

```
Ollama:  configurado, offline (normal)
Gemini:  precisa GEMINI_API_KEYS no .env
Groq:    precisa GROQ_API_KEYS no .env
```

---

## 5. PONTOS CRÍTICOS — NÃO QUEBRAR

### Imports dos módulos _simple

O `backend/main.py` (versão auth) importa `moe_router_simple` e `llm_manager_simple`.
**Nunca trocar para `moe_router` ou `llm_manager` sem sufixo** — esses têm dependências
(sklearn, pandas) que quebraram o sistema.

### Token no WebSocket

```javascript
// CORRETO:
new WebSocket(`ws://localhost:8000/ws/${SESSION_ID}?token=${token}`)

// ERRADO (não autentica):
new WebSocket(`ws://localhost:8000/ws/${SESSION_ID}`)
```

### Proxy do Vite

Todas as rotas `/api/*`, `/auth/*`, `/ws/*`, `/health` precisam estar no proxy do
`vite.config.js`. Sem isso, o frontend chama `localhost:3000/auth/login` em vez de
`localhost:8000/auth/login`.

### Streaming

Qualquer mudança na lógica de mensagens do `App.jsx` exige teste manual:
1. Enviar mensagem longa
2. Verificar texto chegando em chunks (não tudo de uma vez)
3. Verificar expert tag aparece após "done"
4. Enviar segunda mensagem sem reload da página

---

## 6. BACKLOG — APÓS CONSOLIDAÇÃO FUNCIONAR

```
PRIORIDADE ALTA (próxima sessão):
  [ ] Lista de conversas na sidebar (useConversations hook)
  [ ] Clicar em conversa → carrega mensagens anteriores
  [ ] Título automático da conversa (primeiras palavras da 1ª mensagem)
  [ ] Badge do provider na resposta (Gemini / Groq / Ollama)

PRIORIDADE MÉDIA:
  [ ] Configurar pelo menos Gemini ou Groq no .env e testar LLM real
  [ ] Página de status dos providers
  [ ] Copiar código com um clique nos blocos de código

PRIORIDADE BAIXA (Etapa 2):
  [ ] Docker / docker-compose para distribuição
  [ ] RAG com ChromaDB local
  [ ] OAuth (Google, GitHub)
  [ ] Multi-usuário
```

---

## 7. DESIGN SYSTEM

### CSS Variables (definidas no index.html)

```css
--bg: #080c0f          /* fundo principal */
--bg2: #0e1318         /* sidebar, header */
--bg3: #141b22         /* código, inputs */
--border: #1e2d3d      /* bordas */
--amber: #f5a623       /* acento principal */
--green: #4ade80       /* sucesso, online */
--red: #f87171         /* erro */
--text: #c8d8e8        /* texto padrão */
--text-dim: #5a7a96    /* texto secundário */
--text-bright: #e8f4ff /* destaque */
--mono: 'IBM Plex Mono', monospace
--sans: 'IBM Plex Sans', sans-serif
```

### Padrões visuais

**Input:** background `--bg3`, border `--border`, focus border `rgba(245,166,35,0.4)`

**Botão primário:** border `--amber`, color `--amber`, hover background `rgba(245,166,35,0.08)`

**Erro:** background `rgba(248,113,113,0.08)`, border `rgba(248,113,113,0.3)`, color `--red`

**Label de seção:** mono, 10px, letterSpacing 2, uppercase, color `--text-dim`

---

## 8. CONVENÇÕES

- **Python:** async/await em I/O · comentários português · snake_case · nunca silenciar exceções
- **JS/React:** hooks para lógica reutilizável · estilos inline (objeto JS) · sem biblioteca de ícones (SVG inline Heroicons)
- **Decisão:** Simples > Complexo · Menos deps > Mais deps · Funciona agora > Perfeito depois
- **Git:** `feat:` / `fix:` / `refactor:` em minúsculo

---

*Última atualização: 2026-03-04 — Sessão 3*
*Docker removido do escopo. Consolidação de arquivos é o próximo passo.*
