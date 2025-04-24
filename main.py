"""
Main entry point for the SyncService API.

This module creates a Flask application that serves as a wrapper for the SyncService FastAPI application.
"""

import os
import sys
from flask import Flask, request, Response, jsonify
import requests

# Create a simple Flask app
app = Flask(__name__)

# URL of the SyncService API
SYNCSERVICE_URL = "http://localhost:8000"

@app.route('/')
def root():
    """
    Root endpoint providing information about the API.
    """
    return jsonify({
        "service": "TerraFusion SyncService - Gateway",
        "version": "0.1.0",
        "status": "running",
        "description": "This is a gateway to the SyncService API. Access API endpoints at /api/"
    })

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
            resp = requests.get(target_url, headers=headers, params=request.args)
        elif request.method == 'POST':
            resp = requests.post(target_url, headers=headers, json=request.get_json())
        elif request.method == 'PUT':
            resp = requests.put(target_url, headers=headers, json=request.get_json())
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers)
        elif request.method == 'OPTIONS':
            resp = requests.options(target_url, headers=headers)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Return the response from the target API
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({
            "error": "Failed to connect to SyncService API",
            "message": "The SyncService API is not currently running. Please start the 'syncservice' workflow."
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
        resp = requests.get(f"{SYNCSERVICE_URL}/health/live")
        syncservice_status = "running" if resp.status_code == 200 else "error"
    except requests.exceptions.ConnectionError:
        syncservice_status = "not running"
    
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)