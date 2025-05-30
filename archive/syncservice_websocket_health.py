"""
TerraFusion SyncService WebSocket Health Check

This module provides health check endpoints for the WebSocket server.
"""

import logging
from aiohttp import web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def health_check(request):
    """
    Health check endpoint for the WebSocket server.
    
    Args:
        request: aiohttp request object
        
    Returns:
        JSON response with health status
    """
    return web.json_response({
        "status": "healthy",
        "service": "terrafusion_websocket",
        "version": "1.0.0"
    })

async def websocket_metrics(request):
    """
    Metrics endpoint for the WebSocket server.
    
    Args:
        request: aiohttp request object
        
    Returns:
        JSON response with WebSocket metrics
    """
    # Import WebSocket metrics from the main module
    from syncservice_websocket import connected_clients, operation_cache
    
    # Collect metrics
    metrics = {
        "connected_clients": len(connected_clients),
        "cached_operations": len(operation_cache),
        "active_operations": len([op for op_id, op in operation_cache.items() 
                                 if op.get('status') in ['running', 'pending']])
    }
    
    return web.json_response(metrics)

def add_health_routes(app):
    """
    Add health check routes to the WebSocket server.
    
    Args:
        app: aiohttp Application instance
    """
    app.router.add_get('/health', health_check)
    app.router.add_get('/websocket-metrics', websocket_metrics)
    logger.info("Added health check and metrics endpoints to WebSocket server")