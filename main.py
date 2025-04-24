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

2. SyncService (FastAPI, port 8080):
   - Core business logic for synchronization
   - Implements change detection, transformation, validation
   - Provides detailed metrics and monitoring
   - Self-healing capabilities for failed syncs
   - Handles direct database interactions

Communication Flow:
-----------------
Client -> API Gateway (port 5000) -> SyncService (port 8080) -> External Systems

Port Configuration:
-----------------
- The main Flask application MUST run on port 5000
- The SyncService MUST run on port 8080 to avoid conflicts

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

# URL of the SyncService API - using port 8080
SYNCSERVICE_URL = "http://localhost:8080"
print(f"SyncService URL: {SYNCSERVICE_URL}")

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
            
            # Path to the run_syncservice_direct script that explicitly uses port 8080
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
        print(f"Checking SyncService status at {SYNCSERVICE_URL}...")
        # Try the root endpoint first
        resp = requests.get(f"{SYNCSERVICE_URL}/", timeout=5)
        print(f"SyncService root endpoint response: {resp.status_code}")
        if resp.status_code in [200, 404]:  # 404 is ok too, it means the service is running
            print("SyncService is running (/ endpoint accessible)")
            return True
            
        # Try the /api/health endpoint as fallback
        resp = requests.get(f"{SYNCSERVICE_URL}/api/health", timeout=5)
        print(f"SyncService /api/health response: {resp.status_code}")
        if resp.status_code in [200, 404]:  # 404 is ok too, it means the service is running
            print("SyncService is running (/api/health endpoint accessible)")
            return True
            
        return False
    except requests.exceptions.RequestException as e:
        print(f"SyncService connection error: {str(e)}")
        return False

# Start SyncService in a separate thread if auto-start is enabled
if AUTO_START_SYNCSERVICE:
    threading.Thread(target=ensure_syncservice_running).start()

@app.route('/')
def root():
    """
    Root endpoint providing information about the API.
    """
    html = """
    <!DOCTYPE html>
    <html lang="en" data-bs-theme="dark">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TerraFusion SyncService</title>
        <link rel="stylesheet" href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
        <style>
            .card-feature {
                transition: all 0.2s ease;
                height: 100%;
            }
            .card-feature:hover {
                transform: translateY(-5px);
                box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
            }
            .feature-icon {
                font-size: 2rem;
                margin-bottom: 1rem;
            }
        </style>
    </head>
    <body>
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-4 mb-3">TerraFusion SyncService</h1>
                <p class="lead mb-4">Enterprise-grade data synchronization and migration platform</p>
                <div class="d-flex justify-content-center">
                    <span class="badge bg-success me-2">
                        <i class="bi bi-check-circle-fill"></i> Service Active
                    </span>
                    <span class="badge bg-info">
                        <i class="bi bi-code-slash"></i> Version 1.0.0
                    </span>
                </div>
            </div>
            
            <div class="row mb-5">
                <div class="col-md-4 mb-4">
                    <div class="card card-feature">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon text-primary">
                                <i class="bi bi-speedometer2"></i>
                            </div>
                            <h3>Dashboard</h3>
                            <p class="text-muted">Monitor sync status and system metrics</p>
                            <a href="/dashboard.html" class="btn btn-primary mt-2">
                                Open Dashboard
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card card-feature">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon text-success">
                                <i class="bi bi-arrow-repeat"></i>
                            </div>
                            <h3>Sync Operations</h3>
                            <p class="text-muted">Manage and monitor sync operations</p>
                            <a href="/sync.html" class="btn btn-success mt-2">
                                View Operations
                            </a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="card card-feature">
                        <div class="card-body text-center p-4">
                            <div class="feature-icon text-info">
                                <i class="bi bi-diagram-3"></i>
                            </div>
                            <h3>Compatibility Matrix</h3>
                            <p class="text-muted">Configure system compatibility settings</p>
                            <a href="/compatibility.html" class="btn btn-info mt-2">
                                Configure
                            </a>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="mb-0">API Documentation</h5>
                        </div>
                        <div class="card-body">
                            <p>Access the API documentation to learn about available endpoints and how to use them.</p>
                            <a href="/api-docs" class="btn btn-outline-primary">View Documentation</a>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-4">
                    <div class="card h-100">
                        <div class="card-header">
                            <h5 class="mb-0">Service Status</h5>
                        </div>
                        <div class="card-body">
                            <p>Check the current status of the SyncService and view system health information.</p>
                            <a href="/status" class="btn btn-outline-secondary">Check Status</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <footer class="bg-dark text-light py-3">
            <div class="container">
                <div class="row">
                    <div class="col-md-6">
                        <p class="mb-0">&copy; 2025 TerraFusion SyncService</p>
                    </div>
                    <div class="col-md-6 text-md-end">
                        <p class="mb-0">Version 1.0.0</p>
                    </div>
                </div>
            </div>
        </footer>
    </body>
    </html>
    """
    return Response(html, content_type='text/html')

@app.route('/dashboard')
def dashboard():
    """
    Redirect to the SyncService dashboard UI.
    """
    return proxy('dashboard.html')

@app.route('/dashboard.html')
def dashboard_html():
    """
    Display the main dashboard page.
    """
    return proxy('dashboard.html')

@app.route('/sync.html')
def sync_dashboard():
    """
    Display the sync operations dashboard.
    """
    return proxy('sync.html')

@app.route('/metrics.html')
def metrics_dashboard():
    """
    Display the metrics dashboard.
    """
    return proxy('metrics.html')

@app.route('/compatibility.html')
def compatibility_dashboard():
    """
    Display the compatibility matrix dashboard.
    """
    return proxy('compatibility.html')

@app.route('/api-docs')
def api_docs():
    """
    Redirect to the SyncService API documentation.
    """
    return proxy('api-docs')

@app.route('/static/<path:path>')
def serve_static(path):
    """
    Serve static files from the SyncService.
    """
    return proxy(f"static/{path}")

@app.route('/js/<path:path>')
def serve_js(path):
    """
    Serve JavaScript files from the SyncService.
    """
    return proxy(f"static/js/{path}")

@app.route('/css/<path:path>')
def serve_css(path):
    """
    Serve CSS files from the SyncService.
    """
    return proxy(f"static/css/{path}")

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
    # Check if the SyncService API is running using the same method as check_syncservice_status
    syncservice_status = "running" if check_syncservice_status() else "not running"
    
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