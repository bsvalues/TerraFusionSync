"""
Workflow runner for SyncService on port 8080.

This script is used by the Replit workflow to start the SyncService on port 8080
to avoid conflicts with the main application on port 5000.
"""
import os
import sys
import logging
import signal
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

def main():
    """
    Run the SyncService on port 8080 for the workflow.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Set environment variable to run in development mode with no auth
        os.environ["SYNCSERVICE_DEV_MODE"] = "1"
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the SyncService directory
        syncservice_dir = os.path.join(current_dir, "apps", "backend", "syncservice")
        
        # Change to the SyncService directory
        os.chdir(syncservice_dir)
        
        # Command to run uvicorn
        cmd = [
            sys.executable, "-m", "uvicorn",
            "syncservice.main:app",
            "--host", "0.0.0.0",
            "--port", "8080",
            "--reload"
        ]
        
        logger.info(f"Starting SyncService on port 8080...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Execute the command and wait for it to complete
        process = subprocess.run(cmd)
        
        return process.returncode == 0
        
    except Exception as e:
        logger.error(f"Error starting SyncService: {str(e)}")
        return False

if __name__ == "__main__":
    main()