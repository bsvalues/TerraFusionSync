"""
Main entry point for the SyncService API.

This module creates a Flask application that serves as a wrapper for the SyncService FastAPI application.
"""

import os
import sys
from flask import Flask, request, Response
import requests

# Create a simple Flask app
app = Flask(__name__)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    """
    Proxy all requests to the SyncService FastAPI application running on syncservice workflow.
    """
    return "TerraFusion SyncService - Please access the API through the syncservice workflow directly."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)