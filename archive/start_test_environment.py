#!/usr/bin/env python
"""
TerraFusion SyncService Test Environment Starter

This script prepares and starts the entire TerraFusion SyncService platform
for testing, including:

1. Starting the API Gateway service
2. Starting the SyncService service
3. Starting the WebSocket server
4. Verifying that all services are running correctly
5. Setting up a test database if needed

Usage:
    python start_test_environment.py [--debug]

Arguments:
    --debug           Enable debug logging
"""

import os
import sys
import time
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Service definitions
SERVICES = [
    {
        "name": "API Gateway",
        "port": 5000,
        "start_script": "bash",
        "start_args": ["-c", "gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app"],
        "check_url": "http://localhost:5000/health",
    },
    {
        "name": "SyncService",
        "port": 8080,
        "start_script": "python",
        "start_args": ["run_syncservice_workflow_8080.py"],
        "check_url": "http://localhost:8080/health",
    },
    {
        "name": "WebSocket Server",
        "port": 8081,
        "start_script": "python",
        "start_args": ["run_websocket_server.py"],
        "check_url": "http://localhost:8081/health",
    }
]

def check_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    import socket
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # 1 second timeout
    
    try:
        result = sock.connect_ex(('localhost', port))
        return result == 0  # Port is in use if result is 0
    except socket.error:
        return False
    finally:
        sock.close()

def terminate_process_on_port(port: int) -> bool:
    """Terminate a process using a specific port."""
    # Find the process ID
    import psutil
    
    for conn in psutil.net_connections(kind='inet'):
        if conn.laddr.port == port:
            process = psutil.Process(conn.pid)
            logger.info(f"Terminating process {process.pid} ({process.name()}) on port {port}")
            
            # Try to terminate gracefully
            process.terminate()
            try:
                process.wait(timeout=3)
                return True
            except psutil.TimeoutExpired:
                # Force kill if it doesn't terminate
                process.kill()
                return True
    
    return False

def start_service(service: Dict) -> Optional[subprocess.Popen]:
    """
    Start a service and return its process.
    
    Args:
        service: Service definition
        
    Returns:
        Process object or None if failed
    """
    name = service["name"]
    port = service["port"]
    
    # Check if port is already in use
    if check_port_in_use(port):
        logger.warning(f"Port {port} is already in use")
        
        # Try to terminate the process
        if terminate_process_on_port(port):
            logger.info(f"Successfully terminated process on port {port}")
        else:
            logger.error(f"Could not terminate process on port {port}")
            return None
        
        # Wait for port to be released
        time.sleep(2)
    
    # Start the service
    logger.info(f"Starting {name}...")
    
    try:
        process = subprocess.Popen(
            [service["start_script"]] + service["start_args"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"{name} started with PID {process.pid}")
        return process
    except Exception as e:
        logger.error(f"Failed to start {name}: {str(e)}")
        return None

def check_service_health(url: str, name: str, max_attempts: int = 10, sleep_interval: int = 1) -> bool:
    """
    Check if a service is healthy by polling its health endpoint.
    
    Args:
        url: Health check URL
        name: Service name for logging
        max_attempts: Maximum number of health check attempts
        sleep_interval: Interval between attempts in seconds
        
    Returns:
        True if service is healthy, False otherwise
    """
    import requests
    
    logger.info(f"Checking health of {name} at {url}...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                logger.info(f"{name} is healthy")
                return True
            else:
                logger.warning(f"{name} returned status code {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.warning(f"Cannot connect to {name} (attempt {attempt}/{max_attempts})")
        except requests.exceptions.Timeout:
            logger.warning(f"Connection to {name} timed out (attempt {attempt}/{max_attempts})")
        except Exception as e:
            logger.warning(f"Error checking {name} health: {str(e)} (attempt {attempt}/{max_attempts})")
        
        if attempt < max_attempts:
            time.sleep(sleep_interval)
    
    logger.error(f"{name} is not healthy after {max_attempts} attempts")
    return False

def setup_test_database() -> bool:
    """
    Set up a test database with sample data if needed.
    
    Returns:
        True if successful, False otherwise
    """
    # Check if seed_initial_data.py exists
    if not os.path.exists("seed_initial_data.py"):
        logger.warning("seed_initial_data.py not found, skipping database setup")
        return True
    
    # Run the script to seed the database
    logger.info("Setting up test database...")
    
    try:
        subprocess.check_call(["python", "seed_initial_data.py"], 
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        
        logger.info("Test database setup completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to set up test database: {e.stderr.decode() if e.stderr else str(e)}")
        return False

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start TerraFusion SyncService test environment")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting TerraFusion SyncService test environment...")
    
    # Start all services
    processes = []
    for service in SERVICES:
        process = start_service(service)
        if process:
            processes.append((service, process))
    
    # Check if all services started
    if len(processes) < len(SERVICES):
        logger.error("Failed to start all services")
        # Stop any started services
        for service, process in processes:
            logger.info(f"Terminating {service['name']}...")
            process.terminate()
        sys.exit(1)
    
    # Wait for services to initialize
    logger.info("Waiting for services to initialize...")
    time.sleep(5)
    
    # Check health of all services
    all_healthy = True
    for service, _ in processes:
        healthy = check_service_health(service["check_url"], service["name"])
        if not healthy:
            all_healthy = False
    
    # Set up test database if all services are healthy
    if all_healthy:
        db_setup = setup_test_database()
        if not db_setup:
            logger.warning("Test database setup failed, but services are running")
    
    # Status report
    if all_healthy:
        logger.info("✅ All services started and healthy")
        logger.info("\nService URLs:")
        for service, _ in processes:
            logger.info(f"  {service['name']}: {service['check_url']}")
        
        # Additional info
        logger.info("\nTo run tests, use the following commands:")
        logger.info("  python run_all_tests.py        # Run all tests")
        logger.info("  python test_websocket.py       # Test WebSocket functionality")
        logger.info("  python test_integration.py     # Test integration between services")
    else:
        logger.error("❌ Some services failed to start or are not healthy")
        logger.error("Please check the logs for details")
    
    # Keep running until interrupted
    try:
        logger.info("\nPress Ctrl+C to stop the test environment")
        
        # Wait for all processes to complete (which they won't unless they crash)
        for _, process in processes:
            process.wait()
    except KeyboardInterrupt:
        logger.info("Stopping test environment...")
        
        # Terminate all processes
        for service, process in processes:
            logger.info(f"Terminating {service['name']}...")
            process.terminate()
    
    logger.info("Test environment stopped")

if __name__ == "__main__":
    main()