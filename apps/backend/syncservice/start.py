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

# Function to check if port 5000 is in use and select 8000 as an alternative
def get_available_port():
    # First try port 8000 (preferred)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 8000))
        s.close()
        return 8000
    except socket.error:
        # If port 8000 is not available
        try:
            # Check if port 5000 is available
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', 5000))
            s.close()
            return 5000
        except socket.error:
            # If neither port is available, try port 8080
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind(('0.0.0.0', 8080))
                s.close()
                return 8080
            except socket.error:
                # If all ports are taken, default to 8000 and let uvicorn handle the error
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