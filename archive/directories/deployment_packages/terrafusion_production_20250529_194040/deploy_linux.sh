#!/bin/bash
echo "TerraFusion Production Deployment"
echo "=================================="

# Check Docker installation
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    echo "Please install Docker and try again"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not available"
    echo "Please install Docker Compose and try again"
    exit 1
fi

echo "Building TerraFusion containers..."
docker-compose build

echo "Starting TerraFusion services..."
docker-compose up -d

echo "Waiting for services to start..."
sleep 30

echo "Running deployment validation..."
python3 terrafusion_deployment_validator.py

echo "TerraFusion deployment complete!"
echo "Access the platform at: http://localhost:5000"
