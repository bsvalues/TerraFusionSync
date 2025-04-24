#!/usr/bin/env python
"""
Startup script for SyncService workflow.

This script explicitly runs the SyncService on port 8000 to avoid 
conflicts with the main application on port 5000.
"""

import os
import sys
import subprocess

def main():
    """
    Entry point for the SyncService workflow.
    Always runs on port 8000 to avoid conflicts.
    """
    try:
        print("Starting SyncService API on port 8000...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Change to the SyncService directory
        syncservice_dir = os.path.join(current_dir, "apps/backend/syncservice")
        os.chdir(syncservice_dir)
        
        # Construct the command
        cmd = [
            "python", "-m", "uvicorn", 
            "syncservice.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ]
        
        # Run the command
        process = subprocess.Popen(cmd)
        process.wait()
        
    except Exception as e:
        print(f"Error starting SyncService: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()