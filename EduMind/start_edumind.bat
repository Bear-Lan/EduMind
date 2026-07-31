@echo off
title EduMind System Launcher
color 0A
echo ======================================================================
echo.
echo           EduMind V1 -- AI Personalized Learning Coach
echo                     One-Click System Launcher
echo.
echo ======================================================================
echo.

:: 1. Check & Auto-create Python Virtual Environment
if not exist "%~dp0venv\Scripts\python.exe" (
    echo [SETUP] Virtual environment not found at venv\
    echo [SETUP] Auto-creating virtual environment and installing dependencies...
    python -m venv "%~dp0venv"
    if errorlevel 1 (
        echo [ERROR] Python not found in system PATH. Please install Python 3.10+
        pause
        exit /b 1
    )
    echo [SETUP] Installing Python requirements from requirements.txt...
    "%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
)

:: 2. Check & Auto-install Frontend node_modules
if not exist "%~dp0frontend\node_modules" (
    echo [SETUP] Frontend node_modules not found. Installing npm packages...
    cd /d "%~dp0frontend"
    call npm install
    cd /d "%~dp0"
)

:: 3. Launch Backend Server in new window
echo [1/2] Launching EduMind FastAPI Backend Server (Port 8000)...
start "EduMind Backend (Port 8000)" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"

:: 4. Launch Frontend Dev Server in new window
echo [2/2] Launching EduMind Vite Frontend Server (Port 5173)...
start "EduMind Frontend (Port 5173)" cmd /k "cd /d %~dp0frontend && npm run dev"

:: 5. Auto-open browser
timeout /t 3 >nul
start http://localhost:5173

echo.
echo ======================================================================
echo System startup initiated!
echo.
echo  - Backend API:    http://127.0.0.1:8000
echo  - API Docs:       http://127.0.0.1:8000/docs
echo  - Frontend App:   http://localhost:5173
echo.
echo Demo Account:
echo  - Username: demo_student
echo  - Password: DemoPassword123!
echo ======================================================================
echo.
pause
