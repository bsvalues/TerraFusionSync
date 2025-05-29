@echo off
echo TerraFusion Production Deployment
echo ==================================

echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop and try again
    pause
    exit /b 1
)

echo Checking Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not available
    echo Please ensure Docker Compose is installed
    pause
    exit /b 1
)

echo Building TerraFusion containers...
docker-compose build

echo Starting TerraFusion services...
docker-compose up -d

echo Waiting for services to start...
timeout /t 30

echo Running deployment validation...
python terrafusion_deployment_validator.py

echo TerraFusion deployment complete!
echo Access the platform at: http://localhost:5000
pause
