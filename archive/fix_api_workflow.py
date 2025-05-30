#!/usr/bin/env python3
"""
Fix API Gateway workflow issues.

This script checks if the API Gateway is already running and properly
configures the workflow to avoid port conflicts.
"""
import subprocess
import logging
import time
import sys
import requests
import signal
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

def check_api_gateway_status():
    """Check if the API Gateway is running."""
    try:
        response = requests.get("http://localhost:5000/api/status", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False

def main():
    """Fix the API Gateway workflow."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Checking API Gateway status...")
    
    # Check if API Gateway is already running
    if check_api_gateway_status():
        logger.info("API Gateway is already running, no need to start it")
        
        # Create a simple loop to keep the workflow "running" without actually starting another instance
        logger.info("Starting monitor loop for existing API Gateway")
        try:
            while True:
                if not check_api_gateway_status():
                    logger.warning("API Gateway is no longer responding! Starting it...")
                    # Start the API Gateway
                    cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "--timeout", "120", "main:app"]
                    logger.info(f"Starting API Gateway with command: {' '.join(cmd)}")
                    process = subprocess.Popen(cmd)
                    logger.info(f"API Gateway started with PID {process.pid}")
                    
                    # Wait for process to exit
                    process.wait()
                    logger.warning("API Gateway process exited")
                    
                time.sleep(30)  # Check every 30 seconds
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            return 0
    else:
        # API Gateway is not running, start it
        logger.info("API Gateway is not running, starting it...")
        
        # Start the API Gateway
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reload", "--timeout", "120", "main:app"]
        logger.info(f"Starting API Gateway with command: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)
        logger.info(f"API Gateway started with PID {process.pid}")
        
        # Wait for process to exit
        try:
            process.wait()
            logger.warning("API Gateway process exited")
            return process.returncode
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            process.kill()
            return 0

if __name__ == "__main__":
    sys.exit(main())