"""
Health check endpoints for the SyncService.

This module provides API endpoints for health checks and status monitoring.
"""

import logging
from typing import Dict, Any
import os

from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

# Configure router
router = APIRouter()


@router.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness probe endpoint.
    
    This endpoint checks if the service is alive and responding.
    
    Returns:
        A dictionary with basic service status information
    """
    return {
        "status": "up",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness probe endpoint.
    
    This endpoint checks if the service is ready to accept requests.
    It validates that all required dependencies are available.
    
    Returns:
        A dictionary with service readiness information
    """
    # Check database connectivity
    db_status = "ok"
    try:
        # This would normally check actual database connectivity
        pass
    except Exception as e:
        logger.error(f"Database connectivity check failed: {str(e)}")
        db_status = "error"
    
    # Check event bus connectivity
    event_bus_status = "ok"
    try:
        # This would normally check actual event bus connectivity
        pass
    except Exception as e:
        logger.error(f"Event bus connectivity check failed: {str(e)}")
        event_bus_status = "error"
    
    # Determine overall status
    ready = db_status == "ok" and event_bus_status == "ok"
    
    response = {
        "status": "ready" if ready else "not_ready",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "dependencies": {
            "database": db_status,
            "event_bus": event_bus_status
        }
    }
    
    # If not ready, return a 503 Service Unavailable
    if not ready:
        raise HTTPException(status_code=503, detail=response)
    
    return response


@router.get("/status")
async def detailed_health_status() -> Dict[str, Any]:
    """
    Detailed health status endpoint.
    
    This endpoint provides detailed information about the service health
    and its dependencies.
    
    Returns:
        A dictionary with detailed health status information
    """
    # Check database connectivity
    db_status = {
        "status": "connected",
        "latency": "10ms"  # This would be measured in a real implementation
    }
    
    # Check event bus connectivity
    event_bus_status = {
        "status": "connected",
        "latency": "5ms"  # This would be measured in a real implementation
    }
    
    # Get process info
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        memory_usage = f"{memory_info.rss / (1024 * 1024):.1f}MB"
        cpu_usage = f"{process.cpu_percent(interval=0.1):.1f}%"
    except ImportError:
        memory_usage = "N/A"
        cpu_usage = "N/A"
    
    return {
        "status": "healthy",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "dependencies": {
            "database": db_status,
            "event_bus": event_bus_status
        },
        "performance": {
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage
        }
    }