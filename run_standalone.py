"""
Standalone runner for TerraFusion SyncService.

This script runs both the Flask API Gateway and the SyncService directly,
without relying on the Replit workflow system.
"""
import os
import sys
import time
import logging
import threading
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Process tracking
api_gateway_process = None
sync_service_process = None

def run_api_gateway():
    """Run the Flask API Gateway."""
    global api_gateway_process
    
    try:
        logger.info("Starting API Gateway on port 5000...")
        
        cmd = [sys.executable, "main.py"]
        api_gateway_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor stdout in real-time
        for line in iter(api_gateway_process.stdout.readline, ""):
            logger.info(f"API Gateway: {line.strip()}")
            
        # If we reach here, the process has terminated
        returncode = api_gateway_process.wait()
        logger.warning(f"API Gateway process exited with code {returncode}")
        
        # Read any remaining stderr
        stderr = api_gateway_process.stderr.read()
        if stderr:
            logger.error(f"API Gateway stderr: {stderr}")
            
    except Exception as e:
        logger.error(f"Error running API Gateway: {str(e)}")
    finally:
        if api_gateway_process and api_gateway_process.poll() is None:
            logger.info("Terminating API Gateway process...")
            api_gateway_process.terminate()


def run_sync_service():
    """Run the SyncService FastAPI application."""
    global sync_service_process
    
    try:
        logger.info("Starting SyncService on port 8080...")
        
        sync_service_dir = "apps/backend/syncservice"
        os.makedirs(sync_service_dir, exist_ok=True)
        
        # Create an __init__.py file if it doesn't exist
        init_file = os.path.join(sync_service_dir, "__init__.py")
        if not os.path.exists(init_file):
            with open(init_file, "w") as f:
                pass
        
        # Run the SyncService using the main.py in the syncservice module
        cmd = [
            sys.executable, 
            "-c", 
            "from apps.backend.syncservice.syncservice.main import app; "
            "import uvicorn; "
            "uvicorn.run(app, host='0.0.0.0', port=8080)"
        ]
        
        sync_service_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor stdout in real-time
        for line in iter(sync_service_process.stdout.readline, ""):
            logger.info(f"SyncService: {line.strip()}")
            
        # If we reach here, the process has terminated
        returncode = sync_service_process.wait()
        logger.warning(f"SyncService process exited with code {returncode}")
        
        # Read any remaining stderr
        stderr = sync_service_process.stderr.read()
        if stderr:
            logger.error(f"SyncService stderr: {stderr}")
            
    except Exception as e:
        logger.error(f"Error running SyncService: {str(e)}")
    finally:
        if sync_service_process and sync_service_process.poll() is None:
            logger.info("Terminating SyncService process...")
            sync_service_process.terminate()


def monitor_processes():
    """Monitor running processes and restart if necessary."""
    global api_gateway_process, sync_service_process
    
    while True:
        try:
            # Check API Gateway
            if api_gateway_process and api_gateway_process.poll() is not None:
                logger.warning("API Gateway process has stopped, restarting...")
                api_gateway_thread = threading.Thread(target=run_api_gateway)
                api_gateway_thread.daemon = True
                api_gateway_thread.start()
            
            # Check SyncService
            if sync_service_process and sync_service_process.poll() is not None:
                logger.warning("SyncService process has stopped, restarting...")
                sync_service_thread = threading.Thread(target=run_sync_service)
                sync_service_thread.daemon = True
                sync_service_thread.start()
                
            # Sleep before next check
            time.sleep(10)
            
        except Exception as e:
            logger.error(f"Error in process monitor: {str(e)}")
            time.sleep(10)


def cleanup():
    """Clean up processes on exit."""
    global api_gateway_process, sync_service_process
    
    logger.info("Cleaning up processes...")
    
    if api_gateway_process and api_gateway_process.poll() is None:
        logger.info("Terminating API Gateway process...")
        api_gateway_process.terminate()
        api_gateway_process.wait(timeout=5)
        
    if sync_service_process and sync_service_process.poll() is None:
        logger.info("Terminating SyncService process...")
        sync_service_process.terminate()
        sync_service_process.wait(timeout=5)


def main():
    """Main entry point."""
    try:
        logger.info("Starting TerraFusion SyncService standalone runner...")
        
        # Start API Gateway in a separate thread
        api_gateway_thread = threading.Thread(target=run_api_gateway)
        api_gateway_thread.daemon = True
        api_gateway_thread.start()
        
        # Allow API Gateway to start before SyncService
        time.sleep(2)
        
        # Start SyncService in a separate thread
        sync_service_thread = threading.Thread(target=run_sync_service)
        sync_service_thread.daemon = True
        sync_service_thread.start()
        
        # Start the process monitor
        monitor_thread = threading.Thread(target=monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Wait for keyboard interrupt
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()