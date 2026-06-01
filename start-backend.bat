@echo off
cd /d "%~dp0"
set PYTHONPATH=

if not exist ".venv\Scripts\python.exe" (
    echo [ERRO] .venv nao encontrado. Execute: python -m venv .venv
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat

echo Iniciando Open Slap Backend (porta 5150)...
.venv\Scripts\python.exe -m uvicorn backend.main_auth:app --reload --host 127.0.0.1 --port 5150

if errorlevel 1 (
    echo [ERRO] Servidor encerrou com erro.
    pause
)
