#!/usr/bin/env python
"""
WebSocket Client Test for TerraFusion SyncService

This script tests the WebSocket client connection from the perspective of the frontend,
simulating what a browser client would do. It verifies:

1. Connection to the WebSocket server
2. Message sending and receiving
3. Event subscription and handling
4. Automatic reconnection
5. Error handling

Usage:
    python test_websocket_client.py [--server URL] [--duration SECONDS]

Arguments:
    --server URL       WebSocket server URL (default: ws://localhost:8081/ws)
    --duration SEC     Test duration in seconds (default: 30)
"""

import os
import sys
import time
import json
import logging
import argparse
import asyncio
import websockets
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_WS_URL = "ws://localhost:8081/ws"
DEFAULT_DURATION = 30  # seconds

# Global state
received_messages = []
connected = False
connection_attempts = 0
last_connection_time = None
last_message_time = None

async def connect_websocket(url: str, timeout: int = 10) -> websockets.WebSocketClientProtocol:
    """
    Connect to the WebSocket server with timeout.
    
    Args:
        url: WebSocket server URL
        timeout: Connection timeout in seconds
        
    Returns:
        WebSocket connection
    
    Raises:
        asyncio.TimeoutError: If connection times out
        ConnectionError: If connection fails
    """
    global connected, connection_attempts, last_connection_time
    
    connection_attempts += 1
    logger.info(f"Connecting to WebSocket server at {url} (attempt {connection_attempts})...")
    
    try:
        # Connect with timeout
        websocket = await asyncio.wait_for(
            websockets.connect(url, ping_interval=None),
            timeout=timeout
        )
        
        connected = True
        last_connection_time = datetime.now()
        logger.info(f"Connected to WebSocket server at {url}")
        
        return websocket
    except asyncio.TimeoutError:
        logger.error(f"Connection timed out after {timeout} seconds")
        connected = False
        raise
    except Exception as e:
        logger.error(f"Connection failed: {str(e)}")
        connected = False
        raise ConnectionError(f"Failed to connect: {str(e)}")

async def send_ping(websocket: websockets.WebSocketClientProtocol) -> bool:
    """
    Send a ping message to the WebSocket server.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        True if ping was successful, False otherwise
    """
    try:
        ping_message = json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()})
        await websocket.send(ping_message)
        logger.info(f"Sent ping message: {ping_message}")
        return True
    except Exception as e:
        logger.error(f"Error sending ping: {str(e)}")
        return False

async def subscribe_to_events(websocket: websockets.WebSocketClientProtocol) -> bool:
    """
    Subscribe to sync operation events.
    
    Args:
        websocket: WebSocket connection
        
    Returns:
        True if subscription was successful, False otherwise
    """
    try:
        subscription_message = json.dumps({
            "type": "subscribe",
            "events": ["sync_operation_update", "sync_pair_update", "system_status"]
        })
        await websocket.send(subscription_message)
        logger.info(f"Sent subscription request: {subscription_message}")
        return True
    except Exception as e:
        logger.error(f"Error subscribing to events: {str(e)}")
        return False

async def receive_messages(websocket: websockets.WebSocketClientProtocol, 
                         stop_event: asyncio.Event) -> None:
    """
    Receive and process messages from the WebSocket server.
    
    Args:
        websocket: WebSocket connection
        stop_event: Event to signal when to stop receiving messages
    """
    global received_messages, last_message_time
    
    while not stop_event.is_set():
        try:
            # Set a timeout to periodically check the stop event
            message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
            
            # Process the message
            try:
                message_data = json.loads(message)
                received_messages.append(message_data)
                last_message_time = datetime.now()
                
                logger.info(f"Received message: {message}")
                
                # Handle specific message types
                msg_type = message_data.get("type")
                if msg_type == "pong":
                    logger.info("Received pong response")
                elif msg_type == "subscription_confirmed":
                    logger.info("Subscription confirmed")
                elif msg_type == "sync_operation_update":
                    op_id = message_data.get("data", {}).get("id")
                    op_status = message_data.get("data", {}).get("status")
                    logger.info(f"Sync operation update: {op_id} - {op_status}")
                
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message: {message}")
            
        except asyncio.TimeoutError:
            # This is expected due to the timeout we set
            continue
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            break
        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            break

