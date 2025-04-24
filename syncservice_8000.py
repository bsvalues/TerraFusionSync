"""
Start the SyncService on port 8000.

This script is used by the Replit workflow to start the SyncService on port 8000
instead of the default port 5000 to avoid conflicts with the main application.
"""

import os
import sys
import uvicorn

def main():
    """Start the SyncService on port 8000."""
    # Change directory to the syncservice directory
    os.chdir('apps/backend/syncservice')
    
    # Set the port environment variable to 8000
    os.environ["PORT"] = "8000"
    os.environ["SYNC_SERVICE_PORT"] = "8000"
    
    # Start the SyncService on port 8000
    uvicorn.run("syncservice.main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()