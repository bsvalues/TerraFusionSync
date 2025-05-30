#!/usr/bin/env python3
"""
TerraFusion SyncService - Market Analysis API Runner

This script launches the simplified Market Analysis API on port 8080.
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

def run_api():
    """Run the simplified Market Analysis API."""
    logger.info("Starting Market Analysis API...")
    
    # Use the current Python executable
    python_exe = sys.executable
    
    # Environment variables for the subprocess
    env = os.environ.copy()
    env["PORT"] = "8080"
    
    try:
        # Start the process
        proc = subprocess.Popen(
            [python_exe, "simplified_market_analysis_api.py"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Handle graceful shutdown
        def shutdown_handler(signum, frame):
            logger.info("Received signal. Shutting down gracefully...")
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
        
        # Log output in real-time
        while True:
            stdout_line = proc.stdout.readline() if proc.stdout else ""
            stderr_line = proc.stderr.readline() if proc.stderr else ""
            
            if stdout_line:
                logger.info(stdout_line.strip())
            if stderr_line:
                logger.error(stderr_line.strip())
                
            # Check if process is still running
            if proc.poll() is not None:
                # Process has terminated
                logger.info(f"Process exited with code {proc.returncode}")
                remaining_stdout, remaining_stderr = proc.communicate()
                
                if remaining_stdout:
                    logger.info(remaining_stdout.strip())
                if remaining_stderr:
                    logger.error(remaining_stderr.strip())
                    
                break
                
            # Small sleep to prevent CPU thrashing
            time.sleep(0.1)
            
    except Exception as e:
        logger.error(f"Error starting API: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_api()