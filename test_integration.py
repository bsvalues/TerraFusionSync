"""
Test script to verify the integration between the API Gateway and SyncService.

This script performs a simple test to ensure that the API Gateway can
successfully communicate with the SyncService.
"""
import requests
import logging
import time
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Endpoints to test
API_GATEWAY = "http://0.0.0.0:5000"
SYNCSERVICE = "http://0.0.0.0:8080"

def test_api_gateway():
    """Test that the API Gateway is accessible."""
    try:
        response = requests.get(f"{API_GATEWAY}/api/status", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API Gateway is accessible!")
            return response.json()
        else:
            logger.error(f"❌ API Gateway returned status code {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.error(f"❌ Failed to connect to API Gateway: {str(e)}")
        return None

def test_syncservice_direct():
    """Test that the SyncService is directly accessible."""
    try:
        response = requests.get(f"{SYNCSERVICE}/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ SyncService is directly accessible!")
            return response.json()
        else:
            logger.error(f"❌ SyncService returned status code {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.error(f"❌ Failed to connect to SyncService: {str(e)}")
        return None

def test_api_gateway_proxy():
    """Test that the API Gateway can proxy requests to the SyncService."""
    try:
        response = requests.get(f"{API_GATEWAY}/api/health", timeout=5)
        if response.status_code == 200:
            logger.info("✅ API Gateway successfully proxied request to SyncService!")
            return response.json()
        else:
            logger.error(f"❌ API Gateway proxy returned status code {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.error(f"❌ Failed to connect to API Gateway proxy: {str(e)}")
        return None

def main():
    """Run the integration tests."""
    logger.info("Starting integration tests...")
    
    # Test API Gateway
    api_status = test_api_gateway()
    if not api_status:
        logger.error("API Gateway test failed. Cannot continue.")
        sys.exit(1)
    
    # Give services time to initialize if needed
    time.sleep(1)
    
    # Test SyncService directly
    sync_status = test_syncservice_direct()
    if not sync_status:
        logger.error("Direct SyncService test failed. Cannot continue.")
        sys.exit(1)
    
    # Test proxy functionality
    proxy_status = test_api_gateway_proxy()
    if not proxy_status:
        logger.error("API Gateway proxy test failed.")
        sys.exit(1)
    
    logger.info("✅ All tests passed! The integration is working correctly.")
    logger.info("\nAPI Gateway Status:")
    logger.info(f"  - API Gateway: {api_status['components']['api_gateway']}")
    logger.info(f"  - SyncService: {api_status['components']['sync_service']}")
    logger.info(f"  - Database: {api_status['components']['database']}")

if __name__ == "__main__":
    main()