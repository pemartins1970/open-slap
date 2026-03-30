# Instalação — Open Slap!

## Requisitos

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20+ |
| RAM | 4 GB | 8 GB |
| Disco | 500 MB | 2 GB (modelos locais requerem mais) |
| OS | Windows 10 / macOS 12 / Ubuntu 22.04 | qualquer |

Um i5 de 2010 roda. Testado nele.

---

## Instalação completa

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USER/open-slap.git
cd open-slap
```

### 2. Configure o ambiente

```bash
cp src/.env.example src/.env
```

Edite `src/.env`. O mínimo necessário é **uma chave de LLM**:

```env
# Opção A — Gemini (gratuito)
GEMINI_API_KEYS=sua_chave_aqui

# Opção B — Groq (gratuito)
GROQ_API_KEYS=sua_chave_aqui

# Opção C — Ollama (local, sem internet)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

Para autenticação persistente entre reinicializações:

```env
JWT_SECRET=uma_string_longa_e_aleatoria_de_pelo_menos_32_chars
```

### 3. Backend Python

```bash
cd src
pip install -r backend/requirements.txt
```

Inicie o servidor:

```bash
uvicorn backend.main_auth:app --reload --host 0.0.0.0 --port 8000
```

O backend ficará disponível em `http://localhost:8000`.

### 4. Frontend React

Em outro terminal:

```bash
cd src/frontend
npm install
npm run dev
```

Acesse `http://localhost:5173`.

Para build de produção:

```bash
npm run build
# Os arquivos estarão em src/frontend/dist/
```

---

## Variáveis de ambiente completas

Todas as variáveis estão documentadas em [`src/.env.example`](../src/.env.example).  
As principais flags de feature:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `OPENSLAP_CAC` | `1` | Cache de respostas idênticas |
| `OPENSLAP_RAG_SQLITE` | `1` | Recuperação de memória por similaridade |
| `OPENSLAP_MEMORY_WRITE` | `1` | Escrita automática de fatos na memória |
| `OPENSLAP_WEB_RETRIEVAL` | `0` | Busca na web por heurística de keywords |
| `OPENSLAP_OS_COMMANDS` | `1` | Execução de comandos do sistema pelo agente |
| `SLAP_MEMORY_REDACTION_ENABLED` | `1` | Redação de PII antes da persistência |

---

## Ollama (LLM local)

Se quiser rodar sem internet:

```bash
# Instale Ollama: https://ollama.com/download
ollama serve          # inicia o servidor
ollama pull llama3.2  # baixa o modelo (~2 GB)
```

Configure no `.env`:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
PROVIDER_ORDER=ollama
```

---

## Conectores opcionais

Os conectores são opcionais. Configure em **Personalizar → Conectores** na interface:

- **GitHub** — Personal Access Token (classic ou fine-grained) com escopo `repo`
- **Google Drive / Calendar / Gmail** — Access Token OAuth Bearer do Google Cloud Console  
  *(ative as APIs: Drive API v3, Calendar API v3, Gmail API)*

---

## Executando os testes

```bash
cd src
python -m pytest backend/tests/ -v
```

Saída esperada: **50 testes passando**.

---

## Solução de problemas

**`ModuleNotFoundError: No module named 'bcrypt'`**  
→ `pip install bcrypt`

**Frontend não conecta ao backend**  
→ Verifique se o backend está rodando na porta 8000. O Vite faz proxy automático via `vite.config.js`.

**Modelos Ollama muito lentos**  
→ Use um modelo menor: `ollama pull phi3:mini` e ajuste `OLLAMA_MODEL=phi3:mini`

**JWT inválido após reinicialização**  
→ Defina `JWT_SECRET` fixo no `.env`. Sem ele, um novo secret é gerado a cada restart.

---
---

# Installation — Open Slap!

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20+ |
| RAM | 4 GB | 8 GB |
| Disk | 500 MB | 2 GB (local models need more) |
| OS | Windows 10 / macOS 12 / Ubuntu 22.04 | any |

A 2010 i5 runs it. Tested on one.

---

## Full installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USER/open-slap.git
cd open-slap
```

### 2. Configure the environment

```bash
cp src/.env.example src/.env
```

Edit `src/.env`. The minimum required is **one LLM key**:

```env
# Option A — Gemini (free)
GEMINI_API_KEYS=your_key_here

# Option B — Groq (free)
GROQ_API_KEYS=your_key_here

# Option C — Ollama (local, no internet)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

For auth persistence across restarts:

```env
JWT_SECRET=a_long_random_string_at_least_32_chars
```

### 3. Python backend

```bash
cd src
pip install -r backend/requirements.txt
```

Start the server:

```bash
uvicorn backend.main_auth:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at `http://localhost:8000`.

### 4. React frontend

In another terminal:

```bash
cd src/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

For a production build:

```bash
npm run build
# Output will be in src/frontend/dist/
```

---

## Full environment variables

All variables are documented in [`src/.env.example`](../src/.env.example).  
Key feature flags:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENSLAP_CAC` | `1` | Cache identical question responses |
| `OPENSLAP_RAG_SQLITE` | `1` | Memory retrieval by similarity |
| `OPENSLAP_MEMORY_WRITE` | `1` | Automatic fact writing to memory |
| `OPENSLAP_WEB_RETRIEVAL` | `0` | Web search via keyword heuristic |
| `OPENSLAP_OS_COMMANDS` | `1` | Agent system command execution |
| `SLAP_MEMORY_REDACTION_ENABLED` | `1` | PII redaction before persistence |

---

## Ollama (local LLM)

To run without internet:

```bash
# Install Ollama: https://ollama.com/download
ollama serve          # start the server
ollama pull llama3.2  # download the model (~2 GB)
```

Configure in `.env`:
```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
PROVIDER_ORDER=ollama
```

---

## Optional connectors

Connectors are optional. Configure via **Customize → Connectors** in the UI:

- **GitHub** — Personal Access Token (classic or fine-grained) with `repo` scope
- **Google Drive / Calendar / Gmail** — Google Cloud Console OAuth Bearer Token  
  *(enable APIs: Drive API v3, Calendar API v3, Gmail API)*

---

## Running the tests

```bash
cd src
python -m pytest backend/tests/ -v
```

Expected output: **50 tests passing**.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'bcrypt'`**  
→ `pip install bcrypt`

**Frontend not connecting to backend**  
→ Verify the backend is running on port 8000. Vite proxies automatically via `vite.config.js`.

**Ollama models too slow**  
→ Use a smaller model: `ollama pull phi3:mini` and set `OLLAMA_MODEL=phi3:mini`

**Invalid JWT after restart**  
→ Set a fixed `JWT_SECRET` in `.env`. Without it, a new secret is generated on every restart.
