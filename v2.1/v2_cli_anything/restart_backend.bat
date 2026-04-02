@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"
set "SRC=%ROOT%src"
set "VENV=%SRC%\.venv"
set "PORT=5150"
echo [backend] src: %SRC%

for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do taskkill /PID %%p /F >nul 2>nul

if exist "%VENV%\Scripts\python.exe" goto :venv_ok

where py >nul 2>nul
if not errorlevel 1 (
  py -3 -m venv "%VENV%"
  goto :venv_created
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3 ou habilite o launcher py e tente novamente.
  exit /b 1
)
python -m venv "%VENV%"

:venv_created
if not exist "%VENV%\Scripts\python.exe" (
  echo Falha ao criar o ambiente virtual em: %VENV%
  exit /b 1
)

:venv_ok
set "PY=%VENV%\Scripts\python.exe"

"%PY%" -m pip --version >nul 2>nul
if errorlevel 1 "%PY%" -m ensurepip --upgrade >nul 2>nul

call :deps_ok
if errorlevel 1 goto :deps_install
goto :run

:deps_install
  echo [backend] installing python deps...
  "%PY%" -m pip install --upgrade pip
  "%PY%" -m pip install -r "%SRC%\backend\requirements.txt"
  if errorlevel 1 exit /b 1
call :deps_ok
if errorlevel 1 exit /b 1

:run
if /i "%~1"=="--deps-only" exit /b 0
echo [backend] starting uvicorn on port %PORT%...
set "RELOAD_FLAG="
if /i "%OPENSLAP_RELOAD%"=="1" set "RELOAD_FLAG=--reload"
if /i "%~1"=="--reload" set "RELOAD_FLAG=--reload"
pushd "%SRC%"
"%PY%" -m uvicorn backend.main_auth:app --host 127.0.0.1 --port %PORT% %RELOAD_FLAG%
popd
exit /b 0

:deps_ok
if not exist "%VENV%\Scripts\uvicorn.exe" exit /b 1
"%PY%" -c "import fastapi, uvicorn, aiohttp" >nul 2>nul
if errorlevel 1 exit /b 1
exit /b 0
