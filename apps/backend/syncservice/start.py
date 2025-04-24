"""
Entry point script for the SyncService when running in the workflow.

This file is meant to be executed directly to run the FastAPI application.
"""

import os
import sys
import uvicorn
import socket

# Get the directory containing this file
app_directory = os.path.dirname(os.path.abspath(__file__))

# Add the applications directory to sys.path
if app_directory not in sys.path:
    sys.path.insert(0, app_directory)

# Function to get the port for SyncService
def get_available_port():
    # Always use port 8000 for SyncService
    # This avoids conflict with the main application on port 5000
    return 8000

if __name__ == "__main__":
    port = get_available_port()
    
    print(f"Starting SyncService on port {port}")
    print(f"Python path: {sys.path}")
    
    # Run the FastAPI application
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )