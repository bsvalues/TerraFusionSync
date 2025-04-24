"""
Utility script to fix the SyncService workflow port.

This script changes the SyncService workflow to use port 8080 instead of 5000
to avoid conflicts with the main application.
"""

import os
import subprocess
import sys

def main():
    """
    Create a new workflow configuration file for the SyncService with port 8080.
    """
    print("Creating SyncService workflow configuration...")
    
    # Create workflow file content
    workflow_content = """command = ["cd apps/backend/syncservice && python -m uvicorn syncservice.main:app --host 0.0.0.0 --port 8080"]
"""
    
    # Ensure the .replit.d directory exists
    os.makedirs(".replit.d", exist_ok=True)
    
    # Write the workflow configuration file
    with open(".replit.d/syncservice.toml", "w") as f:
        f.write(workflow_content)
    
    print("SyncService workflow configuration created successfully.")
    print("Updated to use port 8080 instead of port 5000.")
    print("This change will take effect the next time the workflow is started.")
    
    # Restart SyncService workflow
    try:
        subprocess.run(["restart_syncservice_workflow.py"], capture_output=True, text=True)
        print("SyncService workflow has been requested to restart.")
    except Exception as e:
        print(f"Failed to restart SyncService workflow: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())