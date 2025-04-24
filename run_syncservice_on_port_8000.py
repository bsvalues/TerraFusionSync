"""
Runner script for the SyncService on port 8000.

This script starts the SyncService FastAPI application on port 8000.
"""

import os
import sys
import uvicorn

# Set environment variables for port
os.environ["SYNC_SERVICE_PORT"] = "8000"

def main():
    """
    Main entry point for the SyncService.
    """
    print(f"Starting SyncService on port 8000...")
    
    # Get the absolute path to the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the current directory to Python path
    sys.path.insert(0, current_dir)
    
    # Start the FastAPI application on port 8000
    uvicorn.run(
        "apps.backend.syncservice.syncservice.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()