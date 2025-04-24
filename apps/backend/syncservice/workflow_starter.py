"""
Workflow starter script for the SyncService.

This script is a wrapper that will detect the port before running the actual application.
It's designed to intercept the workflow command and adjust it to use port 8000.
"""

import sys
import os
import subprocess
import signal

# Set up signal handlers
def signal_handler(sig, frame):
    print("Shutting down SyncService...")
    sys.exit(0)

def main():
    """
    Run the SyncService on port 8000 regardless of what the workflow command specifies.
    This avoids port conflicts with the main application on port 5000.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("Starting SyncService workflow starter...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set up the command to run the SyncService on port 8000
    command = [
        "python", "-m", "uvicorn", "syncservice.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ]
    
    print(f"Running command: {' '.join(command)}")
    
    # Start the process
    process = subprocess.Popen(
        command,
        cwd=current_dir,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    # Wait for the process to complete
    process.wait()
    
    # Return the process exit code
    return process.returncode

if __name__ == "__main__":
    sys.exit(main())