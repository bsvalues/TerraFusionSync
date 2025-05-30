"""
Run SyncService on port 8000.

This script starts the SyncService on port 8000 to avoid conflicts with the main application.
"""

import os
import sys
import subprocess

def main():
    """
    Start the SyncService on port 8000.
    """
    # Set the port environment variable
    os.environ["SYNC_SERVICE_PORT"] = "8000"
    
    # Build the command to run SyncService
    cmd = [
        "python", "-m", "uvicorn", 
        "apps.backend.syncservice.syncservice.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000"
    ]
    
    # Run the command
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    # Stream the output
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
    
    # Wait for process to complete
    process.wait()
    
    # Return the exit code
    return process.returncode

if __name__ == "__main__":
    sys.exit(main())