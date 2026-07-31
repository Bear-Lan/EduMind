@echo off
title EduMind Backend Server
echo ==================================================
echo         Starting EduMind Backend Server
echo ==================================================
echo.

:: ===== Load .env configuration =====
:: The backend reads .env via python-dotenv automatically.
:: We don't need to set env vars manually here; the .env file handles it.

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Change to backend directory and boot uvicorn
cd backend
..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload

pause
