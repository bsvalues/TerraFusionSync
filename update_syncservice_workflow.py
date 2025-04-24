"""
Update the syncservice workflow to use port 8080.

This script modifies the .replit workflow configuration to ensure
the syncservice runs on port 8080 instead of port 5000 to avoid conflicts.
"""

import os
import sys
import logging
import subprocess

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    Create a new workflow configuration for syncservice to use port 8080.
    """
    workflow_content = """<workflow>
<name>
syncservice
</name>
<command>
cd apps/backend/syncservice && python -m uvicorn syncservice.main:app --host 0.0.0.0 --port 8080
</command>
</workflow>
"""
    
    # Check if .replit file exists
    if not os.path.exists('.replit'):
        logger.error(".replit file not found")
        return
    
    # Write the updated workflow definition to .replit file
    with open('.replit', 'r') as f:
        replit_content = f.read()
    
    # Check if syncservice workflow is already defined
    if '<name>\nsyncservice\n</name>' in replit_content:
        logger.info("Found existing syncservice workflow, updating it")
        # Replace the existing workflow
        start_idx = replit_content.find('<workflow>\n<name>\nsyncservice\n</name>')
        if start_idx >= 0:
            end_idx = replit_content.find('</workflow>', start_idx) + len('</workflow>')
            replit_content = replit_content[:start_idx] + workflow_content + replit_content[end_idx:]
    else:
        logger.info("Adding new syncservice workflow")
        # Add the workflow to the end
        replit_content += '\n' + workflow_content
    
    # Write the updated content back
    with open('.replit', 'w') as f:
        f.write(replit_content)
    
    logger.info("Updated syncservice workflow to use port 8080")
    
    # Also add a direct invocation script that runs the SyncService directly
    direct_runner_path = 'direct_run_syncservice.py'
    with open(direct_runner_path, 'w') as f:
        f.write("""#!/usr/bin/env python3
\"\"\"
Direct runner for SyncService on port 8080.

This script directly starts the SyncService FastAPI application on port 8080.
\"\"\"

import os
import subprocess
import sys
import time
import signal

def main():
    \"\"\"Run the SyncService directly on port 8080.\"\"\"
    # Force the port via environment variable
    os.environ['SYNC_SERVICE_PORT'] = '8080'
    
    # Build the command
    cmd = [
        'python', '-m', 'uvicorn', 
        'syncservice.main:app', 
        '--host', '0.0.0.0', 
        '--port', '8080',
        '--reload'
    ]
    
    # Change directory to the syncservice directory
    os.chdir('apps/backend/syncservice')
    
    # Start the process
    print(f"Starting SyncService with command: {' '.join(cmd)}")
    process = subprocess.Popen(cmd)
    
    # Set up signal handling
    def handle_signal(sig, frame):
        print(f"Received signal {sig}, stopping SyncService...")
        process.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Wait for the process to complete
    process.wait()

if __name__ == '__main__':
    main()
""")
    
    # Make it executable
    os.chmod(direct_runner_path, 0o755)
    logger.info(f"Created {direct_runner_path} for manual execution")
    
    print("\nTo run the SyncService manually, execute:")
    print(f"    python {direct_runner_path}")
    print("\nTo restart the workflow, use Replit's workflow interface")

if __name__ == '__main__':
    main()