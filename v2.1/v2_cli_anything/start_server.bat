@echo off
setlocal
start "backend-5150" "%~dp0restart_backend.bat"
start "frontend-3000" "%~dp0restart_frontend.bat"
