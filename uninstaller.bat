@echo off
REM TerraFusion Platform - Clean Uninstaller
REM Removes all services and optionally cleans up dependencies

echo.
echo ========================================================
echo  TerraFusion Platform - Clean Uninstaller
echo ========================================================
echo.

echo WARNING: This will completely remove TerraFusion from your system.
echo.
set /p confirm="Are you sure you want to continue? (y/N): "
if /i not "%confirm%"=="y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo Stopping all TerraFusion services...

REM Stop all TerraFusion processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq TerraFusion*" 2>nul
taskkill /f /im gunicorn.exe 2>nul
taskkill /f /t /im cmd.exe /fi "WINDOWTITLE eq TerraFusion*" 2>nul

echo ✓ Services stopped

REM Remove scheduled tasks (if any)
schtasks /delete /tn "TerraFusion*" /f 2>nul

echo ✓ Scheduled tasks removed

REM Clean up temporary files
if exist "%TEMP%\terrafusion*" (
    rmdir /s /q "%TEMP%\terrafusion*" 2>nul
    echo ✓ Temporary files cleaned
)

REM Clean up logs
if exist "logs" (
    rmdir /s /q "logs" 2>nul
    echo ✓ Log files removed
)

REM Clean up backup files
if exist "backups" (
    rmdir /s /q "backups" 2>nul
    echo ✓ Backup files removed
)

REM Remove Python cache
if exist "__pycache__" (
    rmdir /s /q "__pycache__" 2>nul
    echo ✓ Python cache cleared
)

echo.
echo ========================================================
echo  Optional: Remove Development Dependencies
echo ========================================================
echo.
echo The following were installed for TerraFusion:
echo - Python 3.11
echo - Rust toolchain
echo - Visual Studio Build Tools
echo.
set /p cleanup="Remove these as well? (y/N): "
if /i "%cleanup%"=="y" (
    echo.
    echo Removing Python packages...
    python -m pip uninstall -y flask fastapi sqlalchemy gunicorn uvicorn 2>nul
    
    echo Removing Rust...
    rustup self uninstall -y 2>nul
    
    echo Note: Visual Studio Build Tools must be removed manually
    echo through Windows "Add or Remove Programs"
    echo.
    echo ✓ Development dependencies removed
)

echo.
echo ========================================================
echo  Uninstall Complete
echo ========================================================
echo.
echo TerraFusion has been completely removed from your system.
echo.
echo To reinstall:
echo 1. Extract TerraFusion files to a new location
echo 2. Run setup_rust_prereqs.ps1
echo 3. Run run_all_rust.bat
echo.
echo Thank you for using TerraFusion Platform!
echo.
pause