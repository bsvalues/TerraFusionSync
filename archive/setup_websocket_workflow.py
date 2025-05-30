"""
Setup WebSocket workflow for TerraFusion SyncService.

This script creates a new workflow configuration for the WebSocket server.
"""

import os
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("websocket_workflow_setup")

def main():
    """Set up WebSocket workflow."""
    logger.info("Setting up WebSocket workflow")
    
    # Check if WebSocket configuration exists
    websocket_config_path = os.path.join(os.getcwd(), ".replit.websocket")
    
    if not os.path.exists(websocket_config_path):
        logger.error(f"WebSocket configuration not found at {websocket_config_path}")
        logger.info("Creating WebSocket configuration")
        
        # Create WebSocket configuration
        with open(websocket_config_path, "w") as f:
            f.write("""run = "python run_websocket_server.py"
language = "python3"

[nix]
channel = "stable-23_05"

[deployment]
run = ["sh", "-c", "python run_websocket_server.py"]
deploymentTarget = "cloudrun"
""")
        
        logger.info(f"Created WebSocket configuration at {websocket_config_path}")
    
    # Create WebSocket server launcher if it doesn't exist
    websocket_launcher_path = os.path.join(os.getcwd(), "run_websocket_server.py")
    
    if not os.path.exists(websocket_launcher_path):
        logger.error(f"WebSocket launcher not found at {websocket_launcher_path}")
        logger.info("WebSocket server launcher needs to be created")
        
        # Create WebSocket server launcher
        with open(websocket_launcher_path, "w") as f:
            f.write('''import asyncio
import logging
import os
import signal
import sys

from syncservice_websocket import start_websocket_server

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("websocket_launcher")

async def main():
    """Run the WebSocket server."""
    # Configure signal handlers
    loop = asyncio.get_event_loop()
    
    # Start the WebSocket server
    logger.info("Starting WebSocket server")
    app, runner, update_checker = await start_websocket_server()
    
    # Log the server is running
    port = int(os.environ.get("WEBSOCKET_PORT", 8081))
    logger.info(f"WebSocket server running on port {port}")
    
    # Register signal handlers
    def handle_shutdown():
        logger.info("Shutting down WebSocket server")
        update_checker.cancel()
        loop.create_task(runner.cleanup())
        loop.stop()
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_shutdown)
    
    # Run the server
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Error running WebSocket server: {e}")
        sys.exit(1)
''')
        
        logger.info(f"Created WebSocket server launcher at {websocket_launcher_path}")
    
    # Create a health check endpoint for the WebSocket server
    health_route_path = os.path.join(os.getcwd(), "syncservice_websocket_health.py")
    
    if not os.path.exists(health_route_path):
        logger.info("Creating WebSocket health check endpoint")
        
        # Create health check endpoint
        with open(health_route_path, "w") as f:
            f.write('''import logging
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """Health check endpoint for the WebSocket server."""
    return web.json_response({"status": "healthy"})

def add_health_routes(app):
    """Add health check routes to the WebSocket server."""
    app.router.add_get('/health', health_check)
    logger.info("Added health check endpoint to WebSocket server")
''')
        
        logger.info(f"Created WebSocket health check endpoint at {health_route_path}")
    
    # Update the WebSocket server to include health check
    websocket_server_path = os.path.join(os.getcwd(), "syncservice_websocket.py")
    
    if os.path.exists(websocket_server_path):
        # Read the WebSocket server file
        with open(websocket_server_path, "r") as f:
            content = f.read()
        
        # Check if health check is already imported
        if "from syncservice_websocket_health import add_health_routes" not in content:
            # Find the part where the WebSocket server is started
            if "async def start_websocket_server():" in content:
                # Insert the health check import after the imports
                import_marker = "from logging_config import configure_logger"
                new_import = (
                    "from logging_config import configure_logger\n\n"
                    "# Import health check routes\n"
                    "try:\n"
                    "    from syncservice_websocket_health import add_health_routes\n"
                    "    HEALTH_ROUTES_AVAILABLE = True\n"
                    "except ImportError:\n"
                    "    logger = logging.getLogger('syncservice_websocket')\n"
                    "    logger.warning('Health check routes not available')\n"
                    "    HEALTH_ROUTES_AVAILABLE = False"
                )
                
                content = content.replace(import_marker, new_import)
                
                # Find the part where the app is created
                app_creation_marker = "# Create the aiohttp application\n    app = web.Application()"
                
                if app_creation_marker in content:
                    # Add health check routes after app creation
                    new_app_creation = (
                        "# Create the aiohttp application\n"
                        "    app = web.Application()\n\n"
                        "    # Add health check routes if available\n"
                        "    if HEALTH_ROUTES_AVAILABLE:\n"
                        "        add_health_routes(app)"
                    )
                    
                    content = content.replace(app_creation_marker, new_app_creation)
                    
                    # Write the updated content back to the file
                    with open(websocket_server_path, "w") as f:
                        f.write(content)
                    
                    logger.info(f"Updated WebSocket server at {websocket_server_path} with health check routes")
                else:
                    logger.warning(f"Could not find app creation marker in {websocket_server_path}")
            else:
                logger.warning(f"Could not find start_websocket_server function in {websocket_server_path}")
        else:
            logger.info(f"WebSocket server at {websocket_server_path} already has health check routes")
    else:
        logger.error(f"WebSocket server not found at {websocket_server_path}")
    
    logger.info("WebSocket workflow setup complete")

if __name__ == "__main__":
    main()