"""
Port-aware runner for the SyncService.

This script starts the SyncService on port 8000 to avoid conflicts with the main application.
"""

import sys
import os
import subprocess

def main():
    """
    Run the SyncService on port 8000 instead of the default port 5000.
    """
    # Set up the command to run uvicorn with the correct port
    cmd = [
        "python", "-m", "uvicorn", 
        "syncservice.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    
    print(f"Starting SyncService on port 8000: {' '.join(cmd)}")
    
    try:
        # Execute the command
        process = subprocess.Popen(
            cmd,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        
        # Wait for the process to complete
        process.wait()
        
        return process.returncode
    except Exception as e:
        print(f"Error running SyncService: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())