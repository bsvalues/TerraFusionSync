"""
Direct runner for SyncService on port 8080.

This script imports and directly runs the FastAPI application on port 8080 
instead of relying on module imports.
"""

import os
import sys
import subprocess

# Enforce port 8080
PORT = 8080
os.environ["SYNC_SERVICE_PORT"] = str(PORT)

def main():
    """Run the SyncService directly using subprocess to guarantee port."""
    
    print(f"Starting SyncService directly on port {PORT}...")
    
    # Execute our launcher script
    cmd = [
        "python", "syncservice_launcher.py"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Use subprocess to ensure environment variables are passed
    subprocess.run(cmd)

if __name__ == "__main__":
    main()