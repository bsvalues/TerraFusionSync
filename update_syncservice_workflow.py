"""
Script to update the SyncService workflow configuration.

This script will manually update the .replit file to configure
the SyncService workflow to use port 8080 instead of port 5000.
"""
import os
import sys
import logging
import tomli
import tomli_w

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """
    Update the SyncService workflow in the .replit file
    """
    try:
        # Load the original .replit file
        with open(".replit", "rb") as f:
            config = tomli.load(f)
        
        # Find the syncservice workflow
        workflows = config.get("workflows", {}).get("workflow", [])
        for workflow in workflows:
            if workflow.get("name") == "syncservice":
                # Find the shell.exec task
                for task in workflow.get("tasks", []):
                    if task.get("task") == "shell.exec":
                        # Update the command to use port 8080
                        task["args"] = "python run_syncservice_workflow_8080.py"
                        
                        # If there's a waitForPort, update it to 8080
                        if "waitForPort" in task:
                            task["waitForPort"] = 8080
                            
                logger.info("Updated SyncService workflow to use port 8080")
        
        # Make sure we have the port configuration
        ports = config.get("ports", [])
        has_port_8080 = False
        for port in ports:
            if port.get("localPort") == 8080:
                has_port_8080 = True
                break
        
        if not has_port_8080:
            if "ports" not in config:
                config["ports"] = []
            
            config["ports"].append({
                "localPort": 8080,
                "externalPort": 8080
            })
            logger.info("Added port 8080 configuration")
        
        # Save the updated configuration
        with open(".replit", "wb") as f:
            tomli_w.dump(config, f)
            
        logger.info("Successfully updated .replit file")
        return True
        
    except Exception as e:
        logger.error(f"Error updating workflow configuration: {str(e)}")
        return False

if __name__ == "__main__":
    main()