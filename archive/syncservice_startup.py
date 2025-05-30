"""
Startup script for the SyncService workflow.

This script must be used as the entry point for the syncservice workflow
to ensure correct port configuration.
"""

import os
import sys
import time
import signal
import subprocess

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    print("Shutting down SyncService...")
    sys.exit(0)

def main():
    """
    Start the SyncService with port 8080 using an explicit command line.
    """
    # Register signal handlers for clean termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Enforce port 8080 via environment
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    print("Starting SyncService on port 8080...")
    
    # Kill any existing process using port 8080
    try:
        subprocess.run(["pkill", "-f", "port 8080"], check=False)
        # Give it a moment to die
        time.sleep(1)
    except Exception as e:
        print(f"Warning: Could not kill existing processes: {e}")
    
    # Start the service with explicit port 8080
    cmd = [
        "python", "-m", "uvicorn",
        "--app-dir", "apps/backend/syncservice",
        "--host", "0.0.0.0",
        "--port", "8080",
        "syncservice.main:app"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute the command
    process = subprocess.run(cmd)
    
    # If we get here, the process exited
    sys.exit(process.returncode)

if __name__ == "__main__":
    main()