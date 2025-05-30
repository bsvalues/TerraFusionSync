"""
Wrapper script to start SyncService on the correct port.

This script is used by the Replit workflow to start the SyncService.
It enforces using port 8000 to avoid conflicts with the main application.
"""

import os
import sys
import signal
import uvicorn
import time

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    print("SyncService terminating gracefully...")
    sys.exit(0)

def main():
    """
    Start the SyncService on port 8000 regardless of workflow command.
    This avoids conflicts with the main Flask application on port 5000.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Force port 8080 no matter what
    port = 8080
    os.environ["SYNC_SERVICE_PORT"] = str(port)
    
    print(f"Starting SyncService on port {port}...")
    
    # Get the directory containing this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add current directory to Python path if not already there
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Run uvicorn
    uvicorn.run(
        "apps.backend.syncservice.syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()