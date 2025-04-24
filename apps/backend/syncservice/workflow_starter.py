#!/usr/bin/env python
"""
Wrapper script to start SyncService on the correct port.

This script is used by the Replit workflow to start the SyncService.
It enforces using port 8000 to avoid conflicts with the main application.
"""

import os
import sys
import signal
import subprocess

def signal_handler(sig, frame):
    print("Terminating SyncService workflow starter...")
    sys.exit(0)

def main():
    """
    Start the SyncService on port 8000 regardless of workflow command.
    This avoids conflicts with the main Flask application on port 5000.
    """
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build the command to run the uvicorn server on port 8000
    cmd = [
        sys.executable, "-m", "uvicorn",
        "syncservice.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]

    print(f"Starting SyncService with command: {' '.join(cmd)}")

    try:
        # Run the command and wait for it to complete
        subprocess.check_call(cmd)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting...")
    except subprocess.CalledProcessError as e:
        print(f"Error running SyncService: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())