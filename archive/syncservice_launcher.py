#!/usr/bin/env python3
"""
Launcher script for SyncService.

This script will:
1. Kill any existing processes using ports 8080
2. Update all configuration to use port 8080
3. Start the SyncService on port 8080
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

def kill_process_on_port(port):
    """Kill any process using the specified port."""
    try:
        # Find processes using the port
        cmd = f"lsof -i :{port} -t"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        
        if result.stdout.strip():
            # Extract PIDs
            pids = result.stdout.strip().split('\n')
            
            # Kill each process
            for pid in pids:
                if pid:
                    print(f"Killing process {pid} using port {port}")
                    try:
                        subprocess.run(f"kill -9 {pid}", shell=True, check=True)
                    except subprocess.CalledProcessError:
                        print(f"Failed to kill process {pid}")
            
            # Wait for ports to be released
            time.sleep(1)
            return True
        return False
    except Exception as e:
        print(f"Error while killing processes on port {port}: {e}")
        return False

def main():
    """Main entry point."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=== SyncService Launcher ===")
    
    # Free up port 8080 if it's in use
    kill_process_on_port(8080)
    
    # Set environment variables
    os.environ["SYNC_SERVICE_PORT"] = "8080"
    
    # Start SyncService on port 8080
    print("Starting SyncService on port 8080...")
    
    # Change directory to where the syncservice module is located
    os.chdir("apps/backend/syncservice")
    
    # Build the command to run the SyncService
    cmd = [
        "python", "-m", "uvicorn",
        "syncservice.main:app",
        "--host", "0.0.0.0",
        "--port", "8080",
        "--reload", 
        # Add a very short reload wait time to prevent hanging
        "--reload-delay", "0.1"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    # Execute the command
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("SyncService terminated by user")
    except Exception as e:
        print(f"Error running SyncService: {e}")

if __name__ == "__main__":
    main()