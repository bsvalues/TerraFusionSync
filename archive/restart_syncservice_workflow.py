"""
Script to restart the SyncService workflow with proper port configuration.

This script stops any existing SyncService processes and starts a new one on port 8080.
"""

import os
import signal
import subprocess
import time
import psutil

def find_syncservice_processes():
    """Find any running SyncService processes."""
    syncservice_pids = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Look for uvicorn processes running syncservice
            if proc.info['cmdline'] and any('syncservice' in arg for arg in proc.info['cmdline']):
                syncservice_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return syncservice_pids

def stop_existing_syncservices():
    """Stop any existing SyncService processes."""
    pids = find_syncservice_processes()
    
    if not pids:
        print("No existing SyncService processes found.")
        return
    
    print(f"Found {len(pids)} SyncService processes to stop: {pids}")
    
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to process {pid}")
        except OSError as e:
            print(f"Error stopping process {pid}: {e}")
    
    # Give them a moment to shut down gracefully
    time.sleep(2)
    
    # Check if any are still running
    remaining = find_syncservice_processes()
    if remaining:
        print(f"Some processes still running: {remaining}, forcing termination...")
        for pid in remaining:
            try:
                os.kill(pid, signal.SIGKILL)
                print(f"Sent SIGKILL to process {pid}")
            except OSError:
                pass

def start_syncservice_on_port_8080():
    """Start SyncService on port 8080."""
    print("Starting SyncService on port 8080...")
    
    # Use the dedicated runner script
    runner_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "run_syncservice_workflow_8080.py")
    
    # Start the process
    process = subprocess.Popen(
        ["python", runner_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    print(f"Started SyncService (PID: {process.pid})")
    
    # Wait a moment for it to start
    time.sleep(3)
    
    # Check if it's running
    if process.poll() is None:
        print("SyncService started successfully!")
    else:
        stdout, stderr = process.communicate()
        print("SyncService failed to start:")
        print(f"STDOUT: {stdout}")
        print(f"STDERR: {stderr}")

def main():
    """Main entry point."""
    print("Restarting SyncService workflow...")
    
    # Stop any existing instances
    stop_existing_syncservices()
    
    # Start on the correct port
    start_syncservice_on_port_8080()
    
    print("Workflow restart complete.")

if __name__ == "__main__":
    main()