"""
Utility script to fix the SyncService workflow port.

This script changes the SyncService workflow to use port 8080 instead of 5000
to avoid conflicts with the main application.
"""
import os
import sys
import shutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Create a new workflow configuration file for the SyncService with port 8080.
    """
    try:
        # Create a new file with the right command
        with open(".replit.syncservice", "w") as f:
            f.write("""modules = ["python-3.11"]

[nix]
channel = "stable-24_05"
packages = ["libxcrypt", "libyaml", "nats-server", "openssl", "postgresql", "unixODBC"]

[deployment]
deploymentTarget = "autoscale"
run = ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]

[workflows]
runButton = "Project"

[[workflows.workflow]]
name = "Project"
mode = "parallel"
author = "agent"

[[workflows.workflow.tasks]]
task = "workflow.run"
args = "Start application"

[[workflows.workflow.tasks]]
task = "workflow.run"
args = "syncservice"

[[workflows.workflow]]
name = "Start application"
author = "agent"

[workflows.workflow.metadata]
agentRequireRestartOnSave = false

[[workflows.workflow.tasks]]
task = "packager.installForAll"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"
waitForPort = 5000

[[workflows.workflow]]
name = "syncservice"
author = "agent"

[workflows.workflow.metadata]
agentRequireRestartOnSave = false

[[workflows.workflow.tasks]]
task = "packager.installForAll"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "python run_syncservice_workflow_8080.py"
waitForPort = 8080

[[ports]]
localPort = 5000
externalPort = 80

[[ports]]
localPort = 8080
externalPort = 8080
""")
        
        # Backup the original .replit file
        shutil.copy(".replit", ".replit.backup")
        
        # Replace the .replit file with our new version
        shutil.copy(".replit.syncservice", ".replit")
        
        logger.info("Successfully updated .replit file to use port 8080 for SyncService")
        return True
        
    except Exception as e:
        logger.error(f"Error updating .replit file: {str(e)}")
        return False

if __name__ == "__main__":
    main()