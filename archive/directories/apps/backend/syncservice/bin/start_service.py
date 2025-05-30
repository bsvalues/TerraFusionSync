#!/usr/bin/env python
"""
Startup script for SyncService API.

This script always starts the SyncService on port 8000 to avoid conflicts with 
the main application running on port 5000.
"""

import os
import sys
import uvicorn

def main():
    """Run the SyncService on port 8000 to avoid port conflicts."""
    port = 8000
    host = "0.0.0.0"
    
    # Get the path to the current file
    current_file = os.path.abspath(__file__)
    
    # Get the path to the syncservice package directory
    # (bin directory is at apps/backend/syncservice/bin, so go up two levels)
    syncservice_dir = os.path.dirname(os.path.dirname(current_file))
    
    # Change to the syncservice directory
    os.chdir(syncservice_dir)
    
    # Make sure the syncservice package is in the Python path
    if syncservice_dir not in sys.path:
        sys.path.insert(0, syncservice_dir)
    
    print(f"Starting SyncService API on {host}:{port}")
    
    # Run the FastAPI application with uvicorn
    uvicorn.run(
        "syncservice.main:app",
        host=host,
        port=port,
        reload=True
    )

if __name__ == "__main__":
    main()