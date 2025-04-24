"""
Launcher script for SyncService that forces port 8080.

This script is used to start the SyncService on port 8080 when
executed from the syncservice workflow.
"""

import os
import sys
import subprocess

def main():
    """Run the SyncService on port 8080 to avoid conflicts."""
    
    # Set the environment variable to enforce port 8080
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    print("Starting SyncService on port 8080...")
    
    # Command to run the SyncService on port 8080
    cmd = [
        "python", "-m", "uvicorn",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--app-dir", "apps/backend/syncservice",
        "syncservice.main:app"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == "__main__":
    main()