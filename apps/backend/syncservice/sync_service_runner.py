"""
Runner script for the SyncService.

This script is used to start the SyncService on port 8000.
"""

import sys
import os
import subprocess
import signal
import time

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    print('Shutting down SyncService...')
    sys.exit(0)

def main():
    """Run the SyncService on port 8000."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get the directory containing this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Current directory: {current_dir}")
    print("Starting SyncService on port 8000...")
    
    # IMPORTANT: Use port 8000 instead of 5000
    command = [
        "python", "-m", "uvicorn", "syncservice.main:app", 
        "--host", "0.0.0.0", "--port", "8000", "--reload"
    ]
    
    # Start the process
    process = subprocess.Popen(
        command, 
        cwd=current_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True
    )
    
    print(f"SyncService started with PID: {process.pid}")
    
    # Monitor the process
    try:
        while True:
            output = process.stdout.readline()
            if output:
                print(output.strip())
            
            # Check if process has terminated
            if process.poll() is not None:
                print("SyncService process terminated unexpectedly")
                
                # Read any remaining output
                for output in process.stdout.readlines():
                    print(output.strip())
                
                # Try to restart
                print("Attempting to restart SyncService...")
                time.sleep(2)  # Wait before restarting
                process = subprocess.Popen(
                    command,
                    cwd=current_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )
                print(f"SyncService restarted with PID: {process.pid}")
    
    except KeyboardInterrupt:
        print("Received keyboard interrupt. Shutting down...")
        process.terminate()
        process.wait()
        print("SyncService shut down gracefully")

if __name__ == "__main__":
    main()