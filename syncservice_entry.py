"""
Entry point for the SyncService workflow.

This module provides a standardized entry point for running the SyncService in the Replit workflow.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set the port for the service
os.environ["SYNC_SERVICE_PORT"] = "8000"

def main():
    """
    Main entry point for the SyncService workflow.
    """
    import uvicorn
    
    # Set up logging
    logger = logging.getLogger("syncservice_entry")
    logger.info("Starting SyncService on port 8000...")
    
    # Start uvicorn server
    try:
        # Get the absolute path to the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Print debug information
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Application directory: {current_dir}")
        
        # Add the application directory to Python path
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Start the application
        uvicorn.run(
            "apps.backend.syncservice.syncservice.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        logger.error(f"Error starting SyncService: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()