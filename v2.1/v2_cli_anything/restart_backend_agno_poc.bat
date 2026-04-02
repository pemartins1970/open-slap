@echo off
setlocal
set "OPENSLAP_USE_AGNO=1"
if "%OPENSLAP_AGNO_DB_FILE%"=="" set "OPENSLAP_AGNO_DB_FILE=%~dp0src\data\data\agno_sessions.db"
call "%~dp0restart_backend.bat" %*
