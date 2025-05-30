@echo off
REM TerraFusion - Windows Service Registration Script
REM Configures TerraFusion components to run as Windows services

echo.
echo =================================================
echo TerraFusion Service Registration
echo =================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: This script requires administrator privileges
    echo Please right-click and "Run as administrator"
    pause
    exit /b 1
)

REM Set installation paths
set INSTALL_DIR=%~dp0..
set NSSM_PATH=%INSTALL_DIR%\nssm\nssm.exe
set GATEWAY_EXE=%INSTALL_DIR%\bin\terrafusion_gateway.exe
set PYTHON_EXE=%INSTALL_DIR%\python\python.exe
set SYNC_SCRIPT=%INSTALL_DIR%\scripts\sync_service.py

echo Installation directory: %INSTALL_DIR%
echo.

REM Check if NSSM exists
if not exist "%NSSM_PATH%" (
    echo ERROR: NSSM (Non-Sucking Service Manager) not found
    echo Expected location: %NSSM_PATH%
    echo Please ensure the installer completed successfully
    pause
    exit /b 1
)

echo Registering TerraFusion API Gateway service...

REM Stop and remove existing service if it exists
sc query "TerraFusion Gateway" >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping existing TerraFusion Gateway service...
    net stop "TerraFusion Gateway" >nul 2>&1
    "%NSSM_PATH%" remove "TerraFusion Gateway" confirm >nul 2>&1
)

REM Install TerraFusion API Gateway service
"%NSSM_PATH%" install "TerraFusion Gateway" "%GATEWAY_EXE%"
"%NSSM_PATH%" set "TerraFusion Gateway" DisplayName "TerraFusion API Gateway"
"%NSSM_PATH%" set "TerraFusion Gateway" Description "TerraFusion Platform API Gateway - Provides web interface and REST API for county GIS operations"
"%NSSM_PATH%" set "TerraFusion Gateway" Start SERVICE_AUTO_START
"%NSSM_PATH%" set "TerraFusion Gateway" AppDirectory "%INSTALL_DIR%"
"%NSSM_PATH%" set "TerraFusion Gateway" AppStdout "%INSTALL_DIR%\logs\gateway.log"
"%NSSM_PATH%" set "TerraFusion Gateway" AppStderr "%INSTALL_DIR%\logs\gateway_error.log"

if %errorlevel% neq 0 (
    echo ERROR: Failed to register TerraFusion Gateway service
    pause
    exit /b 1
)

echo [OK] TerraFusion API Gateway service registered

echo.
echo Registering TerraFusion Sync Service...

REM Stop and remove existing sync service if it exists
sc query "TerraFusion Sync" >nul 2>&1
if %errorlevel% equ 0 (
    echo Stopping existing TerraFusion Sync service...
    net stop "TerraFusion Sync" >nul 2>&1
    "%NSSM_PATH%" remove "TerraFusion Sync" confirm >nul 2>&1
)

REM Install TerraFusion Sync Service
"%NSSM_PATH%" install "TerraFusion Sync" "%PYTHON_EXE%"
"%NSSM_PATH%" set "TerraFusion Sync" AppParameters "%SYNC_SCRIPT%"
"%NSSM_PATH%" set "TerraFusion Sync" DisplayName "TerraFusion Sync Service"
"%NSSM_PATH%" set "TerraFusion Sync" Description "TerraFusion Platform Sync Service - Manages data synchronization between county systems"
"%NSSM_PATH%" set "TerraFusion Sync" Start SERVICE_AUTO_START
"%NSSM_PATH%" set "TerraFusion Sync" AppDirectory "%INSTALL_DIR%"
"%NSSM_PATH%" set "TerraFusion Sync" AppStdout "%INSTALL_DIR%\logs\sync.log"
"%NSSM_PATH%" set "TerraFusion Sync" AppStderr "%INSTALL_DIR%\logs\sync_error.log"

if %errorlevel% neq 0 (
    echo ERROR: Failed to register TerraFusion Sync service
    pause
    exit /b 1
)

echo [OK] TerraFusion Sync service registered

echo.
echo Creating log directories...
if not exist "%INSTALL_DIR%\logs" mkdir "%INSTALL_DIR%\logs"

echo.
echo Starting TerraFusion services...

REM Start the services
net start "TerraFusion Gateway"
if %errorlevel% neq 0 (
    echo WARNING: Failed to start TerraFusion Gateway service
    echo Check the logs at: %INSTALL_DIR%\logs\gateway_error.log
) else (
    echo [OK] TerraFusion Gateway service started
)

timeout /t 5 /nobreak >nul

net start "TerraFusion Sync"
if %errorlevel% neq 0 (
    echo WARNING: Failed to start TerraFusion Sync service
    echo Check the logs at: %INSTALL_DIR%\logs\sync_error.log
) else (
    echo [OK] TerraFusion Sync service started
)

echo.
echo =================================================
echo Service Registration Complete
echo =================================================
echo.
echo TerraFusion services are now configured to:
echo - Start automatically when Windows boots
echo - Run in the background without user login
echo - Log activity to %INSTALL_DIR%\logs\
echo.
echo Service Management:
echo - Start: net start "TerraFusion Gateway"
echo - Stop:  net stop "TerraFusion Gateway"
echo - Status: sc query "TerraFusion Gateway"
echo.
echo Access TerraFusion at: http://localhost:5000
echo.

pause
exit /b 0