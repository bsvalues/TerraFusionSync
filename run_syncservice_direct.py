"""
Direct runner for SyncService on port 8000.

This script imports and directly runs the FastAPI application on port 8000 
instead of relying on module imports.
"""

import os
import sys
import subprocess

# Enforce port 8000
PORT = 8000
os.environ["SYNC_SERVICE_PORT"] = str(PORT)

def main():
    """Run the SyncService directly using subprocess to guarantee port."""
    
    print(f"Starting SyncService directly on port {PORT}...")
    
    # Execute uvicorn with explicit port 8000
    cmd = [
        "python", "-m", "uvicorn",
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--app-dir", "apps/backend/syncservice",
        "syncservice.main:app"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Use subprocess to ensure environment variables are passed
    subprocess.run(cmd)

if __name__ == "__main__":
    main()