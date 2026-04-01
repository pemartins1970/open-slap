# Instalação — Open Slap! (v2.1)

Documento focado em instalação local (Windows). Para visão geral do projeto, ver `README.md`.

## Requisitos

| Componente | Mínimo | Recomendado |
|-----------|--------|-------------|
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20+ |
| RAM | 4 GB | 8 GB |
| OS | Windows 10+ | Windows 11 |

---

## 1) Backend (FastAPI)

```powershell
cd src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Configuração de providers (LLM)

Copie o template e edite com pelo menos um provider:

```powershell
Copy-Item env.example .env
```

Arquivo: `src/backend/.env`  
Template: `src/backend/env.example`

### Iniciar o backend

```powershell
python main_auth.py
```

Backend (padrão): `http://127.0.0.1:5150`  
Config: `OPENSLAP_HOST` / `OPENSLAP_PORT`

---

## 2) Frontend (React/Vite)

Em outro terminal:

```powershell
cd src\frontend
npm install
npm run dev
```

Frontend (padrão): `http://localhost:5173`

---

## Conectores (opcionais)

Os conectores são opcionais e configurados via UI em **Personalizar → Conectores**.

- GitHub — Personal Access Token
- Google Drive / Calendar / Gmail — OAuth Bearer access token
- Telegram — token do bot + vínculo por link-code

---

## Testes

```powershell
cd src\backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

---
---

# Installation — Open Slap! (v2.1)

This doc focuses on local installation (Windows). For a project overview, see `README.md`.

## Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.10 | 3.12 |
| Node.js | 18 | 20+ |
| RAM | 4 GB | 8 GB |
| OS | Windows 10+ | Windows 11 |

---

## 1) Backend (FastAPI)

```powershell
cd src\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item env.example .env
python main_auth.py
```

Backend (default): `http://127.0.0.1:5150`

---

## 2) Frontend (React/Vite)

```powershell
cd src\frontend
npm install
npm run dev
```

Frontend (default): `http://localhost:5173`

