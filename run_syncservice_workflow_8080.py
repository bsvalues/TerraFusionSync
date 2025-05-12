#!/usr/bin/env python3
"""
TerraFusion SyncService - Simplified Workflow Runner for Port 8080

This script starts a simplified Market Analysis API on port 8080 for the TerraFusion workflow.
"""

import os
import sys
import time
import signal
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PORT = 8080

def get_python_executable():
    """Get the path to the Python executable."""
    return sys.executable

def run_syncservice():
    """Run the simplified Market Analysis API on port 8080."""
    python_exe = get_python_executable()
    logger.info(f"Starting SyncService on port {PORT}...")
    logger.info(f"Python: {python_exe}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Define environment variables for the subprocess
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    
    # Build the command to run the simplified API
    cmd = [python_exe, "simplified_market_analysis_api.py"]
    
    try:
        # Start the process
        proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Handle graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info("Received SIGTERM. Shutting down gracefully...")
            if proc:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
            sys.exit(0)
        
        # Register signal handlers
        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)
        
        # Wait for the process to complete
        proc.wait()
        
        # Check if process exited with error
        if proc.returncode != 0:
            logger.error(f"SyncService exited with code {proc.returncode}")
            stderr = proc.stderr.read() if proc.stderr else ""
            logger.error(f"Error output: {stderr}")
            sys.exit(1)
        else:
            # Process exited normally
            logger.info("SyncService has stopped")
            
    except Exception as e:
        logger.error(f"Error running SyncService: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_syncservice()