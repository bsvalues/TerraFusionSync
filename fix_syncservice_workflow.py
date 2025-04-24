"""
Fix script for the SyncService workflow.

This script is designed to be used by the Replit workflow instead of directly invoking uvicorn.
It overrides any port configuration and forces the SyncService to use port 8080.
"""

import os
import sys
import subprocess

def main():
    """
    Override any workflow command line arguments to force port 8080.
    """
    print("Starting SyncService with port override...")
    
    # Set environment variable to enforce port 8080
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Build new command with port 8080
    cmd = [
        "python", "-m", "uvicorn",
        "syncservice.main:app",
        "--host", "0.0.0.0",
        "--port", "8080"
    ]
    
    # Change to the correct directory first
    os.chdir("apps/backend/syncservice")
    
    print(f"Executing command: {' '.join(cmd)}")
    print(f"Working directory: {os.getcwd()}")
    
    # Execute the command with the overridden port
    subprocess.run(cmd)

if __name__ == "__main__":
    main()