@echo off
setlocal
set PORT=3000
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>nul
pushd "%~dp0src\frontend"
npm run dev
popd