async def reconnection_loop(url: str, max_retries: int = 5, 
                          retry_delay: int = 2,
                          test_duration: int = DEFAULT_DURATION) -> None:
    """
    Main connection loop with automatic reconnection.
    
    Args:
        url: WebSocket server URL
        max_retries: Maximum number of reconnection attempts
        retry_delay: Delay between reconnection attempts in seconds
        test_duration: Total test duration in seconds
    """
    global connected
    
    stop_event = asyncio.Event()
    retry_count = 0
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=test_duration)
    
    # Set up signal handling
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: stop_event.set())
    
    logger.info(f"Starting WebSocket client test (duration: {test_duration} seconds)...")
    
    while datetime.now() < end_time and not stop_event.is_set():
        try:
            # Connect to WebSocket server
            websocket = await connect_websocket(url)
            
            # Reset retry count on successful connection
            retry_count = 0
            
            # Subscribe to events
            await subscribe_to_events(websocket)
            
            # Set up message receiving task
            receiver_task = asyncio.create_task(receive_messages(websocket, stop_event))
            
            # Send periodic pings while connected
            ping_interval = 5  # seconds
            next_ping_time = datetime.now()
            
            while datetime.now() < end_time and not stop_event.is_set():
                # Check if it's time to send a ping
                if datetime.now() >= next_ping_time:
                    await send_ping(websocket)
                    next_ping_time = datetime.now() + timedelta(seconds=ping_interval)
                
                # Check if we should still be running
                if datetime.now() >= end_time:
                    logger.info("Test duration completed")
                    stop_event.set()
                    break
                
                # Wait a bit before the next iteration
                await asyncio.sleep(0.1)
            
            # Close the connection cleanly
            await websocket.close()
            
        except ConnectionError:
            # Handle connection failures
            retry_count += 1
            
            if retry_count > max_retries:
                logger.error(f"Maximum retry count ({max_retries}) exceeded")
                break
            
            logger.info(f"Retrying in {retry_delay} seconds (attempt {retry_count}/{max_retries})...")
            await asyncio.sleep(retry_delay)
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            break
    
    # Make sure the stop event is set
    stop_event.set()
    
    # Print test summary
    print_test_summary()

def print_test_summary():
    """Print a summary of the WebSocket client test."""
    global received_messages, connection_attempts, connected
    
    print("\n============================================")
    print("  WEBSOCKET CLIENT TEST RESULTS")
    print("============================================")
    
    # Connection stats
    print(f"Connection attempts: {connection_attempts}")
    print(f"Final connection state: {'Connected' if connected else 'Disconnected'}")
    
    if last_connection_time:
        print(f"Last connection time: {last_connection_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Message stats
    message_count = len(received_messages)
    print(f"Messages received: {message_count}")
    
    if last_message_time:
        print(f"Last message time: {last_message_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Message type breakdown
    if message_count > 0:
        message_types = {}
        for message in received_messages:
            msg_type = message.get("type", "unknown")
            if msg_type in message_types:
                message_types[msg_type] += 1
            else:
                message_types[msg_type] = 1
        
        print("\nMessage types received:")
        for msg_type, count in message_types.items():
            print(f"  {msg_type}: {count}")
    
    # Test result
    if connected and message_count > 0:
        print("\n✅ WebSocket client test PASSED")
        print("   Successfully connected and received messages")
    elif connected:
        print("\n⚠️ WebSocket client test PARTIAL SUCCESS")
        print("   Connected but did not receive any messages")
    else:
        print("\n❌ WebSocket client test FAILED")
        print("   Could not establish a stable connection")
    
    print("============================================\n")

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test WebSocket client for TerraFusion SyncService")
    parser.add_argument("--server", default=DEFAULT_WS_URL, help=f"WebSocket server URL (default: {DEFAULT_WS_URL})")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION, help=f"Test duration in seconds (default: {DEFAULT_DURATION})")
    args = parser.parse_args()
    
    try:
        # Run the async test
        asyncio.run(reconnection_loop(args.server, test_duration=args.duration))
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()