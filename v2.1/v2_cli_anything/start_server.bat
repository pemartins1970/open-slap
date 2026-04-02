@echo off
setlocal EnableExtensions

call "%~dp0restart_backend.bat" --deps-only
if errorlevel 1 exit /b 1

call "%~dp0restart_frontend.bat" --deps-only
if errorlevel 1 exit /b 1

start "backend-5150" /D "%~dp0" cmd /k call restart_backend.bat
start "frontend-3000" /D "%~dp0" cmd /k call restart_frontend.bat
