#!/bin/bash

# Force port 8000 for SyncService
export SYNC_SERVICE_PORT=8000

echo "Starting SyncService on port 8000..."

# Get current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "Current directory: $DIR"

# Run using uvicorn directly with explicit port
python -m uvicorn syncservice.main:app --host 0.0.0.0 --port 8000