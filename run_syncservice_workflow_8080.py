"""
TerraFusion SyncService - FastAPI Application Launcher

This script runs the TerraFusion SyncService FastAPI application on port 8080.
It is designed to be used with the Replit workflow system.
"""

import sys
import logging
import uvicorn
import os
import signal
import time
import traceback

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

def handle_sigterm(sig, frame):
    """Handle SIGTERM signal gracefully."""
    logger.info("Received SIGTERM. Shutting down gracefully...")
    sys.exit(0)

def main():
    """
    Run the TerraFusion SyncService on port 8080.
    """
    logger.info("Starting SyncService on port 8080...")
    
    # Register signal handler
    signal.signal(signal.SIGTERM, handle_sigterm)
    
    # Print basic debug info
    logger.info(f"Python: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Wait a moment to ensure port 8080 is free
    time.sleep(2)
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"SyncService startup attempt {attempt}/{max_retries}")
            
            # Start uvicorn server
            uvicorn.run(
                "terrafusion_sync.app:app",
                host="0.0.0.0",
                port=8080,
                reload=True,
                log_level="info"
            )
            
            # If we reach here, the server exited cleanly
            logger.info("SyncService exited cleanly")
            return
            
        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt. Exiting...")
            return
            
        except Exception as e:
            logger.error(f"Failed to start SyncService (attempt {attempt}/{max_retries}): {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try again after a delay if we have more attempts
            if attempt < max_retries:
                logger.info(f"Retrying in 3 seconds...")
                time.sleep(3)
            else:
                logger.error("All retry attempts failed")
                sys.exit(1)

if __name__ == "__main__":
    main()