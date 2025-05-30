"""
Port override script for SyncService.

This script forces the SyncService to run on port 8080 regardless of
any other configuration or command line arguments.
"""

import os
import sys
import subprocess

def main():
    """Force SyncService to run on port 8080."""
    
    # Set environment variable
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    print("Starting SyncService with forced port 8080")
    
    # Run uvicorn as a subprocess with the forced port
    cmd = [
        "python", "-m", "uvicorn", 
        "syncservice.main:app",
        "--host", "0.0.0.0",
        "--port", "8080"
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    
    # Execute the command
    subprocess.run(cmd)

if __name__ == "__main__":
    main()