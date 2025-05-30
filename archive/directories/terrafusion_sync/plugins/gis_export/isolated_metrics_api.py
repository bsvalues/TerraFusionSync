"""
Isolated Metrics API for GIS Export Plugin

This module provides a dedicated FastAPI application for GIS Export metrics,
ensuring isolation from other plugins to prevent registry conflicts.
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a standalone FastAPI app for metrics
app = FastAPI(
    title="GIS Export Metrics API",
    description="Isolated API for GIS Export metrics",
    version="1.0.0",
)

@app.get("/metrics", 
       summary="Get GIS Export plugin metrics",
       description="Get Prometheus metrics for the GIS Export plugin.",
       response_class=PlainTextResponse)
async def get_plugin_metrics():
    """
    Get Prometheus metrics for the GIS Export plugin.
    
    This endpoint provides metrics specific to the GIS Export plugin
    in Prometheus format.
    
    Returns:
        Response: Prometheus-formatted metrics text
    """
    try:
        # Import the GisExportMetrics class to get metrics
        from terrafusion_sync.plugins.gis_export.metrics import GisExportMetrics
        
        # Set up custom registry
        os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"
        
        # Initialize metrics with custom registry if not already initialized
        if GisExportMetrics.registry is None:
            GisExportMetrics.initialize(use_default_registry=False)
        
        # Get metrics as text
        metrics_text = GisExportMetrics.get_metrics()
        
        return metrics_text
    except Exception as e:
        logger.error(f"Error getting GIS Export metrics: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics: {str(e)}"
        )

@app.get("/health", 
       summary="Health check for GIS Export Metrics API",
       description="Check if the GIS Export Metrics API is healthy and operational.")
async def health_check():
    """
    Health check endpoint for the GIS Export Metrics API.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "plugin": "gis_export_metrics",
        "version": "1.0.0"
    }

# Create a mount function for use in the main application
def get_metrics_app():
    """Get the FastAPI application for mounting in the main app."""
    return app