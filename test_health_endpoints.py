"""
Test script to verify the health check endpoints.

This script tests the health check endpoints of both the API Gateway and SyncService
to ensure they're providing accurate and consistent information.
"""
import requests
import logging
import sys
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Endpoints to test
API_GATEWAY = "http://0.0.0.0:5000"
SYNCSERVICE = "http://0.0.0.0:8080"

def test_api_gateway_health_endpoints():
    """Test all health-related endpoints of the API Gateway."""
    endpoints = [
        '/api/status',
        '/health/live',
        '/health/ready'
    ]
    
    results = {}
    all_successful = True
    
    for endpoint in endpoints:
        try:
            url = f"{API_GATEWAY}{endpoint}"
            logger.info(f"Testing API Gateway endpoint: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code in (200, 503):  # 503 is acceptable for readiness check
                logger.info(f"✅ Endpoint {endpoint} returned status {response.status_code}")
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response": response.json()
                }
            else:
                logger.error(f"❌ Endpoint {endpoint} returned unexpected status {response.status_code}")
                all_successful = False
                results[endpoint] = {
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"❌ Error accessing endpoint {endpoint}: {str(e)}")
            all_successful = False
            results[endpoint] = {
                "error": str(e)
            }
    
    return all_successful, results

def test_syncservice_health_endpoints():
    """Test all health-related endpoints of the SyncService."""
    endpoints = [
        '/health',
        '/health/live',
        '/health/ready'
    ]
    
    results = {}
    all_successful = True
    
    for endpoint in endpoints:
        try:
            url = f"{SYNCSERVICE}{endpoint}"
            logger.info(f"Testing SyncService endpoint: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code in (200, 503):  # 503 is acceptable for readiness check
                logger.info(f"✅ Endpoint {endpoint} returned status {response.status_code}")
                results[endpoint] = {
                    "status_code": response.status_code,
                    "response": response.json()
                }
            else:
                logger.error(f"❌ Endpoint {endpoint} returned unexpected status {response.status_code}")
                all_successful = False
                results[endpoint] = {
                    "status_code": response.status_code,
                    "error": f"Unexpected status code: {response.status_code}"
                }
        except Exception as e:
            logger.error(f"❌ Error accessing endpoint {endpoint}: {str(e)}")
            all_successful = False
            results[endpoint] = {
                "error": str(e)
            }
    
    return all_successful, results

def main():
    """Main function to run the tests."""
    logger.info("Testing health endpoints...")
    
    # Test API Gateway health endpoints
    api_success, api_results = test_api_gateway_health_endpoints()
    
    # Test SyncService health endpoints
    sync_success, sync_results = test_syncservice_health_endpoints()
    
    # Print detailed results
    logger.info("\n===== API Gateway Health Endpoints =====")
    for endpoint, result in api_results.items():
        if 'error' in result:
            logger.info(f"{endpoint}: ERROR - {result['error']}")
        else:
            status = result['status_code']
            resp = json.dumps(result['response'], indent=2)
            logger.info(f"{endpoint}: {status}\n{resp}")
    
    logger.info("\n===== SyncService Health Endpoints =====")
    for endpoint, result in sync_results.items():
        if 'error' in result:
            logger.info(f"{endpoint}: ERROR - {result['error']}")
        else:
            status = result['status_code']
            resp = json.dumps(result['response'], indent=2)
            logger.info(f"{endpoint}: {status}\n{resp}")
    
    # Summarize results
    if api_success and sync_success:
        logger.info("\n✅ All health endpoints are working correctly!")
        return 0
    else:
        logger.error("\n❌ Some health endpoints failed. See logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())