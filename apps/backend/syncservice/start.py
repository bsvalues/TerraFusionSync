"""
Entry point script for the SyncService when running in the workflow.

This file is meant to be executed directly to run the FastAPI application.
"""

import os
import sys
import uvicorn

# Get the directory containing this file
app_directory = os.path.dirname(os.path.abspath(__file__))

# Add the applications directory to sys.path
if app_directory not in sys.path:
    sys.path.insert(0, app_directory)

if __name__ == "__main__":
    port = 8000  # Use port 8000 instead of 5000 to avoid conflicts
    
    print(f"Starting SyncService on port {port}")
    print(f"Python path: {sys.path}")
    
    # Run the FastAPI application
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )