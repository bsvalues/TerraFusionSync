"""
Run script for the SyncService workflow.

This script is designed to run the SyncService on port 8000 to avoid conflicts.
"""

import os
import sys
import socket
import uvicorn

# Check if port 5000 is in use and fall back to port 8000
def get_available_port():
    # First check if port 8000 is available (preferred)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 8000))
        s.close()
        return 8000
    except socket.error:
        # If port 8000 is not available, try port 8080
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', 8080))
            s.close()
            return 8080
        except socket.error:
            # If port 8080 is not available, default to port 8000 (let it fail if needed)
            return 8000

# Main entry point
if __name__ == "__main__":
    # Get the available port to use
    port = get_available_port()
    
    print(f"Starting SyncService on port {port}")
    print(f"Current directory: {os.getcwd()}")
    
    # Add the applications directory to sys.path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())
    
    # Start the server
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )