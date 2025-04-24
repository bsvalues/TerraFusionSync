#!/usr/bin/env python3
"""
Entry point for the SyncService workflow in Replit.

This script overrides any port settings and forces the SyncService
to use port 8080 to avoid conflicts with the main application.
"""

import os
import sys
import subprocess

def main():
    """
    Main entry point for the SyncService workflow.
    
    - Sets environment variables to force port 8080
    - Launches the SyncService with the correct port
    """
    # Force port 8080
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    print("SyncService workflow starting on port 8080...")
    
    # Use syncservice_launcher.py to start the service
    # This kills any existing processes on port 8080 and starts a fresh instance
    try:
        subprocess.run(["python", "syncservice_launcher.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running SyncService: {e}")
        return 1
    except KeyboardInterrupt:
        print("SyncService terminated by user")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())