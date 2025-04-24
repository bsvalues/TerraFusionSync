"""
Entry point script for the SyncService workflow.

This script overrides any port settings from the workflow configuration
and ensures that the SyncService always runs on port 8080.
"""

import os
import sys
import time
import signal
import subprocess

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    print("Shutting down SyncService...")
    sys.exit(0)

def main():
    """
    Main entry point that forces the SyncService to run on port 8080.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Enforce port 8080
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Kill any existing process using port 8080
    try:
        subprocess.run(["pkill", "-f", "port 8080"], check=False)
        # Give it a moment to die
        time.sleep(1)
    except Exception as e:
        print(f"Warning when killing processes: {e}")
    
    print("Starting SyncService workflow entry point...")
    print("Current directory:", os.getcwd())
    
    # Change to syncservice directory if needed
    if not os.path.exists("syncservice"):
        os.chdir("apps/backend/syncservice")
        print("Changed to directory:", os.getcwd())
    
    # Build the command to run the SyncService
    cmd = [
        "python", "-m", "uvicorn", 
        "syncservice.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8080"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("SyncService terminated by user.")
    except Exception as e:
        print(f"Error running SyncService: {e}")

if __name__ == "__main__":
    main()