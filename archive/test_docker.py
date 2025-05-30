#!/usr/bin/env python
"""
TerraFusion SyncService Docker Test Script

This script tests the Docker container setup for the TerraFusion SyncService platform by:
1. Building the Docker images
2. Starting the containers with docker-compose
3. Verifying that services are accessible
4. Running basic API tests against the containerized services
5. Shutting down the containers

This helps ensure the Docker deployment will work correctly in production.

Usage:
    python test_docker.py [--skip-build]

Arguments:
    --skip-build        Skip building the Docker images (use existing images)
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
API_PORT = 5000
SYNC_PORT = 8080
WEBSOCKET_PORT = 8081
DOCKER_API_URL = f"http://localhost:{API_PORT}"
DOCKER_SYNC_URL = f"http://localhost:{SYNC_PORT}"
DOCKER_WEBSOCKET_URL = f"http://localhost:{WEBSOCKET_PORT}"

# Test results
class DockerTestResults:
    """Track results of Docker tests."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = []
        self.success_count = 0
        self.failure_count = 0
    
    def add_result(self, test_name: str, success: bool, details: str = None):
        """Add a test result."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            logger.error(f"Test failed: {test_name} - {details}")
    
    def print_summary(self):
        """Print a summary of the test results."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n============================================")
        print("  TERRAFUSION DOCKER TEST RESULTS")
        print("============================================")
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration:.2f} seconds")
        print("--------------------------------------------")
        
        # Print individual test results
        for result in self.results:
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{status} {result['test']}")
            if not result["success"] and result["details"]:
                print(f"  → {result['details']}")
        
        # Print summary
        print("--------------------------------------------")
        total = self.success_count + self.failure_count
        print(f"TESTS:  {total} total, {self.success_count} passed, {self.failure_count} failed")
        print(f"RESULT: {'✅ PASSED' if self.failure_count == 0 else '❌ FAILED'}")
        print("============================================\n")
        
        return self.failure_count == 0

