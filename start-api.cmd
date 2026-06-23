@echo off
setlocal
title RTAS Studio AI — API (port 8000)
cd /d "%~dp0apps\backend"

echo.
echo ========================================
echo   RTAS API — FastAPI (uvicorn)
echo   Directory: %CD%
echo   URL:       http://127.0.0.1:8000
echo ========================================
echo.

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found on PATH.
  echo Install Python 3.11+ and reopen this window.
  pause
  exit /b 1
)

if not exist "main.py" (
  echo ERROR: main.py not found in %CD%
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [setup] Creating Python virtual environment...
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: Failed to create .venv
    pause
    exit /b 1
  )
  echo [setup] Installing requirements.txt ...
  call .venv\Scripts\pip.exe install -r requirements.txt
  if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
  )
)

echo [start] uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
echo.
echo API process exited with code %ERRORLEVEL%
pause
