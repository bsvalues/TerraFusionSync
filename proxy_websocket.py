"""
WebSocket proxy for the API Gateway.

This module adds WebSocket proxy functionality to the Flask API Gateway,
enabling forwarding of WebSocket connections to the WebSocket server.
"""

import logging
import os
import subprocess
import threading
import time
from flask import Blueprint, request, current_app, Response
from werkzeug.wsgi import get_input_stream
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Blueprint for the WebSocket proxy
websocket_bp = Blueprint('websocket', __name__)

# WebSocket server settings
WEBSOCKET_SERVER_URL = "http://0.0.0.0:8081"

def ensure_websocket_server_running():
    """
    Check if the WebSocket server is running and start it if not.
    
    Returns:
        bool: True if the WebSocket server is running or was started successfully
    """
    # Check if the WebSocket server is already running
    try:
        response = requests.get(f"{WEBSOCKET_SERVER_URL}/health", timeout=2)
        if response.status_code == 200:
            logger.info("WebSocket server is already running")
            return True
    except requests.RequestException:
        logger.warning("WebSocket server is not running, attempting to start it")
    
    # Start the WebSocket server in a separate process
    try:
        websocket_process = subprocess.Popen(
            ["python", "run_websocket_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait a moment for the server to start
        time.sleep(2)
        
        # Check if the server started successfully
        try:
            response = requests.get(f"{WEBSOCKET_SERVER_URL}/health", timeout=2)
            if response.status_code == 200:
                logger.info("WebSocket server started successfully")
                return True
            else:
                logger.error(f"WebSocket server health check failed: {response.status_code}")
                return False
        except requests.RequestException:
            logger.error("Failed to connect to WebSocket server after starting")
            return False
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {e}")
        return False

@websocket_bp.route('/ws/<path:path>')
def proxy_websocket(path):
    """
    Proxy WebSocket connections to the WebSocket server.
    
    This function forwards WebSocket upgrade requests to the WebSocket server
    and streams the response back to the client.
    
    Args:
        path: The path to forward to the WebSocket server
        
    Returns:
        Flask Response object with the proxied WebSocket response
    """
    # Ensure the WebSocket server is running
    if not ensure_websocket_server_running():
        return Response("WebSocket server is not available", status=503)
    
    # Construct the target URL
    target_url = f"{WEBSOCKET_SERVER_URL}/{path}"
    
    # Forward the request headers to the WebSocket server
    headers = {
        key: value for key, value in request.headers
        if key.lower() not in ['host', 'content-length']
    }
    
    try:
        # Make a streaming request to the WebSocket server
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=get_input_stream(request.environ),
            stream=True,
            timeout=60
        )
        
        # Create a Flask Response with streaming content from the WebSocket server
        proxy_response = Response(
            response=response.iter_content(chunk_size=1024),
            status=response.status_code,
            content_type=response.headers.get('content-type')
        )
        
        # Copy headers from the WebSocket server response
        for key, value in response.headers.items():
            if key.lower() not in ['content-length', 'connection', 'transfer-encoding']:
                proxy_response.headers[key] = value
        
        return proxy_response
    except Exception as e:
        logger.error(f"Error proxying WebSocket request: {e}")
        return Response(f"Error proxying WebSocket request: {str(e)}", status=500)

# Function to register the blueprint with a Flask app
def register_websocket_proxy(app):
    """
    Register the WebSocket proxy blueprint with a Flask app.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(websocket_bp)
    logger.info("Registered WebSocket proxy blueprint")
    
    # Initialize the WebSocket server
    threading.Thread(target=ensure_websocket_server_running, daemon=True).start()