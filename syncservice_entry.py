"""
Entry point for the SyncService workflow.

This script will detect an available port and start the SyncService.
"""

import os
import sys
import socket
import time
import subprocess

# Function to check if port 5000 is in use and select 8000 as an alternative
def get_available_port():
    # Always use port 8000 for SyncService
    return 8000

if __name__ == "__main__":
    # Get working directory
    working_dir = os.path.dirname(os.path.abspath(__file__))
    if working_dir != os.getcwd():
        print(f"Changing directory to: {working_dir}")
        os.chdir(working_dir)
    
    # Get the syncservice directory
    syncservice_dir = os.path.join(os.getcwd(), "apps/backend/syncservice")
    
    if os.path.exists(syncservice_dir):
        print(f"Found syncservice directory: {syncservice_dir}")
    else:
        print(f"Error: Directory not found: {syncservice_dir}")
        sys.exit(1)
    
    # Move to the syncservice directory
    os.chdir(syncservice_dir)
    
    # Get an available port (always use 8000)
    port = get_available_port()
    print(f"Starting SyncService on port {port}")
    
    # Add the current directory to the Python path
    if syncservice_dir not in sys.path:
        sys.path.insert(0, syncservice_dir)
    
    # Start the SyncService using subprocess
    try:
        print("Running command: python -m uvicorn syncservice.main:app --host 0.0.0.0 --port 8000")
        
        process = subprocess.Popen(
            ["python", "-m", "uvicorn", "syncservice.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait a bit to make sure the process has started
        time.sleep(2)
        
        # Check if the process is still running
        if process.poll() is None:
            print("SyncService started successfully!")
            
            # Read and print output
            while True:
                output = process.stdout.readline()
                if output:
                    print(output.strip())
                if process.poll() is not None:
                    break
        else:
            print("Error: SyncService failed to start")
            stderr = process.stderr.read()
            print(f"Error output: {stderr}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error starting SyncService: {e}")
        sys.exit(1)