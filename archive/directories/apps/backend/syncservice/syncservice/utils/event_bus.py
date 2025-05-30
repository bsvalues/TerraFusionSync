"""
Event bus utilities for SyncService.

This module provides utilities for publishing and subscribing to events through
an event bus (NATS).
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Flag to track if NATS connection is available
_nats_available = False

async def init_event_bus():
    """
    Initialize connection to the event bus.
    
    In a real implementation, this would connect to NATS. For now, we'll just
    log events locally.
    """
    global _nats_available
    try:
        # In a real implementation, this would be:
        # nc = await nats.connect(config.nats_url)
        # js = nc.jetstream()
        
        # For now, just set the flag to simulate a connection
        _nats_available = True
        
        logger.info("Event bus connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize event bus connection: {str(e)}")
        _nats_available = False


async def publish_event(event_type: str, data: Dict[str, Any]) -> bool:
    """
    Publish an event to the event bus.
    
    Args:
        event_type: Type of event to publish
        data: Event data
        
    Returns:
        True if event was published successfully, False otherwise
    """
    if not _nats_available:
        # Try to initialize connection
        await init_event_bus()
        
    try:
        # Create event payload
        payload = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # In a real implementation, this would be:
        # await js.publish(f"terrafusion.syncservice.{event_type}", json.dumps(payload).encode())
        
        # For now, just log the event
        logger.info(f"Event published: {event_type} - {json.dumps(payload)}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to publish event {event_type}: {str(e)}")
        return False


async def check_event_bus() -> bool:
    """
    Check if the event bus connection is active.
    
    Returns:
        True if connection is active, False otherwise
    """
    if not _nats_available:
        await init_event_bus()
    
    return _nats_available