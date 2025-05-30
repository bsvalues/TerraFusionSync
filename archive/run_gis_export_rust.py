#!/usr/bin/env python3
"""
TerraFusion GIS Export Service - Rust Implementation Launcher

This script starts the Rust-based GIS Export service on port 8080
for the TerraFusion workflow.
"""

import os
import sys
import time
import signal
import subprocess
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
PORT = 8080
MAX_HEALTH_CHECK_ATTEMPTS = 5
HEALTH_CHECK_INTERVAL = 2  # seconds


def get_python_executable():
    """Get the path to the Python executable."""
    return sys.executable


def run_rust_gis_export():
    """Run the Rust-based GIS Export service on port 8080."""
    python_exe = get_python_executable()
    logger.info(f"Starting Rust GIS Export Service on port {PORT}...")
    logger.info(f"Python: {python_exe}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Define environment variables for the subprocess
    env = os.environ.copy()
    env["PORT"] = str(PORT)
    
    # Build the command to run the Rust bridge
    cmd = [python_exe, "terrarust_bridge.py", "run_gis_export"]
    
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
        
        # Check if the service is healthy
        service_healthy = False
        for attempt in range(MAX_HEALTH_CHECK_ATTEMPTS):
            try:
                logger.info(f"Health check attempt {attempt + 1}/{MAX_HEALTH_CHECK_ATTEMPTS}...")
                response = requests.get(f"http://localhost:{PORT}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("GIS Export service is healthy!")
                    service_healthy = True
                    break
                else:
                    logger.warning(f"Health check failed with status code: {response.status_code}")
            except requests.RequestException as e:
                logger.warning(f"Health check failed: {e}")
            
            time.sleep(HEALTH_CHECK_INTERVAL)
        
        if not service_healthy:
            logger.error("GIS Export service failed health checks")
            # Continue anyway, as the service might become healthy later
        
        # Wait for the process to complete
        proc.wait()
        
        # Check if process exited with error
        if proc.returncode != 0:
            logger.error(f"GIS Export service exited with code {proc.returncode}")
            stderr = proc.stderr.read() if proc.stderr else ""
            logger.error(f"Error output: {stderr}")
            sys.exit(1)
        else:
            # Process exited normally
            logger.info("GIS Export service has stopped")
            
    except Exception as e:
        logger.error(f"Error running GIS Export service: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_rust_gis_export()