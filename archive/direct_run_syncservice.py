#!/usr/bin/env python3
"""
Direct runner for SyncService on port 8080.

This script directly starts the SyncService FastAPI application on port 8080.
"""

import os
import subprocess
import sys
import time
import signal

def main():
    """Run the SyncService directly on port 8080."""
    # Force the port via environment variable
    os.environ['SYNC_SERVICE_PORT'] = '8080'
    
    # Build the command
    cmd = [
        'python', '-m', 'uvicorn', 
        'syncservice.main:app', 
        '--host', '0.0.0.0', 
        '--port', '8080',
        '--reload'
    ]
    
    # Change directory to the syncservice directory
    os.chdir('apps/backend/syncservice')
    
    # Start the process
    print(f"Starting SyncService with command: {' '.join(cmd)}")
    process = subprocess.Popen(cmd)
    
    # Set up signal handling
    def handle_signal(sig, frame):
        print(f"Received signal {sig}, stopping SyncService...")
        process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Wait for the process to complete
    process.wait()

if __name__ == '__main__':
    main()
