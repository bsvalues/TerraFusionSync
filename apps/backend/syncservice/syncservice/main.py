"""
Main module for the SyncService.

This module initializes and runs the FastAPI application for the SyncService.
"""

import logging
import os
import yaml
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, Request, status, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader
from contextlib import asynccontextmanager
import uvicorn

from .models.base import HealthStatus, HealthCheckResponse
from .monitoring.metrics import MetricsCollector
from .monitoring.system_monitoring import SystemMonitor
from .monitoring.sync_tracker import SyncTracker
from .api import sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger("syncservice")

# Global variables for service components
metrics_collector = None
system_monitor = None
sync_tracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager for FastAPI application lifecycle events.
    
    This function is called when the application starts up and shuts down.
    """
    # Startup
    logger.info("Starting SyncService...")
    
    # Initialize components
    global metrics_collector, system_monitor, sync_tracker
    metrics_collector = MetricsCollector()
    system_monitor = SystemMonitor(metrics_collector)
    sync_tracker = SyncTracker()
    
    # Start monitoring
    await system_monitor.start()
    
    logger.info("SyncService started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down SyncService...")
    
    # Stop monitoring
    if system_monitor:
        await system_monitor.stop()
    
    logger.info("SyncService shut down successfully")


# Create the FastAPI application
app = FastAPI(
    title="SyncService API",
    description="API for the TerraFusion SyncService",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional API key authentication
API_KEY = os.environ.get("SYNC_SERVICE_API_KEY")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Verify API key for protected endpoints.
    
    Args:
        api_key: API key from header
    
    Returns:
        True if key is valid
    
    Raises:
        HTTPException: If key is invalid
    """
    if not API_KEY:
        # No API key set, authentication is disabled
        return True
    
    if api_key == API_KEY:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API key",
        headers={"WWW-Authenticate": "ApiKey"},
    )


# Include routers from other modules
app.include_router(sync.router, dependencies=[Depends(verify_api_key)])

# Create a router for monitoring and health endpoints
monitor_router = APIRouter(prefix="/api/monitor", tags=["monitoring"])


@monitor_router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Check the health of the SyncService.
    
    Returns:
        Health status information
    """
    # Get system health
    system_health = await system_monitor.get_system_health()
    
    # Determine overall status
    status = HealthStatus.UP
    
    # Return health check response
    return HealthCheckResponse(
        status=status,
        service="SyncService",
        version="1.0.0",
        dependencies={
            "database": HealthStatus.UNKNOWN,  # Database not configured yet
            "system": system_health.get("error") and HealthStatus.DEGRADED or HealthStatus.UP
        },
        performance={
            "cpu_percent": str(system_health.get("cpu", {}).get("percent", 0)) + "%",
            "memory_percent": str(system_health.get("memory", {}).get("percent", 0)) + "%"
        }
    )


@monitor_router.get("/metrics")
async def get_metrics(
    prefix: Optional[str] = None,
    hours: int = 1,
    limit: int = 100
):
    """
    Get system metrics.
    
    Args:
        prefix: Optional metric name prefix filter
        hours: Number of hours of data to return
        limit: Maximum number of metrics to return
        
    Returns:
        List of metrics
    """
    from datetime import datetime, timedelta
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    return await metrics_collector.get_metrics(
        metric_name_prefix=prefix or "",
        start_time=start_time,
        end_time=end_time,
        limit=limit
    )


@monitor_router.get("/system")
async def get_system_info():
    """
    Get current system information.
    
    Returns:
        Dictionary of system information
    """
    return await system_monitor.get_system_health()


@monitor_router.get("/sync/operations")
async def get_sync_operations(
    sync_pair_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0
):
    """
    Get sync operations.
    
    Args:
        sync_pair_id: Optional filter by sync pair ID
        status: Optional filter by status
        limit: Maximum number of operations to return
        offset: Offset for pagination
        
    Returns:
        List of sync operations
    """
    from .models.base import SyncStatus
    
    # Convert status string to enum if provided
    status_enum = None
    if status:
        try:
            status_enum = SyncStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status value: {status}"
            )
    
    operations = await sync_tracker.get_operations(
        sync_pair_id=sync_pair_id,
        status=status_enum,
        limit=limit,
        offset=offset
    )
    
    # Convert operations to dictionary for JSON response
    return [
        {
            "id": op.id,
            "sync_pair_id": op.sync_pair_id,
            "sync_type": op.sync_type.value,
            "entity_types": op.entity_types,
            "status": op.status.value,
            "start_time": op.start_time.isoformat(),
            "end_time": op.end_time.isoformat() if op.end_time else None,
            "details": op.details.dict() if op.details else None,
            "error": op.error
        }
        for op in operations
    ]


@monitor_router.get("/sync/metrics")
async def get_sync_metrics(
    sync_pair_id: Optional[str] = None,
    days: int = 7
):
    """
    Get sync metrics.
    
    Args:
        sync_pair_id: Optional filter by sync pair ID
        days: Number of days to include in metrics
        
    Returns:
        Dictionary of sync metrics
    """
    return await sync_tracker.calculate_sync_metrics(
        sync_pair_id=sync_pair_id,
        days=days
    )


@monitor_router.get("/sync/active")
async def get_active_sync_operations():
    """
    Get currently active sync operations.
    
    Returns:
        List of active sync operations
    """
    operations = await sync_tracker.get_active_operations()
    
    # Convert operations to dictionary for JSON response
    return [
        {
            "id": op.id,
            "sync_pair_id": op.sync_pair_id,
            "sync_type": op.sync_type.value,
            "entity_types": op.entity_types,
            "status": op.status.value,
            "start_time": op.start_time.isoformat(),
            "duration_minutes": (datetime.utcnow() - op.start_time).total_seconds() / 60,
            "details": op.details.dict() if op.details else None
        }
        for op in operations
    ]


# Include the monitoring router
app.include_router(monitor_router)

# Mount static files for the dashboard UI
try:
    app.mount("/dashboard", StaticFiles(directory="static", html=True), name="dashboard")
except RuntimeError as e:
    logger.warning(f"Could not mount dashboard static files: {str(e)}")


# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for all unhandled exceptions.
    
    Args:
        request: Request that caused the exception
        exc: Exception raised
        
    Returns:
        JSONResponse with error details
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Add endpoint for internal configuration
@app.get("/internal/config")
async def get_config(api_key: str = Depends(verify_api_key)):
    """
    Get current service configuration.
    
    Args:
        api_key: API key from dependency
        
    Returns:
        Dictionary of configuration values
    """
    # This would normally load configuration from a file or database
    # For now, returning a placeholder
    return {
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "components": {
            "metrics_collector": metrics_collector is not None,
            "system_monitor": system_monitor is not None,
            "sync_tracker": sync_tracker is not None
        }
    }


# Main entry point
if __name__ == "__main__":
    port = int(os.environ.get("SYNC_SERVICE_PORT", 8000))
    
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )