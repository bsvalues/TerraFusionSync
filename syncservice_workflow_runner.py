#!/usr/bin/env python
"""
Dedicated runner script for the SyncService workflow.

This script explicitly sets port 8000 for the SyncService to avoid conflicts with
the main application running on port 5000. It's designed to be the entry point
for the syncservice workflow.
"""

import sys
import os
import subprocess

def main():
    """
    Run the SyncService workflow on port 8000.
    """
    try:
        print("Starting SyncService workflow on port 8000...")
        
        # Get the path to the syncservice directory
        syncservice_dir = os.path.join(os.getcwd(), "apps/backend/syncservice")
        
        # Construct the command to run uvicorn directly with port 8000
        cmd = [
            sys.executable, "-m", "uvicorn", 
            "syncservice.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ]
        
        # Execute the command from the syncservice directory
        print(f"Executing command: {' '.join(cmd)}")
        subprocess.run(cmd, cwd=syncservice_dir, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"Error running SyncService: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()