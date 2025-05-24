#!/usr/bin/env python3
"""
TerraFusion Platform - Port Conflict Resolver

This script identifies and terminates processes using port 5000 to allow
the application to start properly.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def find_processes_using_port(port):
    """Find processes using a specific port."""
    try:
        # Find process IDs using the port
        result = subprocess.run(
            ["lsof", "-i", f":{port}", "-t"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            return [int(pid) for pid in result.stdout.strip().split('\n')]
        return []
    except Exception as e:
        logger.error(f"Error finding processes on port {port}: {str(e)}")
        return []

def kill_process(pid):
    """Kill a process by PID."""
    try:
        logger.info(f"Attempting to terminate process {pid}")
        os.kill(pid, 15)  # SIGTERM
        logger.info(f"Successfully terminated process {pid}")
        return True
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {str(e)}")
        return False

def main():
    """Main function to find and kill processes on port 5000."""
    port = 5000
    logger.info(f"Looking for processes using port {port}")
    
    pids = find_processes_using_port(port)
    
    if not pids:
        logger.info(f"No processes found using port {port}")
        return
    
    logger.info(f"Found {len(pids)} processes using port {port}: {pids}")
    
    # Kill each process
    for pid in pids:
        kill_process(pid)
    
    # Verify port is now free
    remaining_pids = find_processes_using_port(port)
    if remaining_pids:
        logger.warning(f"Some processes still using port {port}: {remaining_pids}")
        logger.warning("Try running 'sudo lsof -i :5000' and 'sudo kill <PID>' manually")
    else:
        logger.info(f"Port {port} is now free!")

if __name__ == "__main__":
    main()