"""
TerraFusion SyncService WebSocket Server

This module provides a WebSocket server that broadcasts real-time updates
about sync operations to connected clients.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Set, Any

import aiohttp
from aiohttp import web

from logging_config import configure_logger

# Import health check routes
try:
    from syncservice_websocket_health import add_health_routes
    HEALTH_ROUTES_AVAILABLE = True
except ImportError:
    logger = logging.getLogger('syncservice_websocket')
    logger.warning('Health check routes not available')
    HEALTH_ROUTES_AVAILABLE = False

# Import models directly from apps backend
try:
    from apps.backend.models import SyncOperation, AuditEntry
    from apps.backend.database import db
except ImportError:
    # Fallback for development or standalone mode
    try:
        from models import SyncOperation, AuditEntry, db
    except ImportError:
        logging.error("Could not import database models. WebSocket server may not function correctly.")
        
        # Create placeholder classes for type checking
        class SyncOperation:
            operation_id: int
            sync_pair_id: int
            status: str
            sync_type: str
            started_at: datetime
            completed_at: datetime
            total_records: int
            processed_records: int
            successful_records: int
            failed_records: int
            error_message: str
            created_at: datetime
            updated_at: datetime
            
        class AuditEntry:
            audit_id: int
            event_type: str
            resource_type: str
            resource_id: str
            operation_id: int
            description: str
            severity: str
            created_at: datetime
            
        class db:
            @staticmethod
            async def Session():
                class AsyncSession:
                    async def __aenter__(self):
                        return self
                    
                    async def __aexit__(self, exc_type, exc_val, exc_tb):
                        pass
                    
                    async def execute(self, query):
                        class ScalarResult:
                            def scalars(self):
                                return self
                            
                            def all(self):
                                return []
                            
                            def scalar_one_or_none(self):
                                return None
                        
                        return ScalarResult()
                
                return AsyncSession()

# Configure logging
logger = configure_logger("syncservice_websocket")

# Store connected WebSocket clients
connected_clients: Set[web.WebSocketResponse] = set()

# Operation cache to reduce database queries
operation_cache: Dict[int, Dict[str, Any]] = {}

# Interval for checking updates (seconds)
UPDATE_CHECK_INTERVAL = 2


async def websocket_handler(request):
    """
    Handle WebSocket connections for real-time updates.
    
    Args:
        request: aiohttp request object
        
    Returns:
        WebSocketResponse object
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    logger.info(f"WebSocket client connected, total clients: {len(connected_clients) + 1}")
    connected_clients.add(ws)
    
    try:
        # Send initial data for all active operations
        await send_initial_data(ws)
        
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    # Handle subscription to specific operation updates
                    if data.get('action') == 'subscribe' and data.get('operation_id'):
                        await send_operation_data(ws, data['operation_id'])
                    
                    # Handle unsubscription from specific operation updates
                    elif data.get('action') == 'unsubscribe' and data.get('operation_id'):
                        # Simply acknowledge the unsubscription
                        # (server still sends broadcasts to all clients)
                        await ws.send_json({
                            'type': 'unsubscribe_ack',
                            'operation_id': data['operation_id']
                        })
                        
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {msg.data}")
                    
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.error(f"WebSocket connection closed with exception: {ws.exception()}")
                break
                
    finally:
        connected_clients.discard(ws)
        logger.info(f"WebSocket client disconnected, remaining clients: {len(connected_clients)}")
        
    return ws


async def send_initial_data(ws: web.WebSocketResponse):
    """
    Send initial data about active operations to a newly connected client.
    
    Args:
        ws: WebSocketResponse object for the client connection
    """
    try:
        # Get all active operations from the database
        async with db.Session() as session:
            active_ops = await session.execute(
                select(SyncOperation).where(
                    SyncOperation.status.in_(['running', 'pending'])
                )
            )
            operations = active_ops.scalars().all()
            
            # Send data for each active operation
            for op in operations:
                op_data = operation_to_dict(op)
                await ws.send_json({
                    'type': 'operation_update',
                    'data': op_data
                })
                
                # Update the cache
                operation_cache[op.operation_id] = op_data
                
    except Exception as e:
        logger.error(f"Error sending initial data: {str(e)}")