def run_command(cmd: List[str], check: bool = True) -> Tuple[bool, str]:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command to run as a list of arguments
        check: Whether to raise an exception on failure
        
    Returns:
        (success, output)
    """
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return True, output
    except subprocess.CalledProcessError as e:
        return False, e.output
    except Exception as e:
        return False, str(e)

def check_docker_installed() -> bool:
    """Check if Docker is installed and running."""
    logger.info("Checking if Docker is installed and running...")
    
    # Check docker command
    docker_success, docker_output = run_command(["docker", "--version"], check=False)
    if not docker_success:
        logger.error("Docker is not installed or not in PATH")
        return False
    
    # Check docker-compose command
    compose_success, compose_output = run_command(["docker-compose", "--version"], check=False)
    if not compose_success:
        logger.error("docker-compose is not installed or not in PATH")
        return False
    
    # Check if Docker daemon is running
    daemon_success, daemon_output = run_command(["docker", "info"], check=False)
    if not daemon_success:
        logger.error("Docker daemon is not running")
        return False
    
    logger.info("Docker is installed and running")
    return True

def build_docker_images() -> bool:
    """Build the Docker images."""
    logger.info("Building Docker images...")
    
    # Build api-gateway image
    logger.info("Building API Gateway image...")
    api_success, api_output = run_command(
        ["docker", "build", "-t", "terrafusion/api-gateway", "-f", "Dockerfile.api-gateway", "."],
        check=False
    )
    if not api_success:
        logger.error(f"Failed to build API Gateway image: {api_output}")
        return False
    
    # Build sync-service image
    logger.info("Building SyncService image...")
    sync_success, sync_output = run_command(
        ["docker", "build", "-t", "terrafusion/sync-service", "-f", "Dockerfile.sync-service", "."],
        check=False
    )
    if not sync_success:
        logger.error(f"Failed to build SyncService image: {sync_output}")
        return False
    
    logger.info("Docker images built successfully")
    return True

def start_docker_containers() -> bool:
    """Start the Docker containers with docker-compose."""
    logger.info("Starting Docker containers...")
    
    # Start containers
    success, output = run_command(["docker-compose", "up", "-d"], check=False)
    if not success:
        logger.error(f"Failed to start containers: {output}")
        return False
    
    # Give containers time to start
    logger.info("Waiting for containers to start...")
    time.sleep(10)
    
    # Check if containers are running
    success, output = run_command(["docker-compose", "ps"], check=False)
    if not success:
        logger.error(f"Failed to check container status: {output}")
        return False
    
    logger.info("Docker containers started successfully")
    return True

def stop_docker_containers() -> bool:
    """Stop and remove the Docker containers."""
    logger.info("Stopping Docker containers...")
    
    # Stop containers
    success, output = run_command(["docker-compose", "down"], check=False)
    if not success:
        logger.error(f"Failed to stop containers: {output}")
        return False
    
    logger.info("Docker containers stopped successfully")
    return True

def check_service_health(url: str, service_name: str) -> Tuple[bool, str]:
    """
    Check if a service is healthy.
    
    Args:
        url: Base URL of the service
        service_name: Name of the service for logging
        
    Returns:
        (success, message)
    """
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"{service_name} is healthy")
            return True, "Service is healthy"
        else:
            logger.error(f"{service_name} returned status code {response.status_code}")
            return False, f"Unhealthy status code: {response.status_code}"
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to {service_name}")
        return False, "Connection error"
    except requests.exceptions.Timeout:
        logger.error(f"{service_name} timed out")
        return False, "Connection timeout"
    except Exception as e:
        logger.error(f"Error checking {service_name} health: {str(e)}")
        return False, f"Error: {str(e)}"

def test_api_gateway() -> Tuple[bool, str]:
    """
    Test the API Gateway container.
    
    Returns:
        (success, message)
    """
    return check_service_health(DOCKER_API_URL, "API Gateway")

def test_sync_service() -> Tuple[bool, str]:
    """
    Test the SyncService container.
    
    Returns:
        (success, message)
    """
    return check_service_health(DOCKER_SYNC_URL, "SyncService")

def test_api_endpoints() -> Tuple[bool, str]:
    """
    Test basic API endpoints.
    
    Returns:
        (success, message)
    """
    try:
        # Test the root endpoint
        response = requests.get(f"{DOCKER_API_URL}/", timeout=5)
        if response.status_code != 200:
            return False, f"Root endpoint returned status code {response.status_code}"
        
        # Test the status endpoint
        response = requests.get(f"{DOCKER_API_URL}/status", timeout=5)
        if response.status_code != 200:
            return False, f"Status endpoint returned status code {response.status_code}"
        
        # Check if the status response contains the expected components
        status_data = response.json()
        if "components" not in status_data:
            return False, "Status response missing 'components' field"
        
        components = status_data["components"]
        if "api_gateway" not in components or "sync_service" not in components:
            return False, "Status response missing required component statuses"
        
        logger.info("API endpoints are working correctly")
        return True, "API endpoints are working correctly"
    except Exception as e:
        logger.error(f"Error testing API endpoints: {str(e)}")
        return False, f"Error: {str(e)}"

def test_sync_api_endpoints() -> Tuple[bool, str]:
    """
    Test SyncService API endpoints.
    
    Returns:
        (success, message)
    """
    try:
        # Test the health endpoint directly
        response = requests.get(f"{DOCKER_SYNC_URL}/health", timeout=5)
        if response.status_code != 200:
            return False, f"Health endpoint returned status code {response.status_code}"
        
        # Test the metrics endpoint
        response = requests.get(f"{DOCKER_SYNC_URL}/metrics", timeout=5)
        if response.status_code != 200:
            return False, f"Metrics endpoint returned status code {response.status_code}"
        
        logger.info("SyncService API endpoints are working correctly")
        return True, "SyncService API endpoints are working correctly"
    except Exception as e:
        logger.error(f"Error testing SyncService API endpoints: {str(e)}")
        return False, f"Error: {str(e)}"

def test_service_interaction() -> Tuple[bool, str]:
    """
    Test interaction between services.
    
    Returns:
        (success, message)
    """
    try:
        # Test the proxy endpoint (API Gateway -> SyncService)
        response = requests.get(f"{DOCKER_API_URL}/api/sync/health", timeout=5)
        if response.status_code != 200:
            return False, f"Proxy endpoint returned status code {response.status_code}"
        
        logger.info("Service interaction is working correctly")
        return True, "Service interaction is working correctly"
    except Exception as e:
        logger.error(f"Error testing service interaction: {str(e)}")
        return False, f"Error: {str(e)}"

def run_docker_tests(skip_build: bool = False) -> DockerTestResults:
    """
    Run all Docker tests and return results.
    
    Args:
        skip_build: Whether to skip building Docker images
        
    Returns:
        DockerTestResults object
    """
    results = DockerTestResults()
    
    # Check if Docker is installed
    docker_installed = check_docker_installed()
    results.add_result("Docker Installation Check", docker_installed)
    
    if not docker_installed:
        return results
    
    # Build Docker images if needed
    if not skip_build:
        build_success = build_docker_images()
        results.add_result("Build Docker Images", build_success)
        
        if not build_success:
            return results
    
    # Start Docker containers
    start_success = start_docker_containers()
    results.add_result("Start Docker Containers", start_success)
    
    if not start_success:
        return results
    
    try:
        # Test API Gateway health
        api_success, api_message = test_api_gateway()
        results.add_result("API Gateway Health", api_success, api_message)
        
        # Test SyncService health
        sync_success, sync_message = test_sync_service()
        results.add_result("SyncService Health", sync_success, sync_message)
        
        # Test API endpoints
        api_endpoints_success, api_endpoints_message = test_api_endpoints()
        results.add_result("API Endpoints", api_endpoints_success, api_endpoints_message)
        
        # Test SyncService API endpoints
        sync_api_success, sync_api_message = test_sync_api_endpoints()
        results.add_result("SyncService API Endpoints", sync_api_success, sync_api_message)
        
        # Test service interaction
        interaction_success, interaction_message = test_service_interaction()
        results.add_result("Service Interaction", interaction_success, interaction_message)
        
    finally:
        # Stop Docker containers
        stop_success = stop_docker_containers()
        results.add_result("Stop Docker Containers", stop_success)
    
    return results

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test TerraFusion SyncService Docker setup")
    parser.add_argument("--skip-build", action="store_true", help="Skip building Docker images")
    args = parser.parse_args()
    
    logger.info("Starting Docker tests...")
    
    # Run tests
    results = run_docker_tests(args.skip_build)
    
    # Print results
    all_passed = results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()