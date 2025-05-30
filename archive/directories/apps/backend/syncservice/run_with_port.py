#!/usr/bin/env python
"""
Port-aware runner for the SyncService.

This script starts the SyncService on port 8000 to avoid conflicts with the main application.
"""

import os
import sys
import uvicorn

def main():
    """
    Run the SyncService on port 8000 instead of the default port 5000.
    """
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Make sure the syncservice package is in the Python path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Change to the syncservice directory
    os.chdir(current_dir)
    
    # Run the FastAPI application with uvicorn on port 8000
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    main()