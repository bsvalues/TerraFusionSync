"""
Runner script for the SyncService workflow.

This script starts the SyncService FastAPI application on port 8000.
"""

import os
import sys
import uvicorn

# Set the port to 8000
PORT = 8000
os.environ["SYNC_SERVICE_PORT"] = str(PORT)

def main():
    """
    Main entry point for the SyncService workflow.
    """
    print(f"Starting SyncService workflow on port {PORT}...")
    
    try:
        # Get the absolute path to the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add the current directory to Python path
        sys.path.insert(0, current_dir)
        
        # Start the FastAPI application
        uvicorn.run(
            "apps.backend.syncservice.syncservice.main:app",
            host="0.0.0.0",
            port=PORT,
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        print(f"Error starting SyncService workflow: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()