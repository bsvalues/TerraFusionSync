"""
Runner script for the SyncService.

This script starts the SyncService FastAPI application on port 8000.
"""

import os
import sys
import subprocess
import time

# Set the SyncService port
SYNC_SERVICE_PORT = 8000
os.environ["SYNC_SERVICE_PORT"] = str(SYNC_SERVICE_PORT)

def start_syncservice():
    """Start the SyncService using uvicorn."""
    try:
        # Get the project directory
        project_dir = os.path.dirname(os.path.abspath(__file__))
        
        # If there are trailing slashes, remove them
        if project_dir.endswith('/'):
            project_dir = project_dir[:-1]
        
        # Add the project directory to Python path
        sys.path.insert(0, project_dir)
        
        # Print debug information
        print(f"Starting SyncService on port {SYNC_SERVICE_PORT}")
        print(f"Project directory: {project_dir}")
        print(f"Python path: {sys.path}")
        
        # Run uvicorn command
        cmd = [
            "python", "-m", "uvicorn",
            "apps.backend.syncservice.syncservice.main:app",
            "--host", "0.0.0.0",
            "--port", str(SYNC_SERVICE_PORT)
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Start uvicorn process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for a moment to see if it starts successfully
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"SyncService started successfully on port {SYNC_SERVICE_PORT}")
            
            # Continue to print output from the process
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                
                error = process.stderr.readline()
                if error:
                    print(f"ERROR: {error.strip()}", file=sys.stderr)
                
                # If process has terminated, exit the loop
                if process.poll() is not None:
                    print("SyncService has stopped.")
                    break
                
                time.sleep(0.1)
        else:
            # Process failed to start or exited immediately
            stdout, stderr = process.communicate()
            print(f"SyncService failed to start: {stderr}", file=sys.stderr)
            return False
        
        return True
            
    except Exception as e:
        print(f"Error starting SyncService: {str(e)}", file=sys.stderr)
        return False

if __name__ == "__main__":
    start_syncservice()