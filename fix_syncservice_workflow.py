"""
Fix SyncService Workflow - Port 8080

This script ensures that the SyncService is properly launched and stays
running on port 8080 without port conflicts or shutdown issues.
"""

import os
import subprocess
import sys
import time
import signal
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Port for SyncService
PORT = 8080

def check_port_in_use(port):
    """Check if a port is in use by another process."""
    try:
        # Try using netstat to check if port is in use
        result = subprocess.run(
            f"netstat -tuln | grep {port}", 
            shell=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return bool(result.stdout)
    except Exception:
        # If netstat fails, we'll try another approach
        try:
            # Try to bind to the port as another test
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            # If result is 0, port is in use
            return result == 0
        except Exception:
            # If all checks fail, assume port is free
            return False

def kill_process_on_port(port):
    """Kill any process running on the specified port."""
    try:
        # Try to find PID using lsof if available
        try:
            cmd = f"lsof -i :{port} -t"
            pid = subprocess.check_output(cmd, shell=True).decode().strip()
            if pid:
                logger.info(f"Found process {pid} on port {port}")
                # Kill the process
                os.kill(int(pid), signal.SIGTERM)
                time.sleep(1)
                return True
        except Exception:
            pass

        # Alternative approach using fuser if available
        try:
            cmd = f"fuser -k {port}/tcp"
            subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)
            time.sleep(1)
            return True
        except Exception:
            pass

        # If both methods fail, try a more general approach
        try:
            # Look for Python processes related to uvicorn/fastapi
            cmd = "ps aux | grep '[p]ython.*uvicorn'"
            result = subprocess.check_output(cmd, shell=True).decode()
            for line in result.splitlines():
                # If the port is mentioned in the command line
                if f"port {port}" in line.lower() or f":{port}" in line:
                    pid = line.split()[1]
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)
                    return True
        except Exception:
            pass

        return False
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {e}")
        return False

def start_syncservice():
    """Start the SyncService with proper configuration."""
    logger.info("Starting SyncService on port 8080...")
    
    # Check if port is already in use
    if check_port_in_use(PORT):
        logger.warning(f"Port {PORT} is already in use. Attempting to free it...")
        if kill_process_on_port(PORT):
            logger.info(f"Successfully killed process on port {PORT}")
        else:
            logger.warning(f"Could not kill process on port {PORT}. Proceeding anyway...")
    
    # Start the SyncService using uvicorn directly for better stability
    cmd = [
        sys.executable,
        "-m", "uvicorn",
        "terrafusion_sync.app:app",
        "--host", "0.0.0.0",
        "--port", str(PORT),
        "--log-level", "info",
        "--reload",
    ]
    
    logger.info(f"Running command: {' '.join(cmd)}")
    
    # Start the process and make sure it stays running
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1  # Line buffered
    )
    
    # Forward all output to the console
    try:
        for line in process.stdout:
            # Remove trailing whitespace
            line = line.rstrip()
            print(line, flush=True)
            # Check for successful startup messages
            if "Application startup complete" in line:
                logger.info("SyncService successfully started!")
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down SyncService...")
        process.terminate()
        process.wait(timeout=5)
    except Exception as e:
        logger.error(f"Error running SyncService: {e}")
    finally:
        # Make sure process is terminated properly
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        
        exit_code = process.returncode
        logger.info(f"SyncService process exited with code {exit_code}")
        return exit_code

if __name__ == "__main__":
    # In case of failure, retry up to 3 times
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        logger.info(f"SyncService launch attempt {attempt}/{max_retries}")
        exit_code = start_syncservice()
        
        # If process exited successfully, we're done
        if exit_code == 0:
            break
        
        # If retries remain, wait briefly and try again
        if attempt < max_retries:
            logger.warning(f"SyncService exited with code {exit_code}. Retrying in 3 seconds...")
            time.sleep(3)
        else:
            logger.error(f"SyncService failed to start after {max_retries} attempts.")
            sys.exit(1)