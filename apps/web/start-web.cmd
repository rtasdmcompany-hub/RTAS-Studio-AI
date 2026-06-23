@echo off
setlocal
title RTAS Studio AI — Web (port 3000)
cd /d "%~dp0"

echo.
echo ========================================
echo   RTAS Web — Next.js dev server
echo   Directory: %CD%
echo   URL:       http://127.0.0.1:3000
echo ========================================
echo.

where node >nul 2>&1
if errorlevel 1 (
  echo ERROR: Node.js not found on PATH.
  echo Install Node 20 LTS and reopen this window.
  pause
  exit /b 1
)

if not exist "package.json" (
  echo ERROR: package.json not found in %CD%
  pause
  exit /b 1
)

echo [start] npm run dev:fast
echo       (skips predev hooks for faster startup; run npm run setup:env first if .env.local is missing)
echo.
call npm.cmd run dev:fast
echo.
echo Web dev server exited with code %ERRORLEVEL%
pause
