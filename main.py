"""
Main entry point for the TerraFusion SyncService API Gateway.

Architecture Overview:
---------------------
This system uses a two-tier microservice architecture:

1. API Gateway (Flask, port 5000):
   - Main entry point for all client requests
   - Handles authentication and routing
   - Proxies API requests to the SyncService
   - Provides auto-recovery of the SyncService if it stops
   - Status monitoring and management endpoints

2. SyncService (FastAPI, port 8000):
   - Core business logic for synchronization
   - Implements change detection, transformation, validation
   - Provides detailed metrics and monitoring
   - Self-healing capabilities for failed syncs
   - Handles direct database interactions

Communication Flow:
-----------------
Client -> API Gateway (port 5000) -> SyncService (port 8000) -> External Systems

Port Configuration:
-----------------
- The main Flask application MUST run on port 5000
- The SyncService MUST run on port 8000 to avoid conflicts

This separation allows independent scaling, updating, and management of each component
while maintaining a unified API surface for clients.
"""

import os
import sys
import subprocess
import threading
import time
from flask import Flask, request, Response, jsonify
import requests

# Create a simple Flask app
app = Flask(__name__)

# URL of the SyncService API - always use port 8000
SYNCSERVICE_URL = "http://localhost:8000"

# Flag to control automatic startup
AUTO_START_SYNCSERVICE = True

def ensure_syncservice_running():
    """
    Ensure that the SyncService is running.
    If not, attempt to start it in the background.
    """
    if not check_syncservice_status():
        print("SyncService not detected. Attempting to start it...")
        try:
            # Get the directory containing this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Path to the run_syncservice_direct script that explicitly uses port 8000
            runner_script = os.path.join(current_dir, "run_syncservice_direct.py")
            
            if os.path.exists(runner_script):
                # Start the SyncService in a separate process
                process = subprocess.Popen(
                    ["python", runner_script],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                print(f"Started SyncService (PID: {process.pid})")
                
                # Wait for it to start
                time.sleep(3)
                
                if check_syncservice_status():
                    print("SyncService started successfully!")
                else:
                    print("SyncService failed to start.")
            else:
                print(f"Error: Runner script not found at {runner_script}")
        except Exception as e:
            print(f"Error starting SyncService: {e}")

def check_syncservice_status():
    """
    Check if the SyncService is running.
    
    Returns:
        bool: True if the SyncService is running, False otherwise.
    """
    try:
        resp = requests.get(f"{SYNCSERVICE_URL}/", timeout=2)
        return resp.status_code == 200
    except requests.exceptions.RequestException:
        return False

# Start SyncService in a separate thread if auto-start is enabled
if AUTO_START_SYNCSERVICE:
    threading.Thread(target=ensure_syncservice_running).start()

@app.route('/')
def root():
    """
    Root endpoint providing information about the API.
    """
    return jsonify({
        "service": "TerraFusion SyncService - Gateway",
        "version": "0.1.0",
        "status": "running",
        "description": "This is a gateway to the SyncService API. Access API endpoints at /api/",
        "links": {
            "dashboard": "/dashboard",
            "api_docs": "/api-docs",
            "api_status": "/status", 
            "start_service": "/start-syncservice"
        }
    })

@app.route('/dashboard')
def dashboard():
    """
    Redirect to the SyncService dashboard UI.
    """
    return proxy('dashboard-ui')

@app.route('/api-docs')
def api_docs():
    """
    Redirect to the SyncService API documentation.
    """
    return proxy('api-docs')

@app.route('/api', defaults={'path': ''})
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    """
    Proxy all requests to the SyncService FastAPI application running on syncservice workflow.
    """
    target_url = f"{SYNCSERVICE_URL}/{path}"
    
    # Forward the request headers and data
    headers = {key: value for key, value in request.headers.items() if key != 'Host'}
    
    try:
        # Make the request to the target API
        if request.method == 'GET':
            resp = requests.get(target_url, headers=headers, params=request.args, timeout=10)
        elif request.method == 'POST':
            resp = requests.post(target_url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == 'PUT':
            resp = requests.put(target_url, headers=headers, json=request.get_json(), timeout=10)
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, timeout=10)
        elif request.method == 'OPTIONS':
            resp = requests.options(target_url, headers=headers, timeout=10)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Check if the response has content
        if resp.status_code == 200:
            # Handle HTML responses differently (don't try to parse as JSON)
            content_type = resp.headers.get('Content-Type', '')
            if 'text/html' in content_type:
                return Response(resp.content, content_type=content_type)
            
            # Try to parse as JSON, but fall back to returning content directly
            try:
                return jsonify(resp.json()), resp.status_code
            except:
                return Response(resp.content, content_type=content_type)
        
        # For non-200 responses, try to parse as JSON but fall back to returning content directly
        try:
            return jsonify(resp.json()), resp.status_code
        except:
            return Response(resp.content), resp.status_code
    except requests.exceptions.ConnectionError:
        # Try to start the SyncService if it's not running
        if AUTO_START_SYNCSERVICE:
            ensure_syncservice_running()
            
        return jsonify({
            "error": "Failed to connect to SyncService API",
            "message": "The SyncService API is not currently running. An attempt was made to start it automatically."
        }), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def status():
    """
    Status endpoint providing information about the API gateway.
    """
    # Check if the SyncService API is running
    try:
        resp = requests.get(f"{SYNCSERVICE_URL}/", timeout=2)
        syncservice_status = "running" if resp.status_code == 200 else "error"
    except requests.exceptions.RequestException:
        syncservice_status = "not running"
        
        # Try to start the SyncService if it's not running
        if AUTO_START_SYNCSERVICE and syncservice_status == "not running":
            threading.Thread(target=ensure_syncservice_running).start()
    
    return jsonify({
        "gateway": {
            "status": "running",
            "service": "terrafusion-sync-service-gateway",
            "version": "0.1.0"
        },
        "syncservice": {
            "status": syncservice_status,
            "url": SYNCSERVICE_URL
        }
    })

@app.route('/start-syncservice')
def start_syncservice():
    """
    Endpoint to manually start the SyncService if it's not running.
    """
    if check_syncservice_status():
        return jsonify({
            "status": "already running",
            "message": "SyncService is already running."
        })
    
    # Start the SyncService in a separate thread
    threading.Thread(target=ensure_syncservice_running).start()
    
    # Wait a moment for it to start
    time.sleep(3)
    
    # Check if it started successfully
    if check_syncservice_status():
        return jsonify({
            "status": "started",
            "message": "SyncService started successfully."
        })
    else:
        return jsonify({
            "status": "error",
            "message": "Failed to start SyncService. Check the logs for details."
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)