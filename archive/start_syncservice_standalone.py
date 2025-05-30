"""
TerraFusion SyncService - Standalone Server

This script starts a standalone FastAPI server for the SyncService,
bypassing the Replit workflow system and any potential port conflicts.

Features:
- Ensures a clean startup by checking and freeing port if necessary
- Applies fixes to Market Analysis plugin modules
- Enables proper integration of the plugin with the SyncService
- Robust error handling and logging
"""

import os
import sys
import time
import signal
import logging
import socket
import subprocess
import traceback
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
PORT = 8080
MAX_RETRIES = 3
RETRY_DELAY = 3  # seconds
TIMEOUT = 60  # seconds to wait for server to start

def is_port_in_use(port):
    """Check if a port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def ensure_directory_exists(path):
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)
    return path

def run_command(cmd, shell=False, timeout=None):
    """Run a command and return the output."""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        if e.output:
            logger.error(f"Output: {e.output}")
        return None
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds")
        return None
    except Exception as e:
        logger.error(f"Command execution error: {str(e)}")
        return None

def kill_process_on_port(port):
    """Kill any process using the specified port."""
    try:
        # Different commands for different platforms
        if sys.platform.startswith('win'):
            # Windows
            cmd = f"netstat -ano | findstr :{port}"
            output = run_command(cmd, shell=True)
            if output:
                for line in output.splitlines():
                    if f":{port}" in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            pid = parts[4]
                            logger.info(f"Killing process {pid} on port {port}")
                            run_command(f"taskkill /F /PID {pid}", shell=True)
        else:
            # Linux/Mac
            cmd = f"lsof -i :{port} -t"
            output = run_command(cmd, shell=True)
            if output:
                for pid in output.splitlines():
                    logger.info(f"Killing process {pid} on port {port}")
                    run_command(f"kill -9 {pid}", shell=True)
                    
        # Wait for port to be released
        time.sleep(1)
        return not is_port_in_use(port)
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")
        return False

def create_market_analysis_plugin_files():
    """
    Create or update Market Analysis plugin files to fix any issues.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create the plugin directory structure if it doesn't exist
        plugin_dir = Path("terrafusion_sync/plugins/market_analysis")
        ensure_directory_exists(plugin_dir)
        
        # Create the __init__.py file to make it a proper Python package
        init_path = plugin_dir / "__init__.py"
        if not init_path.exists():
            with open(init_path, 'w') as f:
                f.write("""\"\"\"
TerraFusion SyncService - Market Analysis Plugin

This plugin provides market analysis functionality for real estate data,
including trend analysis, comparable market area evaluation, and price metrics.
\"\"\"

import logging

# Configure plugin logger
logger = logging.getLogger(__name__)
logger.info("Market Analysis plugin initialized")
""")
            logger.info(f"Created {init_path}")
            
        # Apply existing fix scripts
        router_fix_script = Path("fix_market_analysis_router.py")
        if router_fix_script.exists():
            logger.info("Applying Market Analysis router fixes...")
            output = run_command([sys.executable, str(router_fix_script)], timeout=10)
            if output:
                logger.info(f"Router fix output: {output}")
        
        task_fix_script = Path("fix_market_analysis_background_task.py")
        if task_fix_script.exists():
            logger.info("Applying Market Analysis background task fixes...")
            output = run_command([sys.executable, str(task_fix_script)], timeout=10)
            if output:
                logger.info(f"Task fix output: {output}")
                
        logger.info("Market Analysis plugin files updated successfully")
        return True
    except Exception as e:
        logger.error(f"Error updating Market Analysis plugin files: {e}")
        logger.error(traceback.format_exc())
        return False

def main():
    logger.info("=== TerraFusion SyncService Standalone Server ===")
    logger.info(f"Current time: {datetime.now().isoformat()}")
    logger.info(f"Python: {sys.executable}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, lambda sig, frame: sys.exit(0))
    signal.signal(signal.SIGTERM, lambda sig, frame: sys.exit(0))
    
    # Check if port is in use and kill any existing process
    if is_port_in_use(PORT):
        logger.warning(f"Port {PORT} is already in use, attempting to free it...")
        if not kill_process_on_port(PORT):
            logger.error(f"Failed to free port {PORT}, exiting")
            return 1
    
    # Update Market Analysis plugin files
    if not create_market_analysis_plugin_files():
        logger.error("Failed to update Market Analysis plugin files")
        return 1
    
    # Build the uvicorn command
    logger.info(f"Starting SyncService on port {PORT}")
    cmd = [
        sys.executable, "-m", "uvicorn",
        "terrafusion_sync.app:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--reload",
        "--log-level", "info"
    ]
    
    logger.info(f"Command: {' '.join(cmd)}")
    
    # Start the server
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        logger.info(f"Started server process with PID {process.pid}")
        
        # Monitor for successful startup
        start_time = time.time()
        startup_success = False
        
        try:
            while time.time() - start_time < TIMEOUT:
                line = process.stdout.readline()
                if not line:
                    break
                
                print(line.rstrip())
                
                if "Application startup complete" in line:
                    startup_success = True
                    logger.info("Server started successfully!")
                    break
                
                # Check if process is still running
                if process.poll() is not None:
                    logger.error(f"Server process exited with code {process.returncode}")
                    break
            
            if not startup_success:
                if process.poll() is None:
                    logger.error(f"Server failed to start within {TIMEOUT} seconds")
                    process.terminate()
                    return 1
            
            # Keep server running and capture output
            while process.poll() is None:
                line = process.stdout.readline()
                if line:
                    print(line.rstrip())
            
            # Process exited
            logger.info(f"Server process exited with code {process.returncode}")
            return process.returncode
            
        except KeyboardInterrupt:
            logger.info("Received Ctrl+C, shutting down server...")
            if process.poll() is None:
                process.terminate()
            return 0
        
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())