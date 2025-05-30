"""
Standalone runner for TerraFusion SyncService.

This script runs both the Flask API Gateway and the SyncService directly,
without relying on the Replit workflow system.
"""
import os
import sys
import time
import signal
import logging
import subprocess
import atexit
from threading import Thread

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Process tracking
processes = []

def run_api_gateway():
    """Run the Flask API Gateway."""
    logger.info("Starting API Gateway on port 5000...")
    try:
        cmd = ["gunicorn", "--bind", "0.0.0.0:5000", "--reuse-port", "--reload", "main:app"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("API Gateway", proc))
        
        # Stream logs
        for line in proc.stdout:
            logger.info(f"[API Gateway] {line.strip()}")
            
    except Exception as e:
        logger.error(f"Error starting API Gateway: {e}")

def run_sync_service():
    """Run the SyncService FastAPI application."""
    logger.info("Starting SyncService on port 8080...")
    try:
        cmd = ["python", "-m", "uvicorn", "syncservice:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        processes.append(("SyncService", proc))
        
        # Stream logs
        for line in proc.stdout:
            logger.info(f"[SyncService] {line.strip()}")
            
    except Exception as e:
        logger.error(f"Error starting SyncService: {e}")

def monitor_processes():
    """Monitor running processes and restart if necessary."""
    while True:
        for i, (name, proc) in enumerate(processes):
            if proc.poll() is not None:
                logger.warning(f"{name} exited with code {proc.returncode}, restarting...")
                if name == "API Gateway":
                    Thread(target=run_api_gateway).start()
                else:
                    Thread(target=run_sync_service).start()
                # Remove the old process from our list
                processes.pop(i)
        
        time.sleep(5)

def cleanup():
    """Clean up processes on exit."""
    logger.info("Shutting down all services...")
    for name, proc in processes:
        logger.info(f"Terminating {name}...")
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            logger.warning(f"{name} did not terminate gracefully, killing...")
            proc.kill()
        except Exception as e:
            logger.error(f"Error terminating {name}: {e}")

def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {sig}, shutting down...")
    sys.exit(0)

def main():
    """Main entry point."""
    # Register cleanup function
    atexit.register(cleanup)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the API Gateway in a separate thread
    api_thread = Thread(target=run_api_gateway)
    api_thread.daemon = True
    api_thread.start()
    
    # Start the SyncService in a separate thread
    sync_thread = Thread(target=run_sync_service)
    sync_thread.daemon = True
    sync_thread.start()
    
    # Wait for the services to start
    logger.info("Waiting for services to start...")
    time.sleep(3)
    
    # Start the monitoring thread
    monitor_thread = Thread(target=monitor_processes)
    monitor_thread.daemon = True
    monitor_thread.start()
    
    logger.info("TerraFusion SyncService is running!")
    logger.info("API Gateway: http://0.0.0.0:5000")
    logger.info("SyncService: http://0.0.0.0:8080")
    logger.info("Press Ctrl+C to stop all services")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main()