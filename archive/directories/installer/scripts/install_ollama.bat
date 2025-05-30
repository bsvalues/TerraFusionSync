@echo off
REM TerraFusion - Ollama AI Runtime Installation Script
REM This script sets up the Ollama AI service for NarratorAI features

echo.
echo =================================================
echo TerraFusion AI Runtime Setup
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

REM Set installation directory
set INSTALL_DIR=%~dp0..
set OLLAMA_DIR=%INSTALL_DIR%\ollama
set MODEL_NAME=llama3.2:3b

echo Installing Ollama AI Runtime...
echo Installation directory: %OLLAMA_DIR%

REM Create Ollama directory
if not exist "%OLLAMA_DIR%" mkdir "%OLLAMA_DIR%"

REM Download Ollama if not present
if not exist "%OLLAMA_DIR%\ollama.exe" (
    echo Downloading Ollama runtime...
    powershell -Command "Invoke-WebRequest -Uri 'https://ollama.ai/download/ollama-windows-amd64.exe' -OutFile '%OLLAMA_DIR%\ollama.exe'"
    
    if %errorlevel% neq 0 (
        echo ERROR: Failed to download Ollama
        echo Please check your internet connection and try again
        pause
        exit /b 1
    )
    
    echo Ollama downloaded successfully
) else (
    echo Ollama already installed
)

REM Start Ollama service
echo Starting Ollama service...
start "" "%OLLAMA_DIR%\ollama.exe" serve

REM Wait for service to start
echo Waiting for Ollama to initialize...
timeout /t 10 /nobreak >nul

REM Pull the AI model
echo.
echo Downloading AI model (%MODEL_NAME%)...
echo This may take several minutes depending on your internet connection
echo.

"%OLLAMA_DIR%\ollama.exe" pull %MODEL_NAME%

if %errorlevel% neq 0 (
    echo WARNING: Failed to download AI model
    echo TerraFusion will work without AI features
    echo You can retry this later by running: ollama pull %MODEL_NAME%
) else (
    echo AI model installed successfully
)

REM Test the installation
echo.
echo Testing AI installation...
"%OLLAMA_DIR%\ollama.exe" list | findstr %MODEL_NAME% >nul

if %errorlevel% equ 0 (
    echo [SUCCESS] AI runtime is ready
    echo NarratorAI features will be available in TerraFusion
) else (
    echo [WARNING] AI model not found
    echo NarratorAI features may not work properly
)

echo.
echo =================================================
echo AI Runtime Setup Complete
echo =================================================
echo.
echo To use AI features in TerraFusion:
echo 1. Ensure this script completed successfully
echo 2. Start TerraFusion Platform
echo 3. AI analysis will be available in export jobs
echo.

pause
exit /b 0