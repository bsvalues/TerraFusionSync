@echo off
REM TerraFusion Platform - Unified Rust Service Launcher
REM This script starts all TerraFusion services in the optimal order
REM for county IT operations

echo ========================================
echo TerraFusion Platform - Starting Services
echo ========================================
echo.

REM Check if we're in admin mode
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] Running with administrator privileges
) else (
    echo [!] Warning: Not running as administrator
    echo     Some features may not work properly
    echo.
)

REM Set environment variables
set RUST_LOG=info
set TERRAFUSION_ENV=production
set DATABASE_URL=%DATABASE_URL%

echo [1/6] Checking prerequisites...
where rustc >nul 2>&1
if %errorLevel% neq 0 (
    echo [✗] Rust not found. Please run setup_rust_prereqs.ps1 first
    pause
    exit /b 1
) else (
    echo [✓] Rust toolchain detected
)

echo.
echo [2/6] Starting PostgreSQL database...
REM Check if PostgreSQL is running
sc query postgresql >nul 2>&1
if %errorLevel% == 0 (
    echo [✓] PostgreSQL service is running
) else (
    echo [!] Starting PostgreSQL service...
    net start postgresql
)

echo.
echo [3/6] Building and starting Rust API Gateway...
cd terrarust\api_gateway
if exist "Cargo.toml" (
    echo [✓] Building API Gateway...
    cargo build --release
    if %errorLevel% == 0 (
        echo [✓] Starting API Gateway on port 8080...
        start "TerraFusion API Gateway" cargo run --release
        timeout /t 3 >nul
    ) else (
        echo [✗] Failed to build API Gateway
    )
    cd ..\..
) else (
    echo [!] API Gateway not found, using Python fallback...
    start "TerraFusion Python API" python app.py
)

echo.
echo [4/6] Building and starting Rust GIS Export Service...
cd terrarust\gis_export
if exist "Cargo.toml" (
    echo [✓] Building GIS Export Service...
    cargo build --release
    if %errorLevel% == 0 (
        echo [✓] Starting GIS Export Service on port 8081...
        start "TerraFusion GIS Export" cargo run --release
        timeout /t 3 >nul
    ) else (
        echo [✗] Failed to build GIS Export Service
    )
    cd ..\..
) else (
    echo [!] GIS Export Service not found, skipping...
    cd ..\..
)

echo.
echo [5/6] Starting Python Sync Service...
if exist "syncservice.py" (
    echo [✓] Starting Sync Service on port 8080...
    start "TerraFusion Sync Service" python run_syncservice_workflow_8080.py
    timeout /t 3 >nul
) else (
    echo [!] Sync Service not found
)

echo.
echo [6/6] Starting NarratorAI Service...
if exist "narrator_ai_plugin.py" (
    echo [✓] NarratorAI plugin detected
    echo [i] AI service will start with main application
) else (
    echo [!] NarratorAI not found
)

echo.
echo ========================================
echo TerraFusion Platform Status
echo ========================================
echo.
echo Services starting up...
echo Please wait 30 seconds for all services to initialize.
echo.
echo Web Interface: http://localhost:5000
echo API Gateway:   http://localhost:8080 (if Rust)
echo GIS Export:    http://localhost:8081 (if Rust)
echo Sync Service:  http://localhost:8080
echo.
echo Monitoring:    http://localhost:3000 (Grafana)
echo Metrics:       http://localhost:9090 (Prometheus)
echo.
echo ========================================

REM Wait and then check service health
timeout /t 30 >nul
echo Checking service health...

powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:5000/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Host '[✓] Main application healthy' } else { Write-Host '[!] Main application not responding' } } catch { Write-Host '[!] Main application not accessible' }"

powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://localhost:8080/health' -TimeoutSec 5; if ($response.StatusCode -eq 200) { Write-Host '[✓] API Gateway healthy' } else { Write-Host '[!] API Gateway not responding' } } catch { Write-Host '[!] API Gateway not accessible' }"

echo.
echo ========================================
echo TerraFusion Platform Ready for County Operations
echo ========================================
echo.
pause