"""
Run SyncService Directly

This is a standalone script that runs the SyncService directly using uvicorn,
avoiding the workflow system which might have issues with port conflicts.

It features:
- Robust error handling
- Improved logging
- Automatic retries
- Automatic cleanup of zombie processes
"""

import os
import sys
import time
import signal
import logging
import socket
import subprocess
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
PORT = 8080
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def kill_process_on_port(port):
    """Attempt to kill any process using the specified port."""
    try:
        # Try using netstat to find process
        cmd = f"netstat -tuln | grep {port}"
        result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.stdout:
            logger.info(f"Found process using port {port}")
            
            # Try using fuser to kill the process
            kill_cmd = f"fuser -k {port}/tcp"
            subprocess.run(kill_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"Killed process on port {port}")
            
            # Wait for port to be released
            time.sleep(1)
            return not is_port_in_use(port)
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")
    
    return False

def setup_router_fix():
    """Apply fixes to the router.py file in market analysis plugin."""
    try:
        # Fix the router.py file
        router_path = "terrafusion_sync/plugins/market_analysis/router.py"
        if os.path.exists("fix_market_analysis_router.py"):
            subprocess.run([sys.executable, "fix_market_analysis_router.py"], check=True)
            logger.info("Successfully fixed market analysis router")
        
        # Fix the tasks.py file
        tasks_path = "terrafusion_sync/plugins/market_analysis/tasks.py"
        if os.path.exists("fix_market_analysis_background_task.py"):
            subprocess.run([sys.executable, "fix_market_analysis_background_task.py"], check=True)
            logger.info("Successfully fixed market analysis background tasks")
            
        return True
    except Exception as e:
        logger.error(f"Error fixing router files: {e}")
        return False

def run_syncservice():
    """Run the SyncService using direct uvicorn command."""
    logger.info(f"Starting SyncService on port {PORT}")
    
    # Check if port is in use and try to free it
    if is_port_in_use(PORT):
        logger.warning(f"Port {PORT} is already in use")
        if not kill_process_on_port(PORT):
            logger.warning(f"Failed to free port {PORT}, proceeding anyway")
    
    # Apply fixes to the router file
    setup_router_fix()
    
    # Build the command to run the service
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "terrafusion_sync.app:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--reload",
        "--log-level", "info"
    ]
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        # Start the process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,  # Line buffered
        )
        
        logger.info(f"Started SyncService with PID {process.pid}")
        
        # Monitor the process and capture output
        startup_success = False
        for line in process.stdout:
            print(line.rstrip())
            
            # Check for successful startup
            if "Application startup complete" in line:
                startup_success = True
                logger.info("SyncService started successfully")
            
            # If the process exits, break the loop
            if process.poll() is not None:
                break
        
        # Check if process exited prematurely
        if process.poll() is not None:
            logger.error(f"SyncService exited prematurely with code {process.returncode}")
            return False, process.returncode
        
        return startup_success, None
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
        return False, None
        
    except Exception as e:
        logger.error(f"Error running SyncService: {e}")
        logger.error(traceback.format_exc())
        return False, 1

def main():
    """Main entry point with retry logic."""
    logger.info("=== SyncService Direct Launcher ===")
    logger.info(f"Current time: {datetime.now().isoformat()}")
    logger.info(f"Python: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    # Try to run the service with retries
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(f"Attempt {attempt}/{MAX_RETRIES} to start SyncService")
        
        success, exit_code = run_syncservice()
        
        if success:
            logger.info("SyncService is running successfully")
            return 0
        
        if attempt < MAX_RETRIES:
            logger.warning(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
        else:
            logger.error("All attempts to start SyncService failed")
            return 1

if __name__ == "__main__":
    sys.exit(main())