@echo off
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [INFO] Instalando dependencias do frontend...
    call npm install
)

echo Iniciando Frontend (Vite)...
npm run dev

if errorlevel 1 (
    pause
)
