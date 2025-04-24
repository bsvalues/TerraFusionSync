"""
Health check endpoints for the SyncService.

This module implements liveness and readiness probe endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter

from syncservice.utils.database import check_source_connection, check_target_connection
from syncservice.utils.event_bus import check_event_bus

logger = logging.getLogger(__name__)

# Configure router
router = APIRouter()

# Global variable to track if the service is shutting down
_shutting_down = False

# Track service startup time
_start_time = datetime.utcnow()


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
    return {
        "status": "up" if not _shutting_down else "shutting_down",
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
    # Check all dependencies
    db_source_ok = await check_source_connection()
    db_target_ok = await check_target_connection()
    event_bus_ok = await check_event_bus()
    
    # All dependencies must be OK for the service to be ready
    all_dependencies_ok = db_source_ok and db_target_ok and event_bus_ok
    
    return {
        "status": "ready" if all_dependencies_ok and not _shutting_down else "not_ready",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "dependencies": {
            "database": "ok" if db_source_ok and db_target_ok else "error",
            "event_bus": "ok" if event_bus_ok else "error"
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
    # Check database connections
    db_source_ok = await check_source_connection()
    db_target_ok = await check_target_connection()
    event_bus_ok = await check_event_bus()
    
    # Calculate uptime
    uptime = datetime.utcnow() - _start_time
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"
    
    # All dependencies must be OK for the service to be healthy
    all_dependencies_ok = db_source_ok and db_target_ok and event_bus_ok
    
    return {
        "status": "healthy" if all_dependencies_ok and not _shutting_down else "unhealthy",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "uptime": uptime_str,
        "started_at": _start_time.isoformat(),
        "dependencies": {
            "database": {
                "source": {
                    "status": "connected" if db_source_ok else "disconnected",
                    "latency": "10ms"  # Placeholder
                },
                "target": {
                    "status": "connected" if db_target_ok else "disconnected",
                    "latency": "5ms"  # Placeholder
                }
            },
            "event_bus": {
                "status": "connected" if event_bus_ok else "disconnected",
                "latency": "5ms"  # Placeholder
            }
        },
        "performance": {
            "memory_usage": "120MB",  # Placeholder
            "cpu_usage": "2%",  # Placeholder
            "request_rate": "10 req/s",  # Placeholder
            "error_rate": "0 err/s",  # Placeholder
            "active_connections": 5  # Placeholder
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
    logger.info("Service marked as shutting down")


def reset_shutting_down() -> None:
    """
    Reset the shutting down flag.
    
    This function is primarily for testing purposes.
    """
    global _shutting_down
    _shutting_down = False
    logger.info("Service marked as not shutting down")