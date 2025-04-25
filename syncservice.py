"""
Entry point for the SyncService API.

This module configures and launches the FastAPI application with all required
dependencies and endpoints for the SyncService plugin.
"""
import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

# Import the safe system monitoring component
try:
    from manual_fix_system_monitoring import safe_monitor, get_safe_system_info
    SAFE_MONITOR_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Using SafeSystemMonitor for system monitoring")
except ImportError:
    SAFE_MONITOR_AVAILABLE = False
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.warning("SafeSystemMonitor not available, using basic monitoring")

# Create FastAPI application
app = FastAPI(
    title="TerraFusion SyncService",
    description="Synchronization service for enterprise data migration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# System monitoring (fallback implementation if SafeSystemMonitor is not available)
class BasicSystemMonitor:
    """
    Simplified system monitoring with robust error handling.
    This is a fallback when the full implementation is not available.
    """
    def __init__(self):
        """Initialize the system monitor."""
        self.start_time = datetime.utcnow()
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health with minimal dependencies.
        
        Returns:
            Dictionary with basic system health metrics
        """
        try:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
            
            # Minimal health data that doesn't require external libraries
            return {
                "status": "healthy",
                "uptime_seconds": uptime,
                "cpu_usage_percent": 0.0,  # Placeholder
                "memory_usage_percent": 0.0,  # Placeholder
                "disk_usage_percent": 0.0,  # Placeholder
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "status": "degraded",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Initialize system monitor based on availability
if SAFE_MONITOR_AVAILABLE:
    system_monitor = safe_monitor
else:
    system_monitor = BasicSystemMonitor()

@app.get("/")
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """
    General health check endpoint that provides comprehensive system status.
    This combines liveness and readiness information.
    """
    health_data = system_monitor.get_system_health()
    return {
        "service": "TerraFusion SyncService",
        "status": health_data["status"],
        "version": "0.1.0",
        "time": datetime.utcnow().isoformat(),
        "system": health_data
    }

@app.get("/health/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Verifies that the application is running and responsive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health/ready")
async def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Verifies that the application is ready to accept traffic.
    """
    # Check system health to ensure we're in a good state
    health_data = system_monitor.get_system_health()
    
    # In a real implementation, we would check database connections,
    # message queue connections, and other dependencies
    
    is_ready = health_data["status"] == "healthy"
    
    if not is_ready:
        # Return 503 Service Unavailable if not ready
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "reason": "System health check failed",
                "details": health_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return {
        "status": "ready",
        "details": {
            "dependencies": {
                "database": "up",  # This would be dynamic in a real implementation
                "message_queue": "up"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/config")
async def get_config():
    """Get current service configuration."""
    return {
        "service": "TerraFusion SyncService",
        "port": 8080,
        "debug_mode": True,
        "supports_incremental_sync": True,
        "supports_full_sync": True,
        "max_batch_size": 1000,
        "default_sync_interval_hours": 24
    }

@app.get("/systems")
async def get_systems():
    """Get available systems for synchronization."""
    return [
        {
            "id": "pacs",
            "name": "PACS System",
            "description": "Property Assessment and Collection System",
            "supports_incremental": True
        },
        {
            "id": "cama",
            "name": "CAMA System",
            "description": "Computer Assisted Mass Appraisal",
            "supports_incremental": True
        },
        {
            "id": "gis",
            "name": "GIS System",
            "description": "Geographic Information System",
            "supports_incremental": False
        },
        {
            "id": "erp",
            "name": "ERP System",
            "description": "Enterprise Resource Planning",
            "supports_incremental": True
        },
        {
            "id": "crm",
            "name": "CRM System",
            "description": "Customer Relationship Management",
            "supports_incremental": True
        }
    ]

@app.get("/sync-pairs")
async def get_sync_pairs():
    """Get configured synchronization pairs."""
    return [
        {
            "id": 1,
            "name": "PACS-CAMA Integration",
            "description": "Synchronize property data between PACS and CAMA systems",
            "source_system": "pacs",
            "target_system": "cama",
            "entity_types": ["property", "owner", "valuation"],
            "active": True,
            "created_at": "2023-01-01T00:00:00Z",
            "last_sync": "2023-04-15T08:30:00Z"
        },
        {
            "id": 2,
            "name": "GIS-ERP Integration",
            "description": "Sync geographical data with ERP system",
            "source_system": "gis",
            "target_system": "erp",
            "entity_types": ["location", "boundary", "zone"],
            "active": True,
            "created_at": "2023-01-15T00:00:00Z",
            "last_sync": "2023-04-14T10:15:00Z"
        }
    ]

@app.post("/sync/{pair_id}/start")
async def start_sync(
    pair_id: str,
    sync_type: str = "incremental",
    hours: Optional[int] = 24
):
    """
    Start a synchronization operation.
    
    Args:
        pair_id: ID of the sync pair
        sync_type: Type of sync (incremental or full)
        hours: For incremental sync, how many hours to look back
    """
    # This would normally start a background task
    operation_id = f"op-{int(time.time())}"
    return {
        "operation_id": operation_id,
        "sync_pair_id": pair_id,
        "sync_type": sync_type,
        "status": "pending",
        "started_at": datetime.utcnow().isoformat(),
        "estimated_completion": (
            datetime.utcnow().timestamp() + (3600 if sync_type == "incremental" else 7200)
        ),
        "message": f"Started {sync_type} sync for pair {pair_id}"
    }

@app.get("/operations")
async def get_operations(active_only: bool = False):
    """
    Get sync operations.
    
    Args:
        active_only: If true, only return active operations
    """
    return [
        {
            "operation_id": "op-1681546800",
            "sync_pair_id": 1,
            "sync_type": "incremental",
            "status": "completed",
            "started_at": "2023-04-15T08:00:00Z",
            "completed_at": "2023-04-15T08:30:00Z",
            "total_records": 150,
            "processed_records": 150,
            "successful_records": 148,
            "failed_records": 2
        },
        {
            "operation_id": "op-1681459500",
            "sync_pair_id": 2,
            "sync_type": "incremental",
            "status": "completed",
            "started_at": "2023-04-14T10:05:00Z",
            "completed_at": "2023-04-14T10:15:00Z",
            "total_records": 45,
            "processed_records": 45,
            "successful_records": 45,
            "failed_records": 0
        }
    ]

@app.get("/metrics")
async def get_metrics():
    """
    Get system and operation metrics in a format suitable for monitoring systems.
    This endpoint provides detailed metrics about the syncservice performance.
    """
    # Get current health metrics
    health_data = system_monitor.get_system_health()
    
    # Get system information
    system_info = {}
    if SAFE_MONITOR_AVAILABLE:
        try:
            system_info = get_safe_system_info()
        except Exception as e:
            logger.error(f"Error getting system info: {str(e)}")
    
    # Sample operation metrics (in a real implementation, these would come from a database)
    operation_metrics = {
        "total_operations": 150,
        "successful_operations": 145,
        "failed_operations": 5,
        "active_operations": 2,
        "average_duration_seconds": 450,
        "records_processed_last_24h": 2500,
        "success_rate_percent": 96.7
    }
    
    # Build the complete metrics response
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "system": {
            "status": health_data.get("status", "unknown"),
            "uptime_seconds": health_data.get("uptime_seconds", 0),
            "cpu_usage_percent": health_data.get("cpu_usage", 0),
            "memory_usage_percent": health_data.get("memory_usage", 0),
            "disk_usage_percent": health_data.get("disk_usage", 0),
            "active_connections": health_data.get("active_connections", 0),
            "platform": system_info.get("platform", "unknown"),
            "python_version": system_info.get("python_version", "unknown")
        },
        "operations": operation_metrics,
        "performance": {
            "response_time_avg_ms": health_data.get("response_time", 0) * 1000,
            "error_count": health_data.get("error_count", 0),
            "sync_operations_count": health_data.get("sync_operations_count", 0)
        }
    }
    
    return metrics

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)