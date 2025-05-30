"""
Workflow starter for SyncService.

This script is used to run the SyncService FastAPI application
directly from the workflow environment.
"""

import os
import sys
import subprocess

def main():
    """Run SyncService on port 8000 via subprocess."""
    
    # Force port 8000
    port = 8000
    os.environ["SYNC_SERVICE_PORT"] = str(port)
    print(f"Starting SyncService on port {port}...")
    
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"Current directory: {current_dir}")
    
    # Run the uvicorn command via subprocess to ensure environment variables are passed
    cmd = [
        "python", "-m", "uvicorn",
        "syncservice.main:app",
        "--host=0.0.0.0",
        "--port=8000"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Run in the current directory
        subprocess.run(cmd, cwd=current_dir)
    except Exception as e:
        print(f"Error running SyncService: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()