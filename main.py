"""
TerraFusion SyncService - Main Application Entry Point

This module serves as the main entry point for the Flask API Gateway.
"""

from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)