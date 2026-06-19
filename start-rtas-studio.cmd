@echo off
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

echo [1/2] Web app — http://localhost:3000
start "RTAS Web" cmd /k "cd /d "%~dp0apps\web" && npm run dev:fast"

echo.
echo Web server starting in a new window.
echo Keep that window open while testing Google login and Studio.
echo.
echo Optional: start backend API separately if generation fails.
echo   cd apps\backend && uvicorn app.main:app --reload --port 8000
echo.
pause
