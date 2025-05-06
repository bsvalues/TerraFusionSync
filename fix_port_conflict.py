"""
Utility to fix port conflicts in the TerraFusion project.

This script detects and resolves port conflicts by:
1. Checking if a process is using port 5000
2. Safely terminating the process if it exists
3. Starting the API Gateway workflow
"""

import os
import subprocess
import sys
import time
import logging
import signal
import psutil

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("port_conflict_resolver")

def find_process_using_port(port):
    """
    Find the process ID using the specified port.
    
    Args:
        port: Port number to check
        
    Returns:
        Process ID or None if no process is using the port
    """
    try:
        # Use lsof command to find the process using the port
        cmd = f"lsof -i :{port} -t"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            # Return the first PID found
            return int(result.stdout.strip().split('\n')[0])
        else:
            # Try netstat as an alternative
            cmd = f"netstat -nlp | grep :{port} | awk '{{print $7}}' | cut -d/ -f1 | head -n1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip() and result.stdout.strip() != "":
                try:
                    return int(result.stdout.strip())
                except ValueError:
                    logger.warning(f"Could not parse PID from netstat: {result.stdout.strip()}")
                    return None
            
            return None
    except Exception as e:
        logger.error(f"Error finding process using port {port}: {e}")
        return None

def terminate_process(pid, force=False):
    """
    Safely terminate a process by its PID.
    
    Args:
        pid: Process ID to terminate
        force: Whether to force termination (SIGKILL)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not psutil.pid_exists(pid):
            logger.warning(f"Process {pid} doesn't exist")
            return True
            
        process = psutil.Process(pid)
        process_name = process.name()
        
        logger.info(f"Attempting to terminate process {pid} ({process_name})")
        
        # First try SIGTERM
        process.terminate()
        
        # Give it a moment to terminate gracefully
        gone, alive = psutil.wait_procs([process], timeout=3)
        
        if not alive:
            logger.info(f"Successfully terminated process {pid}")
            return True
            
        # If still alive and force is True, use SIGKILL
        if force:
            logger.warning(f"Process {pid} did not terminate gracefully, using SIGKILL")
            process.kill()
            
            gone, alive = psutil.wait_procs([process], timeout=3)
            
            if not alive:
                logger.info(f"Successfully killed process {pid}")
                return True
            else:
                logger.error(f"Failed to kill process {pid}")
                return False
        else:
            logger.warning(f"Process {pid} did not terminate gracefully")
            return False
            
    except psutil.NoSuchProcess:
        logger.warning(f"Process {pid} no longer exists")
        return True
    except psutil.AccessDenied:
        logger.error(f"Access denied when trying to terminate process {pid}")
        return False
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {e}")
        return False

def start_api_gateway():
    """
    Start the API Gateway workflow.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get current script directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Construct command to start the API Gateway
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
        
        # Start the API Gateway process
        logger.info("Starting API Gateway with command: " + " ".join(cmd))
        subprocess.Popen(cmd, cwd=script_dir)
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's running
        if find_process_using_port(5000):
            logger.info("API Gateway started successfully")
            return True
        else:
            logger.error("API Gateway failed to start")
            return False
    except Exception as e:
        logger.error(f"Error starting API Gateway: {e}")
        return False

def main():
    """
    Main entry point for the port conflict resolver.
    """
    logger.info("Starting port conflict resolution for TerraFusion API Gateway")
    
    # Check if port 5000 is in use
    pid = find_process_using_port(5000)
    
    if pid:
        logger.info(f"Port 5000 is being used by process {pid}")
        
        # Try to terminate the process
        if terminate_process(pid, force=False):
            logger.info("Successfully terminated the process using port 5000")
        else:
            logger.warning("Failed to gracefully terminate the process, trying force kill")
            
            if terminate_process(pid, force=True):
                logger.info("Successfully force killed the process using port 5000")
            else:
                logger.error("Failed to kill the process using port 5000")
                sys.exit(1)
    else:
        logger.info("No process found using port 5000")
    
    # Wait a moment to ensure the port is released
    time.sleep(2)
    
    # Start the API Gateway
    if start_api_gateway():
        logger.info("Port conflict resolution completed successfully")
    else:
        logger.error("Failed to start API Gateway after resolving port conflict")
        sys.exit(1)

if __name__ == "__main__":
    main()