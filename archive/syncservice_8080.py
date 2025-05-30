"""
Start the SyncService on port 8080.

This script is used by the Replit workflow to start the SyncService on port 8080
instead of the default port 5000 to avoid conflicts with the main application.
"""

import os
import sys
import uvicorn

def main():
    """Start the SyncService on port 8080."""
    # Change directory to the syncservice directory
    os.chdir('apps/backend/syncservice')
    
    # Set the port environment variable to 8080
    os.environ["PORT"] = "8080"
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Start the SyncService on port 8080
    uvicorn.run("apps.backend.syncservice.syncservice.main:app", host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()