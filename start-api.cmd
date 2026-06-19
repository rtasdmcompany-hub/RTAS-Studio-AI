@echo off
REM Start FastAPI backend (port 8000) for RTAS Studio AI
cd /d "%~dp0apps\backend"
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python virtual environment...
  python -m venv .venv
  call .venv\Scripts\pip.exe install -r requirements.txt
)
echo Starting API at http://localhost:8000
call .venv\Scripts\python.exe -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
