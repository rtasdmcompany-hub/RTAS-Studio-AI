@echo off
setlocal EnableDelayedExpansion
title RTAS Studio AI — Dev Stack
cd /d "%~dp0"

echo.
echo ========================================
echo   RTAS Studio AI — Starting dev stack
echo ========================================
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo ERROR: Node.js not found. Install from https://nodejs.org
  pause
  exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python not found. Install Python 3.11+ for the FastAPI backend.
  pause
  exit /b 1
)

echo [1/2] FastAPI backend — http://localhost:8000
start "RTAS API :8000" cmd /k call ""%~dp0start-api.cmd""

echo [2/2] Next.js web app — http://localhost:3000
timeout /t 2 /nobreak >nul
start "RTAS Web :3000" cmd /k call ""%~dp0apps\web\start-web.cmd""

echo.
echo Servers are starting in separate windows. Keep both open while developing.
echo.
echo   Web:    http://localhost:3000/auth/login
echo   Studio: http://localhost:3000/studio
echo   API:    http://localhost:8000/api/health
echo.
pause
