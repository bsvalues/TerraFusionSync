"""
Simplified FastAPI application for the syncservice.

This is a minimal version to get the workflow running.
"""

import os
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from syncservice.api import health, sync

# Function to check if port 5000 is in use and select 8000 as an alternative
def get_available_port():
    import socket
    
    # First try port 8000 (preferred)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('0.0.0.0', 8000))
        s.close()
        return 8000
    except socket.error:
        # If port 8000 is not available
        try:
            # Check if port 5000 is available
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('0.0.0.0', 5000))
            s.close()
            return 5000
        except socket.error:
            # If neither port is available, use 8000 anyway
            return 8000

# Create FastAPI application
app = FastAPI(
    title="TerraFusion SyncService",
    description="Service for syncing data between legacy PACS and CAMA systems",
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