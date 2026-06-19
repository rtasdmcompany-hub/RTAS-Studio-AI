@echo off
cd /d "%~dp0"
echo Starting RTAS Studio AI (bypasses PowerShell npm.ps1 restriction)...
call npm.cmd run dev
