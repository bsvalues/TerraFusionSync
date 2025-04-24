"""
Entry point script for the SyncService workflow.

This script overrides any port settings from the workflow configuration
and ensures that the SyncService always runs on port 8080.
"""

import os
import sys
import signal
import subprocess

def signal_handler(sig, frame):
    """Handle signals gracefully."""
    print("Exiting syncservice workflow entry point...")
    sys.exit(0)

def main():
    """
    Main entry point that forces the SyncService to run on port 8080.
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("SyncService workflow entry point starting...")
    print("IMPORTANT: Overriding any port settings to use port 8080")
    
    # Use our port 8080 runner script instead of the default command
    runner_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "run_syncservice_workflow_8080.py")
    
    if not os.path.exists(runner_script):
        print(f"ERROR: Runner script not found at {runner_script}")
        sys.exit(1)
    
    print(f"Using runner script: {runner_script}")
    
    # Execute the runner script directly
    os.execv(sys.executable, [sys.executable, runner_script])

if __name__ == "__main__":
    main()