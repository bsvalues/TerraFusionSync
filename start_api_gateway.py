"""
Script to start the API Gateway and WebSocket server, handling any port conflicts.

This script:
1. Checks if port 5000 is already in use
2. If it is, identifies the process and terminates it
3. Starts the WebSocket server in the background (if not already running)
4. Starts the API Gateway with gunicorn
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
logger = logging.getLogger("api_gateway_launcher")

def find_process_using_port(port):
    """Find the process using a specific port."""
    try:
        for conn in psutil.net_connections(kind='inet'):
            if conn.laddr.port == port and conn.status == 'LISTEN':
                return conn.pid
        return None
    except Exception as e:
        logger.error(f"Error finding process on port {port}: {e}")
        return None

def terminate_process(pid):
    """Safely terminate a process."""
    try:
        process = psutil.Process(pid)
        logger.info(f"Terminating process {pid} ({process.name()})")
        
        # Try SIGTERM first
        process.terminate()
        gone, alive = psutil.wait_procs([process], timeout=3)
        
        if alive:
            # If still alive, use SIGKILL
            logger.warning(f"Process {pid} did not terminate gracefully, using SIGKILL")
            for p in alive:
                p.kill()
                
        logger.info(f"Process {pid} terminated")
        return True
    except Exception as e:
        logger.error(f"Error terminating process {pid}: {e}")
        return False

def check_websocket_server():
    """Check if the WebSocket server is running."""
    # Check if port 8081 is in use
    pid = find_process_using_port(8081)
    if pid:
        logger.info(f"WebSocket server is already running on port 8081 (PID: {pid})")
        return True
    return False

def start_websocket_server():
    """Start the WebSocket server in the background."""
    logger.info("Starting WebSocket server")
    try:
        # Launch the WebSocket server as a subprocess
        websocket_process = subprocess.Popen(
            ["python", "run_websocket_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        time.sleep(2)
        
        # Check if it's running
        if check_websocket_server():
            logger.info("WebSocket server started successfully")
            return True
        else:
            logger.warning("WebSocket server did not start properly")
            return False
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {e}")
        return False

def main():
    """Main entry point for the script."""
    logger.info("Starting API Gateway launcher")
    
    # Check if port 5000 is in use
    pid = find_process_using_port(5000)
    if pid:
        logger.warning(f"Port 5000 already in use by process {pid}")
        
        # Terminate the process
        if terminate_process(pid):
            logger.info("Successfully terminated the process using port 5000")
        else:
            logger.error("Failed to terminate the process, please resolve manually")
            sys.exit(1)
            
        # Give it a moment for the port to be released
        time.sleep(2)
    
    # Check if WebSocket server is running, if not, start it
    if not check_websocket_server():
        logger.info("WebSocket server is not running")
        if not start_websocket_server():
            logger.warning("Could not start WebSocket server, continuing without it")
    
    # Start the API Gateway with gunicorn
    try:
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
        logger.info(f"Starting API Gateway with command: {' '.join(cmd)}")
        
        # Execute gunicorn directly (this will replace the current process)
        os.execvp("gunicorn", cmd)
    except Exception as e:
        logger.error(f"Failed to start API Gateway: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()