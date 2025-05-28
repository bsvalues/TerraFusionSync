@echo off
REM TerraFusion Platform - One-Click Launch Script
REM Launches Gateway, GIS Export Service, and NarratorAI
REM For Windows deployment to county IT staff

echo.
echo ========================================================
echo  TerraFusion Platform - Starting All Services
echo ========================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please run setup_rust_prereqs.ps1 first
    pause
    exit /b 1
)

REM Check if required directories exist
if not exist "apps\api" (
    echo ERROR: API service directory not found
    echo Please ensure TerraFusion is properly installed
    pause
    exit /b 1
)

REM Kill any existing processes to avoid port conflicts
echo Stopping any existing TerraFusion services...
taskkill /f /im python.exe /fi "WINDOWTITLE eq TerraFusion*" 2>nul
taskkill /f /im gunicorn.exe 2>nul

REM Wait a moment for cleanup
timeout /t 2 /nobreak >nul

echo.
echo Starting TerraFusion Gateway (Port 5000)...
start "TerraFusion Gateway" cmd /k "cd /d %~dp0 && python -m gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"

REM Wait for gateway to start
timeout /t 3 /nobreak >nul

echo Starting SyncService (Port 8080)...
start "TerraFusion SyncService" cmd /k "cd /d %~dp0 && python run_syncservice_workflow_8080.py"

REM Wait for syncservice to start
timeout /t 3 /nobreak >nul

echo Starting NarratorAI Service...
if exist "ai\narrator_ai" (
    start "TerraFusion NarratorAI" cmd /k "cd /d %~dp0\ai\narrator_ai && python narrator_ai_service.py"
) else (
    echo Warning: NarratorAI directory not found, skipping...
)

echo.
echo ========================================================
echo  TerraFusion Platform Services Started
echo ========================================================
echo.
echo  Gateway:     http://localhost:5000
echo  SyncService: http://localhost:8080
echo  NarratorAI:  http://localhost:8081 (if available)
echo.
echo  Dashboard:   http://localhost:5000/dashboard
echo  GIS Export:  http://localhost:5000/gis-dashboard
echo  Health:      http://localhost:5000/health
echo.
echo Press any key to open the dashboard in your browser...
pause >nul

REM Open dashboard in default browser
start http://localhost:5000/dashboard

echo.
echo All services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause