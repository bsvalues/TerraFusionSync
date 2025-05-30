"""
This script starts the WebSocket server for real-time sync operation updates.
"""

import argparse
import asyncio
import logging
import os
import signal
import sys

from logging_config import configure_logger
from syncservice_websocket import start_websocket_server

# Configure logger
logger = configure_logger("websocket_launcher")

async def main():
    """
    Main function to start the WebSocket server.
    """
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_event_loop()
    
    # Start the WebSocket server
    app, runner, update_checker = await start_websocket_server()
    
    # Log server start
    port = int(os.environ.get('WEBSOCKET_PORT', 8081))
    logger.info(f"WebSocket server running on port {port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Handle termination signals
    def handle_sigterm():
        logger.info("Received termination signal, shutting down...")
        update_checker.cancel()
        loop.create_task(runner.cleanup())
        loop.stop()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_sigterm)
    
    try:
        # Run until interrupted
        await asyncio.Event().wait()
    finally:
        # Clean up resources
        await runner.cleanup()
        update_checker.cancel()
        logger.info("WebSocket server has been shut down")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the WebSocket server for sync updates")
    parser.add_argument("--port", type=int, default=8081, help="Port to run the WebSocket server on")
    args = parser.parse_args()
    
    # Set port in environment
    os.environ['WEBSOCKET_PORT'] = str(args.port)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running WebSocket server: {e}")
        sys.exit(1)