# Installation — Open Slap! (v2.1.1)

For a project overview, see [README.md](../README.md).

---

## Option A — Desktop App (Recommended)

The easiest way to run Open Slap! is to download the pre-built executable from the [Releases page](https://github.com/pemartins1970/open-slap/releases).

| Platform | File | Notes |
|----------|------|-------|
| Windows (Installer) | `Open Slap! Setup *.exe` | Installs with shortcuts |
| Windows (Portable)  | `Open Slap!-*-portable.exe` | No installation needed |
| macOS               | `Open Slap!-*.dmg` | Open and drag to Applications |
| Linux               | `Open Slap!-*.AppImage` | Make executable and run |

### Requirements for Desktop App

- **Python 3.11+** installed and in PATH
  - Windows: download from https://www.python.org/downloads/ — check "Add Python to PATH"
  - macOS: `brew install python@3.11`
  - Linux: `sudo apt install python3.11`

### First Run

1. Launch the app
2. A splash screen will appear while it:
   - Detects your Python installation
   - Installs Python dependencies automatically (`pip install`)
   - Starts the backend server
3. The main interface loads when ready

---

## Option B — Manual / Development Setup

### Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python    | 3.11    | 3.12        |
| Node.js   | 18      | 20+         |
| RAM       | 4 GB    | 8 GB        |

### 1) Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

# Copy and configure environment
Copy-Item ..\env.example .env     # Linux/macOS: cp ../env.example .env

python main_auth.py
```

Backend runs at `http://127.0.0.1:5150` (configurable via `OPENSLAP_HOST` / `OPENSLAP_PORT`).

### 2) Frontend (React/Vite)

In a separate terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`.

### 3) LLM Provider Configuration

Edit `backend/.env` (copied from `env.example`) and configure at least one provider:

```env
# Google Gemini (free tier)
GEMINI_API_KEYS=your_key_here

# Groq (free, fast)
GROQ_API_KEYS=your_key_here

# Ollama (fully local, no key needed)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# Provider fallback order
PROVIDER_ORDER=gemini,groq,ollama,openai
```

---

## Optional Connectors

Configured via UI at **Settings → Connectors**:

| Connector | Requires |
|-----------|----------|
| GitHub    | Personal Access Token |
| Telegram  | Bot token + link-code |
| Google    | OAuth Bearer access token |

---

## Running Tests

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

---

## Build Desktop App Locally

If you want to build the executables yourself:

```powershell
# 1. Build frontend
cd frontend
npm install
npm run build

# 2. Build Electron app
cd ../electron
npm install
npm run build:win      # Windows
npm run build:mac      # macOS
npm run build:linux    # Linux
```

Output files will be in `electron/dist/`.
