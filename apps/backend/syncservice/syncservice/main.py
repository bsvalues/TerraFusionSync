"""
Main module for the SyncService.

This module initializes and runs the FastAPI application for the SyncService.
"""

import asyncio
import logging
import os
import signal
import sys
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable

from fastapi import FastAPI, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader

import uvicorn

from .monitoring.metrics import MetricsCollector
from .monitoring.system_monitoring import SystemMonitor
from .monitoring.sync_tracker import SyncTracker, SyncStatus

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("syncservice")

# Always use port 8080 for SyncService to avoid conflicts with main app
PORT = 8080
# Override the environment variable to ensure consistency
os.environ["SYNC_SERVICE_PORT"] = str(PORT)

# Import authentication
from .auth import api_key_header, API_KEY

# Create FastAPI app
app = FastAPI(
    title="TerraFusion SyncService API",
    description="API for synchronizing data between different systems",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
metrics_collector = None
system_monitor = None
sync_tracker = None


@app.on_event("startup")
async def startup_event():
    """
    Event handler called when the application starts up.
    """
    global metrics_collector, system_monitor, sync_tracker
    
    # Startup
    logger.info("Starting SyncService...")
    
    # Initialize metrics collector (optional)
    metrics_collector = MetricsCollector(
        db_url=os.environ.get("SYNC_SERVICE_DB_URL")
    )
    await metrics_collector.setup()
    
    # Initialize system monitor
    system_monitor = SystemMonitor(interval=60)
    await system_monitor.start()
    
    # Initialize sync tracker (optional)
    sync_tracker = SyncTracker(
        db_url=os.environ.get("SYNC_SERVICE_DB_URL")
    )
    await sync_tracker.setup()
    
    logger.info("SyncService started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Event handler called when the application shuts down.
    """
    logger.info("Shutting down SyncService...")
    
    if system_monitor:
        await system_monitor.stop()
    
    logger.info("SyncService shut down successfully")


# Try to mount static files for dashboard UI
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(current_dir, "static")
    
    if os.path.exists(static_dir) and os.path.isdir(static_dir):
        app.mount("/dashboard", StaticFiles(directory=static_dir, html=True), name="dashboard")
    else:
        logger.warning(f"Could not mount dashboard static files: Directory 'static' does not exist")
except Exception as e:
    logger.warning(f"Failed to mount static files: {str(e)}")


# Add API routes
@app.get("/", tags=["Info"])
async def root():
    """
    Get API information.
    
    Returns:
        Basic information about the API
    """
    return {
        "name": "TerraFusion SyncService API",
        "version": "1.0.0",
        "description": "API for synchronizing data between different systems",
        "docs_url": "/docs",
        "dashboard_url": "/dashboard"
    }


@app.get("/health/live", tags=["Health"])
async def health_live():
    """
    Liveness probe endpoint.
    
    Returns:
        Health status with timestamp
    """
    return {
        "status": "UP",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/ready", tags=["Health"])
async def health_ready():
    """
    Readiness probe endpoint.
    
    Returns:
        Readiness status with timestamp
    
    Raises:
        HTTPException: If the service is not ready
    """
    # Check if all required services are available
    if not system_monitor:
        raise HTTPException(status_code=503, detail="System monitor not initialized")
    
    return {
        "status": "READY",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health/status", tags=["Health"])
async def health_status():
    """
    Detailed health status endpoint.
    
    Returns:
        Detailed health status with component statuses
    """
    return {
        "status": "UP",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "components": {
            "system_monitor": "UP" if system_monitor else "DOWN",
            "metrics_collector": "UP" if metrics_collector else "DOWN",
            "sync_tracker": "UP" if sync_tracker else "DOWN"
        }
    }


# Import verify_api_key from auth module
from .auth import verify_api_key


@app.get("/api/metrics", tags=["Monitoring"])
async def get_metrics(
    prefix: Optional[str] = None,
    hours: int = 1,
    limit: int = 100,
    api_key: str = Depends(verify_api_key)
):
    """
    Get system metrics.
    
    Args:
        prefix: Optional metric name prefix filter
        hours: Number of hours of data to return
        limit: Maximum number of metrics to return
        api_key: API key from dependency
        
    Returns:
        List of metrics
    """
    if not metrics_collector:
        return []
        
    return await metrics_collector.get_metrics(
        metric_name_prefix=prefix,
        start_time=datetime.utcnow() - timedelta(hours=hours),
        end_time=datetime.utcnow(),
        limit=limit
    )


@app.get("/api/system", tags=["Monitoring"])
async def get_system_info(api_key: str = Depends(verify_api_key)):
    """
    Get current system information.
    
    Args:
        api_key: API key from dependency
        
    Returns:
        Dictionary of system information
    """
    if not system_monitor:
        return {}
        
    return await system_monitor.get_system_health()


@app.get("/api/sync/operations", tags=["Sync"])
async def get_sync_operations(
    sync_pair_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    api_key: str = Depends(verify_api_key)
):
    """
    Get sync operations.
    
    Args:
        sync_pair_id: Optional filter by sync pair ID
        status: Optional filter by status
        limit: Maximum number of operations to return
        offset: Offset for pagination
        api_key: API key from dependency
        
    Returns:
        List of sync operations
    """
    if not sync_tracker:
        return []
        
    status_filter = None
    if status:
        try:
            status_filter = SyncStatus(status.upper())
        except ValueError:
            pass
            
    return await sync_tracker.get_operations(
        sync_pair_id=sync_pair_id,
        status=status_filter,
        limit=limit,
        offset=offset
    )


@app.get("/api/sync/metrics", tags=["Sync"])
async def get_sync_metrics(
    sync_pair_id: Optional[str] = None,
    days: int = 7,
    api_key: str = Depends(verify_api_key)
):
    """
    Get sync metrics.
    
    Args:
        sync_pair_id: Optional filter by sync pair ID
        days: Number of days to include in metrics
        api_key: API key from dependency
        
    Returns:
        Dictionary of sync metrics
    """
    if not sync_tracker:
        return {}
        
    return await sync_tracker.calculate_sync_metrics(
        sync_pair_id=sync_pair_id,
        days=days
    )


@app.get("/api/sync/active", tags=["Sync"])
async def get_active_sync_operations(api_key: str = Depends(verify_api_key)):
    """
    Get currently active sync operations.
    
    Args:
        api_key: API key from dependency
        
    Returns:
        List of active sync operations
    """
    if not sync_tracker:
        return []
        
    return await sync_tracker.get_active_operations()


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
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path
        }
    )


@app.get("/api/config", tags=["Admin"])
async def get_config(api_key: str = Depends(verify_api_key)):
    """
    Get current service configuration.
    
    Args:
        api_key: API key from dependency
        
    Returns:
        Dictionary of configuration values
    """
    return {
        "version": "1.0.0",
        "environment": os.environ.get("ENVIRONMENT", "development"),
        "api_port": PORT,
        "logging_level": logging.getLevelName(logger.level),
        "db_url_configured": bool(os.environ.get("SYNC_SERVICE_DB_URL")),
        "api_key_configured": API_KEY != "dev-api-key"
    }


# Import and include API routers
from .api import dashboard, sync, compatibility

app.include_router(dashboard.router)
app.include_router(sync.router)
app.include_router(compatibility.router)


if __name__ == "__main__":
    # Force port 8080 for SyncService to avoid conflicts with main Flask app on port 5000
    if 'SYNC_SERVICE_PORT' in os.environ:
        try:
            # Try to use the environment variable, but if it's 5000, override to 8080
            port = int(os.environ['SYNC_SERVICE_PORT'])
            if port == 5000:
                logger.warning("Detected port 5000 which conflicts with main app. Forcing port 8080 instead.")
                port = 8080
        except (ValueError, TypeError):
            logger.warning("Invalid port in environment variable. Using default port 8080.")
            port = 8080
    else:
        # No environment variable, use the default
        port = 8080
    
    # Log the port we're using
    logger.info(f"Starting SyncService on port {port}")
    
    # Run uvicorn with the corrected port
    uvicorn.run(app, host="0.0.0.0", port=port)