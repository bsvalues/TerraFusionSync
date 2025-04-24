"""
Workflow starter script for the SyncService.

This script is a wrapper that will detect the port before running the actual application.
It's designed to intercept the workflow command and adjust it to use port 8000.
"""

import os
import sys
import re
import subprocess

# Check the command-line arguments
if len(sys.argv) > 1:
    command = " ".join(sys.argv[1:])
    
    # See if the command is running uvicorn
    if "uvicorn" in command and "--port" in command:
        # Extract the original command
        # Replace port 5000 with port 8000 if it appears in the command
        modified_command = re.sub(r'--port\s+5000', '--port 8000', command)
        
        print(f"Original command: {command}")
        print(f"Modified command: {modified_command}")
        
        # Execute the modified command
        try:
            # Run the modified command
            os.system(modified_command)
        except Exception as e:
            print(f"Error executing command: {e}")
            sys.exit(1)
    else:
        # If it's not a uvicorn command or doesn't specify port, just run it as is
        try:
            os.system(command)
        except Exception as e:
            print(f"Error executing command: {e}")
            sys.exit(1)
else:
    # If no command is provided, run the start.py script directly
    try:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        print("Running start.py...")
        os.system("python start.py")
    except Exception as e:
        print(f"Error executing start.py: {e}")
        sys.exit(1)