"""
Main entry point for the SyncService.

This module provides a standardized entry point for running the SyncService.
"""

import os
import uvicorn

# Set the port for the service
DEFAULT_PORT = 8000
port = int(os.environ.get("SYNC_SERVICE_PORT", DEFAULT_PORT))

if __name__ == "__main__":
    print(f"Starting SyncService on port {port}...")
    
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )