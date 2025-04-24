"""
Health check endpoints for the SyncService.

This module implements liveness and readiness probe endpoints.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status

from syncservice.utils.database import check_source_connection, check_target_connection
from syncservice.utils.event_bus import check_nats_connection

logger = logging.getLogger(__name__)

router = APIRouter()

# Variables to track service health
service_startup_time = datetime.utcnow()
service_is_ready = False
service_is_shutting_down = False


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict:
    """
    Liveness probe endpoint.
    
    This endpoint indicates whether the service is alive. It should return a 200 OK
    status code if the service is running, and a non-200 status code if the service
    needs to be restarted.
    
    Returns:
        Service liveness status
    """
    if service_is_shutting_down:
        # If the service is in the process of shutting down, it should no longer
        # be considered alive
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is shutting down"
        )
    
    uptime = datetime.utcnow() - service_startup_time
    
    return {
        "status": "up",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "uptime_seconds": uptime.total_seconds(),
        "started_at": service_startup_time.isoformat()
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict:
    """
    Readiness probe endpoint.
    
    This endpoint indicates whether the service is ready to accept requests.
    It should return a 200 OK status code if the service is ready, and a non-200
    status code if the service is not ready to accept requests.
    
    Returns:
        Service readiness status
    """
    if service_is_shutting_down:
        # If the service is shutting down, it's not ready for new requests
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is shutting down"
        )
    
    # Check source database connection
    source_db_ok = await check_source_connection()
    
    # Check target database connection
    target_db_ok = await check_target_connection()
    
    # Check NATS connection
    nats_ok = await check_nats_connection()
    
    # All dependencies must be available for the service to be ready
    if not (source_db_ok and target_db_ok and nats_ok):
        # Update global readiness state
        global service_is_ready
        service_is_ready = False
        
        # Return 503 Service Unavailable
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not_ready",
                "dependencies": {
                    "source_database": "ok" if source_db_ok else "error",
                    "target_database": "ok" if target_db_ok else "error",
                    "message_bus": "ok" if nats_ok else "error"
                }
            }
        )
    
    # Update global readiness state
    service_is_ready = True
    
    return {
        "status": "ready",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "dependencies": {
            "source_database": "ok",
            "target_database": "ok",
            "message_bus": "ok"
        }
    }


@router.get("/status", status_code=status.HTTP_200_OK)
async def detailed_health_status() -> Dict:
    """
    Detailed health status endpoint.
    
    This endpoint provides more detailed information about the service's health,
    including dependency statuses and performance metrics.
    
    Returns:
        Detailed service health status
    """
    # Check source database connection
    source_db_ok = await check_source_connection()
    
    # Check target database connection
    target_db_ok = await check_target_connection()
    
    # Check NATS connection
    nats_ok = await check_nats_connection()
    
    # Calculate uptime
    uptime = datetime.utcnow() - service_startup_time
    
    return {
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "status": "available" if (source_db_ok and target_db_ok and nats_ok) else "degraded",
        "uptime_seconds": uptime.total_seconds(),
        "started_at": service_startup_time.isoformat(),
        "is_ready": service_is_ready,
        "is_shutting_down": service_is_shutting_down,
        "dependencies": {
            "source_database": {
                "status": "ok" if source_db_ok else "error"
            },
            "target_database": {
                "status": "ok" if target_db_ok else "error"
            },
            "message_bus": {
                "status": "ok" if nats_ok else "error"
            }
        }
    }


def set_shutting_down() -> None:
    """
    Mark the service as shutting down.
    
    This function should be called when the service is being gracefully shut down,
    to ensure that the health endpoints return appropriate responses.
    """
    global service_is_shutting_down
    service_is_shutting_down = True
    logger.info("Service is now marked as shutting down")
