#!/bin/bash
# Azure Web App startup script for TerraFusion Platform

# Log startup
echo "Starting TerraFusion Platform services..."
echo "Environment: $APPSETTING_ENVIRONMENT"

# Create necessary directories if they don't exist
mkdir -p logs
mkdir -p data
mkdir -p tmp

# Install any missing dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements.azure.txt

# Configure the application
echo "Configuring application..."

# Set environment variables (if not set via app settings)
export PYTHONPATH="$PYTHONPATH:$HOME/site/wwwroot"
export PORT="${PORT:-8000}"
export FLASK_APP="app_azure:app"

# Set up database
python -c "
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app_azure import db
with db.engine.connect() as conn:
    conn.execute('SELECT 1')
print('Database connection successful')
"

# Start the application
if [[ -z "$APPSETTING_STARTUP_COMMAND" ]]; then
    # Default startup if not specified in app settings
    echo "Starting with default command..."
    if [[ "$APPSETTING_APP_TYPE" == "SYNCSERVICE" ]]; then
        echo "Starting SyncService..."
        exec uvicorn syncservice_azure:app --host 0.0.0.0 --port $PORT --workers 4
    else
        echo "Starting API Gateway..."
        exec gunicorn --bind=0.0.0.0:$PORT --workers=4 --timeout=120 app_azure:app
    fi
else
    # Use the startup command specified in app settings
    echo "Starting with custom command: $APPSETTING_STARTUP_COMMAND"
    exec $APPSETTING_STARTUP_COMMAND
fi