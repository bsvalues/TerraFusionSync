"""
Workflow runner for SyncService on port 8080.

This script is used by the Replit workflow to start the SyncService on port 8080
to avoid conflicts with the main application on port 5000.
"""

import os
import sys
import signal
import uvicorn

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    print("Exiting syncservice workflow runner...")
    sys.exit(0)

def main():
    """
    Run the SyncService on port 8080 for the workflow.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting SyncService on port 8080...")
    
    # Set environment variables
    os.environ["PORT"] = "8080"
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Change to the syncservice directory
    if os.path.exists('apps/backend/syncservice'):
        os.chdir('apps/backend/syncservice')
    
    # Start the SyncService on port 8080
    uvicorn.run(
        "syncservice.main:app", 
        host="0.0.0.0", 
        port=8080,
        reload=True
    )

if __name__ == "__main__":
    main()