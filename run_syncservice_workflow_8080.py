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
    
    # Build the command for uvicorn
    command = f"{sys.executable} -m uvicorn terrafusion_sync.app:app --host 0.0.0.0 --port 8080 --reload"
    
    logger.info(f"Command: {command}")
    
    try:
        # Start uvicorn server
        uvicorn.run(
            "terrafusion_sync.app:app",
            host="0.0.0.0",
            port=8080,
            reload=True,
            log_level="debug"
        )
    except Exception as e:
        logger.error(f"Failed to start SyncService: {str(e)}")
        # Print exception traceback
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()