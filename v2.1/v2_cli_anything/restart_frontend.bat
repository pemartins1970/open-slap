@echo off
setlocal EnableExtensions
set "ROOT=%~dp0"
set "FRONT=%ROOT%src\frontend"
set "PORT=3000"
echo [frontend] workdir: %FRONT%
echo [frontend] ensuring port %PORT% is free...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /R /C:":%PORT% " ^| findstr LISTENING') do (
  echo [frontend] killing PID %%p on port %PORT%...
  taskkill /PID %%p /F >nul 2>nul
)
echo [frontend] port check done.

where npm >nul 2>nul
if errorlevel 1 goto :no_npm

pushd "%FRONT%"
if errorlevel 1 goto :fail
call npm --version >nul 2>nul
if errorlevel 1 goto :no_npm

if exist "node_modules\" goto :run
if exist "package-lock.json" goto :ci
echo [frontend] installing deps (npm install)...
call npm install
if errorlevel 1 goto :fail
goto :run

:ci
echo [frontend] installing deps (npm ci)...
call npm ci
if errorlevel 1 goto :fail

:run
if /i "%~1"=="--deps-only" (
  popd
  exit /b 0
)
if not exist "node_modules\.bin\vite.cmd" (
  echo [frontend] vite nao encontrado em node_modules. Rode npm ci e tente novamente.
  popd
  exit /b 1
)
echo [frontend] starting dev server on port %PORT%...
call npm run dev
set "EC=%ERRORLEVEL%"
popd
exit /b %EC%

:no_npm
echo npm nao encontrado. Instale Node.js (incluindo npm) e tente novamente.
exit /b 1

:fail
echo [frontend] failed. Veja a saida acima.
popd
exit /b 1
