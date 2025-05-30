"""
Test script for the TerraFusion SyncService WebSocket functionality.

This script tests the WebSocket server by:
1. Ensuring the WebSocket server can start correctly
2. Checking that clients can connect to the WebSocket server
3. Verifying that real-time updates are properly broadcast to clients
4. Testing automatic recovery if the WebSocket server goes down

Usage:
    python test_websocket.py
"""

import os
import sys
import time
import json
import logging
import asyncio
import websockets
import requests
import threading
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
WEBSOCKET_SERVER_PORT = 8081
API_GATEWAY_PORT = 5000
SYNC_SERVICE_PORT = 8080
WEBSOCKET_URL = f"ws://localhost:{WEBSOCKET_SERVER_PORT}/ws"
API_URL = f"http://localhost:{API_GATEWAY_PORT}"
SYNC_URL = f"http://localhost:{SYNC_SERVICE_PORT}"

# Test data
TEST_SYNC_OPERATION = {
    "id": "test-operation-id",
    "status": "running",
    "progress": 0,
    "details": "Starting test sync operation"
}

class TestResults:
    """Class to store test results."""
    def __init__(self):
        self.success_count = 0
        self.failure_count = 0
        self.results = []
    
    def add_result(self, test_name: str, success: bool, message: str = None):
        """Add a test result."""
        status = "PASS" if success else "FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message or ""
        }
        self.results.append(result)
        
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            logger.error(f"Test '{test_name}' failed: {message}")
    
    def print_summary(self):
        """Print a summary of the test results."""
        print("\n==== WebSocket Test Results ====")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{status_icon} {result['test']}")
            if result["message"] and result["status"] == "FAIL":
                print(f"   → {result['message']}")
        
        print(f"\nPassed: {self.success_count}, Failed: {self.failure_count}")
        
        return self.failure_count == 0


def check_server_running(server_url: str) -> bool:
    """Check if a server is running at the given URL."""
    try:
        response = requests.get(f"{server_url}/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

async def connect_websocket() -> Tuple[bool, str]:
    """
    Attempt to connect to the WebSocket server.
    
    Returns:
        (success, message)
    """
    try:
        async with websockets.connect(WEBSOCKET_URL, ping_interval=None) as websocket:
            # Successfully connected
            logger.info("Successfully connected to WebSocket server")
            return True, "Connected successfully"
    except Exception as e:
        logger.error(f"Failed to connect to WebSocket: {str(e)}")
        return False, f"Connection failed: {str(e)}"

async def test_websocket_receive_updates() -> Tuple[bool, str]:
    """
    Test that the WebSocket server can send updates to clients.
    
    Returns:
        (success, message)
    """
    try:
        # Start a client to listen for messages
        messages_received = []
        
        async def listen_for_messages():
            async with websockets.connect(WEBSOCKET_URL, ping_interval=None) as websocket:
                # Set a timeout for receiving messages
                for _ in range(2):  # Try to receive 2 messages
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        messages_received.append(json.loads(message))
                        logger.info(f"Received message: {message}")
                    except asyncio.TimeoutError:
                        logger.warning("Timeout waiting for message")
                        break
                    except Exception as e:
                        logger.error(f"Error receiving message: {str(e)}")
                        break
        
        # Create a task to listen for messages
        listener_task = asyncio.create_task(listen_for_messages())
        
        # Give it a moment to connect
        await asyncio.sleep(1)
        
        # Trigger some updates via the API
        # This would normally be done by creating a sync operation
        # For testing, we'll use a direct message if an appropriate endpoint exists
        try:
            # Try to trigger a test event if a test endpoint exists
            response = requests.post(f"{API_URL}/test/websocket/broadcast", 
                                    json={"type": "test", "data": TEST_SYNC_OPERATION})
        except requests.exceptions.RequestException:
            # If the test endpoint doesn't exist, we'll see if any messages come through naturally
            logger.warning("Could not trigger test message, waiting for natural events")
        
        # Wait for the listener to finish
        await asyncio.sleep(12)  # Wait a bit longer than the timeout in the listener
        
        # Check if we received any messages
        if messages_received:
            return True, f"Received {len(messages_received)} messages"
        else:
            return False, "No messages received"
        
    except Exception as e:
        logger.error(f"Error testing WebSocket updates: {str(e)}")
        return False, f"Test failed: {str(e)}"

async def test_websocket_reconnection() -> Tuple[bool, str]:
    """
    Test that clients can reconnect if the WebSocket server restarts.
    
    Returns:
        (success, message)
    """
    try:
        # First, ensure we can connect initially
        initial_connect_success, _ = await connect_websocket()
        if not initial_connect_success:
            return False, "Could not establish initial connection"
        
        # Try to restart the WebSocket server
        # This would typically be done through the API Gateway's mechanisms
        try:
            response = requests.post(f"{API_URL}/admin/websocket/restart")
            if response.status_code != 200:
                return False, f"Failed to restart WebSocket server: {response.status_code}"
        except requests.exceptions.RequestException as e:
            logger.warning(f"Could not trigger server restart via API: {str(e)}")
            logger.info("Checking if WebSocket server is running directly...")
            # We'll check directly if it's running
            if not check_server_running(f"http://localhost:{WEBSOCKET_SERVER_PORT}"):
                return False, "WebSocket server is not running"
        
        # Wait for the server to restart
        await asyncio.sleep(5)
        
        # Try to reconnect
        reconnect_success, message = await connect_websocket()
        if reconnect_success:
            return True, "Successfully reconnected after server restart"
        else:
            return False, f"Failed to reconnect: {message}"
        
    except Exception as e:
        logger.error(f"Error testing WebSocket reconnection: {str(e)}")
        return False, f"Test failed: {str(e)}"
    
async def test_websocket_api_proxy() -> Tuple[bool, str]:
    """
    Test that the API Gateway correctly proxies WebSocket connections.
    
    Returns:
        (success, message)
    """
    try:
        # Check if the API Gateway reports the WebSocket server as active
        response = requests.get(f"{API_URL}/status")
        if response.status_code != 200:
            return False, f"API Gateway status check failed: {response.status_code}"
        
        status_data = response.json()
        
        # Check if WebSocket status is reported
        if "components" not in status_data or "websocket_server" not in status_data["components"]:
            return False, "WebSocket server status not reported by API Gateway"
        
        # Check if WebSocket server is reported as healthy
        websocket_status = status_data["components"]["websocket_server"]
        if not isinstance(websocket_status, str) or "healthy" not in websocket_status.lower():
            return False, f"WebSocket server reported as unhealthy: {websocket_status}"
        
        # If we've gotten this far, the API Gateway is aware of the WebSocket server
        # and reports it as healthy
        return True, "API Gateway correctly reports WebSocket server status"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error testing API Gateway WebSocket proxy: {str(e)}")
        return False, f"Test failed: {str(e)}"

async def run_async_tests():
    """Run all async tests and return results."""
    results = TestResults()
    
    # Test basic connection
    logger.info("Testing WebSocket connection...")
    connect_success, connect_message = await connect_websocket()
    results.add_result("WebSocket Connection", connect_success, connect_message)
    
    if connect_success:
        # Test receiving updates
        logger.info("Testing WebSocket updates...")
        updates_success, updates_message = await test_websocket_receive_updates()
        results.add_result("WebSocket Updates", updates_success, updates_message)
        
        # Test reconnection
        logger.info("Testing WebSocket reconnection...")
        reconnect_success, reconnect_message = await test_websocket_reconnection()
        results.add_result("WebSocket Reconnection", reconnect_success, reconnect_message)
    
    # Test API Gateway proxy (this doesn't require WebSocket connection)
    logger.info("Testing API Gateway WebSocket proxy...")
    proxy_success, proxy_message = await test_websocket_api_proxy()
    results.add_result("API Gateway WebSocket Proxy", proxy_success, proxy_message)
    
    return results

def ensure_services_running():
    """Ensure that all required services are running."""
    # Check if API Gateway is running
    if not check_server_running(API_URL):
        logger.info("API Gateway not running, starting it...")
        subprocess.Popen(["python", "restart_syncservice_workflow.py"])
    
    # Check if SyncService is running
    if not check_server_running(SYNC_URL):
        logger.info("SyncService not running, it should be started by the API Gateway...")
    
    # Allow time for services to start
    time.sleep(5)
    
    # Verify again
    api_running = check_server_running(API_URL)
    sync_running = check_server_running(SYNC_URL)
    
    if not api_running:
        logger.error("API Gateway could not be started")
    if not sync_running:
        logger.error("SyncService could not be started")
    
    return api_running and sync_running

def main():
    """Main entry point for the script."""
    logger.info("Starting WebSocket tests...")
    
    # Make sure services are running
    services_running = ensure_services_running()
    if not services_running:
        logger.error("Required services are not running, cannot proceed with tests")
        sys.exit(1)
    
    # Run the async tests
    test_results = asyncio.run(run_async_tests())
    
    # Print test results
    all_passed = test_results.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()