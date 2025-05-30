"""
Event bus utilities for the SyncService.

This module provides functions to connect to NATS and publish/subscribe to events.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

import nats
from nats.aio.client import Client as NATS
from nats.aio.errors import ErrConnectionClosed, ErrTimeout

from syncservice.config import get_settings

logger = logging.getLogger(__name__)

# NATS client
nats_client: Optional[NATS] = None

# Subscription callbacks
subscriptions: Dict[str, List[Callable]] = {}


async def init_nats_connection() -> None:
    """
    Initialize the connection to NATS.
    """
    global nats_client
    
    settings = get_settings()
    
    try:
        logger.info(f"Connecting to NATS: {settings.nats_url}")
        
        # Create NATS client
        nats_client = NATS()
        
        # Connect to NATS server
        await nats_client.connect(
            servers=[settings.nats_url],
            reconnect_time_wait=1,
            max_reconnect_attempts=60,
            name="syncservice-client"
        )
        
        logger.info("NATS connection initialized successfully")
        
        # Set up a reconnect handler
        nats_client.add_reconnect_callback(_on_reconnect)
        
        # Set up a disconnect handler
        nats_client.add_closed_callback(_on_disconnect)
        
        # Resubscribe to topics if reconnected
        await _resubscribe()
        
    except Exception as e:
        logger.error(f"Failed to initialize NATS connection: {str(e)}")
        nats_client = None


async def close_nats_connection() -> None:
    """
    Close the NATS connection.
    """
    global nats_client
    
    if nats_client:
        try:
            logger.info("Closing NATS connection")
            await nats_client.drain()
            await nats_client.close()
            nats_client = None
            logger.info("NATS connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing NATS connection: {str(e)}")


async def publish_event(topic: str, data: Dict[str, Any]) -> bool:
    """
    Publish an event to NATS.
    
    Args:
        topic: NATS topic/subject to publish to
        data: Event data (will be serialized to JSON)
        
    Returns:
        True if the event was published successfully, False otherwise
    """
    global nats_client
    
    if not nats_client:
        try:
            await init_nats_connection()
        except Exception as e:
            logger.error(f"Failed to initialize NATS connection for publishing: {str(e)}")
            return False
    
    try:
        # Add timestamp if not present
        if "timestamp" not in data:
            data["timestamp"] = datetime.utcnow().isoformat()
            
        # Serialize the data to JSON
        payload = json.dumps(data).encode()
        
        # Publish the message
        prefixed_topic = f"terrafusion.syncservice.{topic}"
        await nats_client.publish(prefixed_topic, payload)
        logger.debug(f"Published event to {prefixed_topic}: {data}")
        return True
        
    except ErrConnectionClosed:
        logger.error("NATS connection closed while publishing event, attempting to reconnect")
        try:
            await init_nats_connection()
            # Retry the publish
            prefixed_topic = f"terrafusion.syncservice.{topic}"
            await nats_client.publish(prefixed_topic, json.dumps(data).encode())
            logger.debug(f"Published event to {prefixed_topic} after reconnection: {data}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event after reconnection: {str(e)}")
            return False
    except Exception as e:
        logger.error(f"Error publishing event to {topic}: {str(e)}")
        return False


async def subscribe(topic: str, callback: Callable) -> bool:
    """
    Subscribe to a NATS topic.
    
    Args:
        topic: NATS topic/subject to subscribe to
        callback: Async function to call when a message is received
        
    Returns:
        True if the subscription was successful, False otherwise
    """
    global nats_client, subscriptions
    
    if not nats_client:
        try:
            await init_nats_connection()
        except Exception as e:
            logger.error(f"Failed to initialize NATS connection for subscription: {str(e)}")
            return False
    
    try:
        # Add to subscriptions dict for reconnection purposes
        if topic not in subscriptions:
            subscriptions[topic] = []
        subscriptions[topic].append(callback)
        
        # Subscribe to the topic
        prefixed_topic = f"terrafusion.syncservice.{topic}"
        await nats_client.subscribe(
            prefixed_topic,
            cb=lambda msg: _handle_message(msg, callback)
        )
        
        logger.info(f"Subscribed to NATS topic: {prefixed_topic}")
        return True
        
    except Exception as e:
        logger.error(f"Error subscribing to NATS topic {topic}: {str(e)}")
        return False


async def _handle_message(msg, callback: Callable) -> None:
    """
    Handle a message received from NATS.
    
    Args:
        msg: NATS message object
        callback: Callback function to process the message
    """
    try:
        # Parse the JSON payload
        data = json.loads(msg.data.decode())
        
        # Call the callback function
        await callback(data)
        
    except json.JSONDecodeError:
        logger.error(f"Received invalid JSON in NATS message: {msg.data.decode()}")
    except Exception as e:
        logger.error(f"Error handling NATS message: {str(e)}")


async def _resubscribe() -> None:
    """
    Resubscribe to all topics after a reconnection.
    """
    global nats_client, subscriptions
    
    if not nats_client or not subscriptions:
        return
    
    logger.info("Resubscribing to NATS topics")
    
    for topic, callbacks in subscriptions.items():
        prefixed_topic = f"terrafusion.syncservice.{topic}"
        
        for callback in callbacks:
            try:
                await nats_client.subscribe(
                    prefixed_topic,
                    cb=lambda msg: _handle_message(msg, callback)
                )
                logger.info(f"Resubscribed to NATS topic: {prefixed_topic}")
            except Exception as e:
                logger.error(f"Error resubscribing to NATS topic {prefixed_topic}: {str(e)}")


def _on_reconnect() -> None:
    """
    Callback function when NATS reconnects.
    """
    logger.info("Reconnected to NATS server")
    
    # Schedule resubscription
    asyncio.create_task(_resubscribe())


def _on_disconnect() -> None:
    """
    Callback function when NATS disconnects.
    """
    logger.warning("Disconnected from NATS server")


async def check_nats_connection() -> bool:
    """
    Check if the NATS connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    global nats_client
    
    if not nats_client:
        try:
            await init_nats_connection()
        except Exception:
            return False
    
    try:
        test_topic = "connection.test"
        test_data = {"timestamp": datetime.utcnow().isoformat(), "test": True}
        
        # Try to publish a test message
        result = await publish_event(test_topic, test_data)
        return result
    except Exception as e:
        logger.error(f"NATS connection check failed: {str(e)}")
        return False
