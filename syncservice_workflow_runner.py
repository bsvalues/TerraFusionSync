"""
Workflow runner for the SyncService.

This script starts the SyncService as a separate workflow process.
"""

import os
import sys
import uvicorn

# Set environment variables
os.environ["SYNC_SERVICE_PORT"] = "8000"

def main():
    """
    Main entry point for the SyncService workflow.
    """
    print("Starting SyncService workflow...")
    
    try:
        # Get the absolute path to the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Add the current directory to Python path
        sys.path.insert(0, current_dir)
        
        # Start uvicorn server
        uvicorn.run(
            "apps.backend.syncservice.syncservice.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info"
        )
        
    except Exception as e:
        print(f"Error starting SyncService workflow: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()