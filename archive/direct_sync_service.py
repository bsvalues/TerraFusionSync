#!/usr/bin/env python3
"""
Direct launcher for SyncService on port 8080.

This script bypasses any workflow configuration and directly
runs the SyncService on port 8080.
"""

import os
import sys
import signal
import subprocess

# Force port 8080
os.environ["SYNC_SERVICE_PORT"] = "8080"

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    print("SyncService terminating...")
    sys.exit(0)

def main():
    """Launch SyncService directly on port 8080."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the service with an explicitly specified port
    # This bypasses any workflow configuration that might try to use port 5000
    print("Starting SyncService on port 8080...")
    cmd = [
        "python", "-m", "uvicorn",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--app-dir", "apps/backend/syncservice",
        "syncservice.main:app"
    ]
    
    # Debug
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        # Start the service
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("SyncService terminated by user")
    except Exception as e:
        print(f"Error running SyncService: {e}")

if __name__ == "__main__":
    main()