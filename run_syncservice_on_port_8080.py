"""
SyncService launcher script for port 8080.

This script runs the SyncService on port 8080 to avoid port conflicts
with the main Flask application on port 5000.
"""
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Run the SyncService on port 8080.
    """
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Path to the SyncService directory
        syncservice_dir = os.path.join(current_dir, "apps", "backend", "syncservice")
        
        # Check if the directory exists
        if not os.path.exists(syncservice_dir):
            logger.error(f"SyncService directory not found: {syncservice_dir}")
            return False
        
        # Command to run the SyncService
        cmd = [
            sys.executable, "-m", "uvicorn",
            "syncservice.main:app",
            "--host", "0.0.0.0",
            "--port", "8080"
        ]
        
        # Run the command
        logger.info(f"Starting SyncService on port 8080...")
        logger.info(f"Command: {' '.join(cmd)}")
        
        # Change to the SyncService directory
        os.chdir(syncservice_dir)
        
        # Execute the command
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor the process output
        for line in iter(process.stdout.readline, ""):
            print(line, end="")
            sys.stdout.flush()
        
        # If we reach here, the process has exited
        return_code = process.wait()
        logger.info(f"SyncService process exited with code {return_code}")
        
        # Print any error messages
        stderr = process.stderr.read()
        if stderr:
            logger.error(f"SyncService errors: {stderr}")
        
        return return_code == 0
        
    except Exception as e:
        logger.error(f"Error running SyncService: {str(e)}")
        return False

if __name__ == "__main__":
    main()