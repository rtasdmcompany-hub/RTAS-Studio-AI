@echo off
title RTAS Studio AI - Web (port 3000)
cd /d "%~dp0"
echo.
echo RTAS Studio AI web server starting on http://localhost:3000
echo Keep this window open while using Google sign-in.
echo.
npm run dev:fast
