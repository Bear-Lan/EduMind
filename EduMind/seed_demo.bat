@echo off
title EduMind Demo Data Seeder
color 0E
echo ======================================================================
echo           EduMind V1 -- Demo Data Seeder
echo           Run this AFTER starting deploy.bat (backend must be running)
echo ======================================================================
echo.

:: Check if backend is running
echo [CHECK] Testing backend connection...
"%~dp0venv\Scripts\python.exe" -c "import httpx; r=httpx.get('http://127.0.0.1:8000/api/v1/health'); print('OK' if r.status_code==200 else 'FAIL')" 2>nul | findstr "OK" >nul
if errorlevel 1 (
    echo [ERROR] Backend is not running on port 8000.
    echo         Please start deploy.bat first, then run this script.
    pause
    exit /b 1
)
echo [OK] Backend is running.
echo.

:: 1. Seed demo student
echo [1/2] Seeding demo student (demo_student / DemoPassword123!)...
"%~dp0venv\Scripts\python.exe" "%~dp0scripts\seed_demo_student.py"
if errorlevel 1 (
    echo [WARN] Demo student seeding had issues (may already exist).
) else (
    echo [OK] Demo student ready.
)
echo.

:: 2. Seed textbook resources (requires admin password)
echo [2/2] Seeding textbook resources (requires admin login)...
set ADMIN_PASSWORD=EduMindTeam#2026!
"%~dp0venv\Scripts\python.exe" "%~dp0scripts\seed_via_api.py"
if errorlevel 1 (
    echo [ERROR] Resource seeding failed. Check the error above.
    echo         If admin password was changed, set ADMIN_PASSWORD env var.
    pause
    exit /b 1
)
echo.

echo ======================================================================
echo [DONE] Demo data seeded successfully!
echo.
echo   Demo Student:  demo_student / DemoPassword123!
echo   Admin Login:  edumind_admin / EduMindTeam#2026!
echo.
echo   Open: http://localhost:8000
echo ======================================================================
pause
