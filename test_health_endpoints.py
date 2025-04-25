#!/usr/bin/env python3
"""
Health Endpoint Smoke Test Script

This script tests the health endpoints of both the API Gateway (port 5000)
and the SyncService (port 8080) to verify they are working correctly.

Usage:
    python test_health_endpoints.py
"""

import argparse
import json
import sys
import time
from typing import Dict, List, Tuple
import requests


# Define the services and their health endpoints
SERVICES = {
    "API Gateway": {
        "base_url": "http://localhost:5000",
        "endpoints": {
            "liveness": "/health/live",
            "readiness": "/health/ready"
        }
    },
    "SyncService": {
        "base_url": "http://localhost:8080",
        "endpoints": {
            "health": "/health"
        }
    }
}


def test_endpoint(url: str, expected_status: int = 200) -> Tuple[bool, dict, int]:
    """
    Test a health endpoint and return the result.
    
    Args:
        url: The URL to test
        expected_status: The expected HTTP status code (default: 200)
        
    Returns:
        Tuple of (success, response_json, status_code)
    """
    try:
        response = requests.get(url, timeout=5)
        status_code = response.status_code
        
        try:
            response_json = response.json()
        except ValueError:
            response_json = {"error": "Invalid JSON response", "text": response.text}
        
        return status_code == expected_status, response_json, status_code
    except requests.RequestException as e:
        return False, {"error": str(e)}, 0


def run_tests(verbose: bool = False) -> Tuple[bool, List[Dict]]:
    """
    Run tests on all health endpoints.
    
    Args:
        verbose: Whether to print verbose output
        
    Returns:
        Tuple of (all_passed, results)
    """
    results = []
    all_passed = True
    
    for service_name, service_config in SERVICES.items():
        base_url = service_config["base_url"]
        
        for endpoint_name, endpoint_path in service_config["endpoints"].items():
            url = f"{base_url}{endpoint_path}"
            
            if verbose:
                print(f"Testing {service_name} {endpoint_name} endpoint: {url}")
            
            success, response, status_code = test_endpoint(url)
            all_passed = all_passed and success
            
            result = {
                "service": service_name,
                "endpoint": endpoint_name,
                "url": url,
                "success": success,
                "status_code": status_code,
                "response": response
            }
            
            results.append(result)
            
            if verbose:
                status = "✅ PASSED" if success else "❌ FAILED"
                print(f"  {status} (Status: {status_code})")
                print(f"  Response: {json.dumps(response, indent=2)}")
                print()
    
    return all_passed, results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test health endpoints of TerraFusion services")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("-w", "--wait", type=int, default=0, help="Wait time in seconds before running tests")
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"Waiting {args.wait} seconds for services to start...")
        time.sleep(args.wait)
    
    print("Testing health endpoints...")
    all_passed, results = run_tests(args.verbose)
    
    if all_passed:
        print("\n✅ All health endpoint tests PASSED")
        return 0
    else:
        print("\n❌ Some health endpoint tests FAILED")
        if not args.verbose:
            print("\nRun with --verbose for detailed information")
            
            # Print a summary of failures
            for result in results:
                if not result["success"]:
                    service = result["service"]
                    endpoint = result["endpoint"]
                    status = result["status_code"]
                    print(f"- {service} {endpoint}: Failed with status {status}")
        
        return 1


if __name__ == "__main__":
    sys.exit(main())