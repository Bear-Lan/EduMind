@echo off
title EduMind Deploy Launcher
color 0B
echo ======================================================================
echo.
echo           EduMind V1 -- AI Personalized Learning Coach
echo                Deploy Edition (Single-Server Mode)
echo.
echo ======================================================================
echo.

:: 0. Create .env from template on first run
if not exist "%~dp0.env" (
    echo [SETUP] Creating local .env from template...
    copy /Y "%~dp0.env.example" "%~dp0.env" >nul
    echo [SETUP] .env created. You can edit it to add your API keys later.
)

:: 1. Check & auto-create Python venv
if not exist "%~dp0venv\Scripts\python.exe" (
    echo [SETUP] Python venv not found. Creating...
    python -m venv "%~dp0venv"
    if errorlevel 1 (
        echo [ERROR] Python not found. Please install Python 3.10-3.12.
        pause
        exit /b 1
    )
    echo [SETUP] Installing Python dependencies...
    "%~dp0venv\Scripts\python.exe" -m pip install --upgrade pip
    "%~dp0venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies.
        pause
        exit /b 1
    )
)

:: 2. Build frontend if dist/ doesn't exist
if not exist "%~dp0frontend\dist\index.html" (
    echo [SETUP] Frontend build not found. Building...
    if not exist "%~dp0frontend\node_modules" (
        echo [SETUP] Installing npm packages...
        cd /d "%~dp0frontend"
        call npm install
        if errorlevel 1 (
            echo [ERROR] npm install failed. Please install Node.js 18+.
            pause
            exit /b 1
        )
    )
    echo [SETUP] Building frontend (npm run build)...
    cd /d "%~dp0frontend"
    call npm run build
    if errorlevel 1 (
        echo [ERROR] Frontend build failed.
        pause
        exit /b 1
    )
    cd /d "%~dp0"
    echo [SETUP] Frontend built successfully.
)

:: 3. Check if data exists, warn if not
if not exist "%~dp0data\edumind.db" (
    echo [WARN] data\edumind.db not found. The app will create an empty database on first run.
    echo [WARN] To load demo data, run: venv\Scripts\python.exe scripts\seed_demo_student.py
    echo [WARN] Then run: venv\Scripts\python.exe scripts\seed_resources_v2.py
    echo.
)

:: 4. Start single server (backend serves API + frontend)
echo ======================================================================
echo [START] Launching EduMind (Port 8000)...
echo.
echo   Web App:    http://localhost:8000
echo   API Docs:    http://localhost:8000/docs
echo   Health:      http://localhost:8000/api/v1/health
echo.
echo   Demo Login:  demo_student / DemoPassword123!
echo   Admin Login: edumind_admin / EduMindTeam#2026!
echo.
echo   Press Ctrl+C in this window to stop the server.
echo ======================================================================
echo.

"%~dp0venv\Scripts\python.exe" -m uvicorn main:app --app-dir "%~dp0backend" --host 0.0.0.0 --port 8000

pause
