"""
Workflow runner for SyncService on port 8080.

This script is used by the Replit workflow to start the SyncService on port 8080
to avoid conflicts with the main application on port 5000.
"""

import os
import sys
import time
import signal
import subprocess

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    print("Shutting down SyncService...")
    sys.exit(0)

def main():
    """
    Run the SyncService on port 8080 for the workflow.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Enforce port 8080
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Change directory to syncservice location
    os.chdir("apps/backend/syncservice")
    
    print("Starting SyncService workflow on port 8080...")
    
    # Command that explicitly sets the port to 8080
    cmd = [
        "python", "-m", "uvicorn",
        "syncservice.main:app",
        "--host", "0.0.0.0",
        "--port", "8080"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Run the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("SyncService terminated by user.")
    except Exception as e:
        print(f"Error running SyncService: {e}")

if __name__ == "__main__":
    main()