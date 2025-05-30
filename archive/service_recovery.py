"""
TerraFusion SyncService Recovery Utilities

This module provides utilities for manual service recovery and health checking
for the TerraFusion SyncService platform.
"""

import os
import sys
import time
import json
import logging
import requests
import subprocess
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('service_recovery')

# Service endpoints
API_GATEWAY_URL = "http://localhost:5000"
SYNC_SERVICE_URL = "http://localhost:8080"

# Service status check endpoints
STATUS_ENDPOINTS = {
    "api_gateway": f"{API_GATEWAY_URL}/api/status",
    "sync_service": f"{SYNC_SERVICE_URL}/health",
    "sync_service_live": f"{SYNC_SERVICE_URL}/health/live",
    "sync_service_ready": f"{SYNC_SERVICE_URL}/health/ready"
}


def check_service_status(service_name: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Check the status of a service.
    
    Args:
        service_name: Name of the service to check
        
    Returns:
        Tuple of (is_healthy, response_data)
    """
    if service_name not in STATUS_ENDPOINTS:
        logger.error(f"Unknown service: {service_name}")
        return False, {"error": f"Unknown service: {service_name}"}
    
    url = STATUS_ENDPOINTS[service_name]
    
    try:
        logger.info(f"Checking {service_name} status at {url}")
        response = requests.get(url, timeout=5)
        
        is_healthy = response.status_code == 200
        
        try:
            data = response.json()
        except ValueError:
            data = {"status": "unknown", "response_text": response.text[:100]}
        
        return is_healthy, data
    
    except requests.RequestException as e:
        logger.error(f"Error checking {service_name}: {str(e)}")
        return False, {"error": str(e)}


def restart_api_gateway():
    """
    Restart the API Gateway service.
    
    Returns:
        True if restart was successful, False otherwise
    """
    logger.info("Restarting API Gateway service")
    
    try:
        # Using the workflow restart method
        subprocess.run(
            ["replit", "workflow", "restart", "Start application"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the service to start
        logger.info("Waiting for API Gateway to start...")
        for _ in range(5):
            time.sleep(3)
            is_healthy, _ = check_service_status("api_gateway")
            if is_healthy:
                logger.info("API Gateway restarted successfully")
                return True
        
        logger.error("API Gateway did not start within the timeout period")
        return False
        
    except subprocess.SubprocessError as e:
        logger.error(f"Error restarting API Gateway: {str(e)}")
        return False


def restart_sync_service():
    """
    Restart the SyncService.
    
    Returns:
        True if restart was successful, False otherwise
    """
    logger.info("Restarting SyncService")
    
    try:
        # First try using the workflow restart
        subprocess.run(
            ["replit", "workflow", "restart", "syncservice"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for the service to start
        logger.info("Waiting for SyncService to start...")
        for _ in range(5):
            time.sleep(3)
            is_healthy, _ = check_service_status("sync_service")
            if is_healthy:
                logger.info("SyncService restarted successfully")
                return True
        
        # If workflow restart failed, try the dedicated restart script
        logger.warning("Workflow restart didn't bring up SyncService, trying restart script")
        subprocess.run(
            ["python", "restart_syncservice_workflow.py"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait again for the service to start
        for _ in range(5):
            time.sleep(3)
            is_healthy, _ = check_service_status("sync_service")
            if is_healthy:
                logger.info("SyncService restarted successfully using restart script")
                return True
        
        logger.error("SyncService did not start within the timeout period")
        return False
        
    except subprocess.SubprocessError as e:
        logger.error(f"Error restarting SyncService: {str(e)}")
        return False


def comprehensive_health_check() -> Dict[str, Any]:
    """
    Perform comprehensive health check of all services.
    
    Returns:
        Dictionary with health status details
    """
    results = {}
    
    # Check each service
    for service_name in STATUS_ENDPOINTS:
        is_healthy, data = check_service_status(service_name)
        results[service_name] = {
            "is_healthy": is_healthy,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Get additional metrics
    try:
        response = requests.get(f"{SYNC_SERVICE_URL}/metrics", timeout=5)
        if response.status_code == 200:
            results["metrics"] = response.json()
    except requests.RequestException as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        results["metrics"] = {"error": str(e)}
    
    # Determine overall health
    services_healthy = all(service["is_healthy"] for service in results.values() 
                         if isinstance(service, dict) and "is_healthy" in service)
    
    results["overall_health"] = {
        "is_healthy": services_healthy,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    return results


def display_health_status(health_data: Dict[str, Any]):
    """
    Display health check results in a readable format.
    
    Args:
        health_data: Health check results
    """
    print("\n===== TerraFusion SyncService Health Status =====\n")
    
    # Overall health
    if health_data["overall_health"]["is_healthy"]:
        print("Overall Status: \033[92mHEALTHY\033[0m")
    else:
        print("Overall Status: \033[91mUNHEALTHY\033[0m")
    
    print(f"Timestamp: {health_data['overall_health']['timestamp']}")
    print("\n----- Component Status -----\n")
    
    # Service status
    for service_name, service_data in health_data.items():
        if service_name in ["overall_health", "metrics"]:
            continue
        
        if service_data["is_healthy"]:
            status = "\033[92mHEALTHY\033[0m"
        else:
            status = "\033[91mUNHEALTHY\033[0m"
        
        print(f"{service_name}: {status}")
        
        if "data" in service_data and isinstance(service_data["data"], dict):
            # Print relevant status information
            if "status" in service_data["data"]:
                print(f"  Status: {service_data['data']['status']}")
            if "time" in service_data["data"]:
                print(f"  Time: {service_data['data']['time']}")
            if "version" in service_data["data"]:
                print(f"  Version: {service_data['data']['version']}")
            if "error" in service_data["data"]:
                print(f"  Error: {service_data['data']['error']}")
        
        print()
    
    # Metrics summary
    if "metrics" in health_data and isinstance(health_data["metrics"], dict):
        print("----- System Metrics -----\n")
        
        metrics = health_data["metrics"]
        if "system" in metrics and isinstance(metrics["system"], dict):
            system = metrics["system"]
            print(f"CPU Usage: {system.get('cpu_usage_percent', 'N/A')}%")
            print(f"Memory Usage: {system.get('memory_usage_percent', 'N/A')}%")
            print(f"Disk Usage: {system.get('disk_usage_percent', 'N/A')}%")
            print(f"Active Connections: {system.get('active_connections', 'N/A')}")
        
        if "operations" in metrics and isinstance(metrics["operations"], dict):
            ops = metrics["operations"]
            print(f"\nTotal Operations: {ops.get('total_operations', 'N/A')}")
            print(f"Successful Operations: {ops.get('successful_operations', 'N/A')}")
            print(f"Failed Operations: {ops.get('failed_operations', 'N/A')}")
            print(f"Success Rate: {ops.get('success_rate_percent', 'N/A')}%")
    
    print("\n=============================================\n")


def main():
    """Main entry point for the recovery utility."""
    parser = argparse.ArgumentParser(description="TerraFusion SyncService Recovery Utility")
    parser.add_argument('command', choices=['check', 'restart-api', 'restart-sync', 'restart-all'],
                        help="Command to execute")
    parser.add_argument('--save', action='store_true',
                        help="Save health check results to health_status.json")
    
    args = parser.parse_args()
    
    if args.command == 'check':
        # Perform health check
        health_data = comprehensive_health_check()
        display_health_status(health_data)
        
        if args.save:
            with open('health_status.json', 'w') as f:
                json.dump(health_data, f, indent=2)
            print(f"Health status saved to health_status.json")
    
    elif args.command == 'restart-api':
        # Restart API Gateway
        success = restart_api_gateway()
        if success:
            print("API Gateway restarted successfully")
        else:
            print("Failed to restart API Gateway")
            sys.exit(1)
    
    elif args.command == 'restart-sync':
        # Restart SyncService
        success = restart_sync_service()
        if success:
            print("SyncService restarted successfully")
        else:
            print("Failed to restart SyncService")
            sys.exit(1)
    
    elif args.command == 'restart-all':
        # Restart both services
        sync_success = restart_sync_service()
        api_success = restart_api_gateway()
        
        if sync_success and api_success:
            print("All services restarted successfully")
        else:
            if not sync_success:
                print("Failed to restart SyncService")
            if not api_success:
                print("Failed to restart API Gateway")
            sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)