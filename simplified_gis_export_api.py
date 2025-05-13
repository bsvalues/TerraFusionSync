"""
TerraFusion SyncService - Simplified GIS Export API

This is a simplified version of the SyncService API that focuses only on the GIS Export plugin.
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the GIS Export plugin router
try:
    from terrafusion_sync.plugins.gis_export import router as gis_export_router
    logger.info("Successfully imported GIS Export router")
    GIS_EXPORT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import GIS Export router: {e}")
    GIS_EXPORT_AVAILABLE = False

# Create FastAPI application
app = FastAPI(
    title="TerraFusion GIS Export Service",
    description="Simplified GIS Export service",
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

# Include GIS Export router
if GIS_EXPORT_AVAILABLE:
    app.include_router(gis_export_router, prefix="/plugins/v1/gis-export", tags=["gis-export"])
    logger.info("Successfully included GIS Export router")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion GIS Export Service",
        "version": "0.1.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "TerraFusion GIS Export Service",
        "status": "healthy",
        "version": "0.1.0",
        "time": datetime.utcnow().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)