async def send_operation_data(ws: web.WebSocketResponse, operation_id: int):
    """
    Send data for a specific operation to a client.
    
    Args:
        ws: WebSocketResponse object for the client connection
        operation_id: ID of the operation to send data for
    """
    try:
        # First check cache
        if operation_id in operation_cache:
            await ws.send_json({
                'type': 'operation_update',
                'data': operation_cache[operation_id]
            })
            return
            
        # If not in cache, get from database
        async with db.Session() as session:
            op = await session.execute(
                select(SyncOperation).where(SyncOperation.operation_id == operation_id)
            )
            operation = op.scalar_one_or_none()
            
            if operation:
                op_data = operation_to_dict(operation)
                await ws.send_json({
                    'type': 'operation_update',
                    'data': op_data
                })
                
                # Update the cache
                operation_cache[operation_id] = op_data
            else:
                # Operation not found
                await ws.send_json({
                    'type': 'error',
                    'message': f"Operation {operation_id} not found"
                })
                
    except Exception as e:
        logger.error(f"Error sending operation data: {str(e)}")
        await ws.send_json({
            'type': 'error',
            'message': f"Error retrieving operation data: {str(e)}"
        })


def operation_to_dict(operation: SyncOperation) -> Dict[str, Any]:
    """
    Convert a SyncOperation object to a dictionary for JSON serialization.
    
    Args:
        operation: SyncOperation object
        
    Returns:
        Dictionary representation of the operation
    """
    return {
        'operation_id': operation.operation_id,
        'sync_pair_id': operation.sync_pair_id,
        'status': operation.status,
        'sync_type': operation.sync_type,
        'started_at': operation.started_at.isoformat() if operation.started_at else None,
        'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
        'total_records': operation.total_records,
        'processed_records': operation.processed_records,
        'successful_records': operation.successful_records,
        'failed_records': operation.failed_records,
        'error_message': operation.error_message,
        'created_at': operation.created_at.isoformat() if operation.created_at else None,
        'updated_at': operation.updated_at.isoformat() if operation.updated_at else None
    }


