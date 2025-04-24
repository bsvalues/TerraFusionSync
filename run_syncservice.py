"""
Script to run SyncService on port 8000.

This script will be executed by the workflow to start the SyncService.
"""

import os
import sys
import subprocess

def main():
    # Get the path to the syncservice package
    syncservice_dir = os.path.join(os.getcwd(), "apps/backend/syncservice")
    
    if not os.path.exists(syncservice_dir):
        print(f"Error: SyncService directory not found at {syncservice_dir}")
        sys.exit(1)
    
    # Change to the syncservice directory
    os.chdir(syncservice_dir)
    
    # Always use port 8000 for SyncService
    port = 8000
    host = "0.0.0.0"
    
    print(f"Starting SyncService on {host}:{port}")
    
    # Run the uvicorn server with the FastAPI app
    cmd = [
        "python", "-m", "uvicorn", 
        "syncservice.main:app", 
        "--host", host, 
        "--port", str(port)
    ]
    
    try:
        process = subprocess.Popen(cmd)
        process.wait()
    except KeyboardInterrupt:
        print("SyncService stopped by user")
    except Exception as e:
        print(f"Error running SyncService: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()