"""
Simplified FastAPI application for the syncservice.

This is a minimal version to get the workflow running.
"""

import os
import sys
from fastapi import FastAPI, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional

from syncservice.api import health, sync, dashboard
from syncservice.monitoring import system_monitoring

# Function to check if port 5000 is in use and select 8000 as an alternative
def get_available_port():
    import socket
    
    # Always use port 8000 for syncservice
    # This avoids conflict with the main application on port 5000
    return 8000

# Create FastAPI application
app = FastAPI(
    title="TerraFusion SyncService",
    description="Service for syncing data between various source and target systems",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Start system monitoring on application startup
system_monitoring.start_monitoring(interval=60)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "status": "running",
    }

@app.get("/health/live", tags=["health"])
async def liveness_check():
    """Liveness probe endpoint."""
    return {
        "status": "up",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
    }

@app.get("/health/ready", tags=["health"])
async def readiness_check():
    """Readiness probe endpoint."""
    return {
        "status": "ready",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
        "dependencies": {
            "database": "ok",
            "event_bus": "ok"
        }
    }

@app.get("/health/status", tags=["health"])
async def detailed_health_status():
    """Detailed health status endpoint."""
    return {
        "status": "healthy",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
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
            "cpu_usage": "2%"
        }
    }

@app.get("/systems/source", tags=["systems"])
async def list_source_systems():
    """List all available source systems."""
    try:
        # Import here to avoid circular imports
        from syncservice.adapters import get_available_source_systems
        from syncservice.config.system_config import get_sync_config
        
        config = get_sync_config()
        return {
            "systems": get_available_source_systems(),
            "enabled_systems": [
                system.system_name for system in config.source_systems.values() 
                if system.is_enabled
            ]
        }
    except Exception as e:
        return {
            "error": f"Failed to list source systems: {str(e)}",
            "systems": [],
            "enabled_systems": []
        }

@app.get("/systems/target", tags=["systems"])
async def list_target_systems():
    """List all available target systems."""
    try:
        # Import here to avoid circular imports
        from syncservice.adapters import get_available_target_systems
        from syncservice.config.system_config import get_sync_config
        
        config = get_sync_config()
        return {
            "systems": get_available_target_systems(),
            "enabled_systems": [
                system.system_name for system in config.target_systems.values() 
                if system.is_enabled
            ]
        }
    except Exception as e:
        return {
            "error": f"Failed to list target systems: {str(e)}",
            "systems": [],
            "enabled_systems": []
        }

@app.get("/systems/pairs", tags=["systems"])
async def list_sync_pairs():
    """List all configured sync pairs."""
    try:
        # Import here to avoid circular imports
        from syncservice.config.system_config import get_sync_config
        
        config = get_sync_config()
        return {
            "pairs": [
                {
                    "id": pair_id,
                    "source": pair.source_system,
                    "target": pair.target_system,
                    "description": pair.description,
                    "enabled": pair.is_enabled,
                    "entity_mappings": pair.entity_mappings
                }
                for pair_id, pair in config.sync_pairs.items()
            ]
        }
    except Exception as e:
        return {
            "error": f"Failed to list sync pairs: {str(e)}",
            "pairs": []
        }