@echo off
setlocal
set "OPENSLAP_USE_AGNO=1"
if "%OPENSLAP_AGNO_DB_FILE%"=="" set "OPENSLAP_AGNO_DB_FILE=%~dp0src\data\data\agno_sessions.db"
set PORT=5150
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>nul
pushd "%~dp0src"
python -m uvicorn backend.main_auth:app --host 127.0.0.1 --port %PORT% --reload
popd
