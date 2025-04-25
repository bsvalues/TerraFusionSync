"""
Run the local standalone SyncService.

This script runs the local standalone version of the SyncService with the
updated health check endpoints.
"""
import os
import sys
import signal
import logging
import uvicorn
import asyncio
from syncservice import app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

def main():
    """Run the local SyncService."""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting local SyncService on port 8080...")
    
    # Run the application
    uvicorn.run(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()