async def check_for_updates():
    """
    Periodically check for operation updates and broadcast them to connected clients.
    """
    while True:
        try:
            if connected_clients:  # Only query if there are connected clients
                async with db.Session() as session:
                    # Get all active operations
                    active_ops = await session.execute(
                        select(SyncOperation).where(
                            SyncOperation.status.in_(['running', 'pending'])
                        )
                    )
                    operations = active_ops.scalars().all()
                    
                    # Check for updates and broadcast changes
                    for op in operations:
                        op_dict = operation_to_dict(op)
                        
                        # Check if the operation is in cache and has changed
                        if op.operation_id in operation_cache:
                            old_data = operation_cache[op.operation_id]
                            if op_dict != old_data:
                                # Data has changed, broadcast update
                                await broadcast_update(op_dict)
                                # Update cache
                                operation_cache[op.operation_id] = op_dict
                        else:
                            # New operation, broadcast and cache
                            await broadcast_update(op_dict)
                            operation_cache[op.operation_id] = op_dict
                    
                    # Check for completed operations
                    completed_ops = await session.execute(
                        select(SyncOperation).where(
                            SyncOperation.operation_id.in_(list(operation_cache.keys())),
                            SyncOperation.status.in_(['completed', 'failed', 'cancelled'])
                        )
                    )
                    completed = completed_ops.scalars().all()
                    
                    # Broadcast updates for recently completed operations
                    for op in completed:
                        op_dict = operation_to_dict(op)
                        if op.operation_id in operation_cache:
                            old_data = operation_cache[op.operation_id]
                            if op_dict != old_data:
                                await broadcast_update(op_dict)
                                # Keep in cache for a while before removing
                                operation_cache[op.operation_id] = op_dict
                    
                    # Clean up old completed operations from cache
                    # (This helps reduce memory usage over time)
                    current_time = datetime.utcnow()
                    for op_id in list(operation_cache.keys()):
                        op_data = operation_cache[op_id]
                        if op_data['status'] in ['completed', 'failed', 'cancelled']:
                            if op_data['completed_at']:
                                completed_time = datetime.fromisoformat(op_data['completed_at'].replace('Z', '+00:00'))
                                # Remove from cache if completed more than 1 hour ago
                                if (current_time - completed_time).total_seconds() > 3600:
                                    del operation_cache[op_id]
                    
                    # Get recent audit entries
                    recent_audits = await session.execute(
                        select(AuditEntry)
                        .where(AuditEntry.event_type.in_(['sync_started', 'sync_completed', 'sync_failed']))
                        .order_by(AuditEntry.created_at.desc())
                        .limit(5)
                    )
                    
                    audits = recent_audits.scalars().all()
                    
                    # Broadcast audit notifications
                    for audit in audits:
                        # Check if this is a new audit entry (within last 10 seconds)
                        if (datetime.utcnow() - audit.created_at).total_seconds() < 10:
                            await broadcast_audit(audit)
            
        except Exception as e:
            logger.error(f"Error in update checker: {str(e)}")
            
        # Wait before checking for updates again
        await asyncio.sleep(UPDATE_CHECK_INTERVAL)


async def broadcast_update(operation_data: Dict[str, Any]):
    """
    Broadcast an operation update to all connected clients.
    
    Args:
        operation_data: Dictionary containing operation data
    """
    if not connected_clients:
        return
        
    message = {
        'type': 'operation_update',
        'data': operation_data
    }
    
    # Send update to all connected clients
    disconnected_clients = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Error sending update to client: {str(e)}")
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        connected_clients.discard(client)


async def broadcast_audit(audit: AuditEntry):
    """
    Broadcast an audit notification to all connected clients.
    
    Args:
        audit: AuditEntry object
    """
    if not connected_clients:
        return
        
    message = {
        'type': 'audit_notification',
        'data': {
            'audit_id': audit.audit_id,
            'event_type': audit.event_type,
            'resource_type': audit.resource_type,
            'resource_id': audit.resource_id,
            'operation_id': audit.operation_id,
            'description': audit.description,
            'severity': audit.severity,
            'created_at': audit.created_at.isoformat() if audit.created_at else None
        }
    }
    
    # Send notification to all connected clients
    disconnected_clients = set()
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception as e:
            logger.error(f"Error sending notification to client: {str(e)}")
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        connected_clients.discard(client)


async def start_websocket_server():
    """
    Start the WebSocket server.
    """
    # Create the aiohttp application
    app = web.Application()

    # Add health check routes if available
    if HEALTH_ROUTES_AVAILABLE:
        add_health_routes(app)
    
    # Add routes
    app.router.add_get('/ws', websocket_handler)
    
    # Set up background task for checking updates
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Get port from environment or use default
    port = int(os.environ.get('WEBSOCKET_PORT', 8081))
    
    # Start the WebSocket server
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"WebSocket server started on port {port}")
    
    # Start the update checker
    update_checker_task = asyncio.create_task(check_for_updates())
    
    return app, runner, update_checker_task


def main():
    """Main entry point for the WebSocket server."""
    loop = asyncio.get_event_loop()
    
    # Start WebSocket server
    app, runner, update_checker = loop.run_until_complete(start_websocket_server())
    
    try:
        # Run forever
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down WebSocket server...")
    finally:
        # Clean up
        loop.run_until_complete(runner.cleanup())
        update_checker.cancel()
        loop.close()


if __name__ == "__main__":
    main()