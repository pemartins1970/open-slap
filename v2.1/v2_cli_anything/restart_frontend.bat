@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "FRONT=%ROOT%src\frontend"
set "PORT=3000"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>nul

where npm >nul 2>nul
if errorlevel 1 goto :no_npm

pushd "%FRONT%"
npm --version >nul 2>nul
if errorlevel 1 goto :no_npm

if exist "node_modules\" goto :run
if exist "package-lock.json" goto :ci
npm install
if errorlevel 1 goto :fail
goto :run

:ci
npm ci
if errorlevel 1 goto :fail

:run
npm run dev
set "EC=%ERRORLEVEL%"
popd
exit /b %EC%

:no_npm
echo npm nao encontrado. Instale Node.js (incluindo npm) e tente novamente.
exit /b 1

:fail
popd
exit /b 1
