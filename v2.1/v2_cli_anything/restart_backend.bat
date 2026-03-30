@echo off
setlocal
set PORT=5150
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>nul
pushd "%~dp0src"
python -m uvicorn backend.main_auth:app --host 127.0.0.1 --port %PORT% --reload
popd
