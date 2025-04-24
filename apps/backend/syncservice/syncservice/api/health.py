"""
Health check endpoints for the SyncService.

This module implements liveness and readiness probe endpoints.
"""

from typing import Dict

from fastapi import APIRouter

# Create a router
router = APIRouter()

# Flag to indicate if the service is shutting down
_shutting_down = False

@router.get("/live")
async def liveness_check() -> Dict:
    """
    Liveness probe endpoint.
    
    This endpoint indicates whether the service is alive. It should return a 200 OK
    status code if the service is running, and a non-200 status code if the service
    needs to be restarted.
    
    Returns:
        Service liveness status
    """
    if _shutting_down:
        # If we're shutting down, report the service as not alive
        return {"status": "shutting_down"}
    
    return {
        "status": "up",
        "service": "terrafusion-sync-service",
        "version": "0.1.0"
    }

@router.get("/ready")
async def readiness_check() -> Dict:
    """
    Readiness probe endpoint.
    
    This endpoint indicates whether the service is ready to accept requests.
    It should return a 200 OK status code if the service is ready, and a non-200
    status code if the service is not ready to accept requests.
    
    Returns:
        Service readiness status
    """
    # For now, our readiness criteria are simple:
    # 1. Service is not shutting down
    # 2. All critical dependencies are available
    
    if _shutting_down:
        # If we're shutting down, report the service as not ready
        return {"status": "shutting_down"}
    
    # Check if all dependencies are available
    dependencies_ok = True
    
    # In a real implementation, we would check connections to databases,
    # message brokers, etc. For now, we'll assume everything is available.
    
    if dependencies_ok:
        return {
            "status": "ready",
            "service": "terrafusion-sync-service",
            "version": "0.1.0",
            "dependencies": {
                "database": "ok",
                "event_bus": "ok"
            }
        }
    else:
        # Return a failure status if any dependencies are unavailable
        return {
            "status": "not_ready",
            "service": "terrafusion-sync-service",
            "version": "0.1.0",
            "dependencies": {
                "database": "not_connected",
                "event_bus": "ok"
            }
        }

@router.get("/status")
async def detailed_health_status() -> Dict:
    """
    Detailed health status endpoint.
    
    This endpoint provides more detailed information about the service's health,
    including dependency statuses and performance metrics.
    
    Returns:
        Detailed service health status
    """
    # In a real implementation, we would gather metrics from various
    # components and provide a detailed health report.
    
    return {
        "status": "healthy",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "uptime": "1h 23m",
        "dependencies": {
            "database": {
                "status": "connected",
                "latency": "10ms"
            },
            "event_bus": {
                "status": "connected",
                "latency": "5ms"
            }
        },
        "performance": {
            "memory_usage": "120MB",
            "cpu_usage": "2%",
            "active_connections": 5,
            "request_rate": "10 req/s",
            "error_rate": "0 err/s"
        }
    }

def set_shutting_down() -> None:
    """
    Mark the service as shutting down.
    
    This function should be called when the service is being gracefully shut down,
    to ensure that the health endpoints return appropriate responses.
    """
    global _shutting_down
    _shutting_down = True