@echo off
setlocal
start "backend-5150-agno-poc" "%~dp0restart_backend_agno_poc.bat"
start "frontend-3000" "%~dp0restart_frontend_agno_poc.bat"
