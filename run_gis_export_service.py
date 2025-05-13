#!/usr/bin/env python
"""
Run GIS Export Service

This script runs the GIS Export service as a standalone process.
It configures the service with a custom metrics registry to avoid conflicts.
"""

import os
import sys
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set environment variable for custom registry
os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"

def create_app():
    """Create and configure the FastAPI application."""
    logger.info("Creating GIS Export application...")
    
    # Create FastAPI app
    app = FastAPI(
        title="GIS Export Service",
        description="Service for exporting GIS data",
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
    
    # Initialize the database and models
    @app.on_event("startup")
    async def startup_db_client():
        """Initialize database on startup."""
        from isolated_gis_export_test import startup_event
        await startup_event()
    
    # Add routes from the isolated test module
    from isolated_gis_export_test import (
        run_gis_export_job,
        get_job_status,
        list_jobs,
        cancel_job,
        health_check,
    )
    
    # Register routes
    app.add_api_route("/gis-export/run", run_gis_export_job, methods=["POST"])
    app.add_api_route("/gis-export/status/{job_id}", get_job_status, methods=["GET"])
    app.add_api_route("/gis-export/list", list_jobs, methods=["GET"])
    app.add_api_route("/gis-export/cancel/{job_id}", cancel_job, methods=["POST"])
    app.add_api_route("/gis-export/health", health_check, methods=["GET"])
    
    # Add metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Expose Prometheus metrics."""
        # Use a custom registry
        registry = CollectorRegistry()
        
        # Add sample metrics for testing
        counter = Counter('gis_export_api_requests_total', 'Total count of API requests', 
                         ['endpoint', 'method', 'status'], registry=registry)
        counter.labels('run', 'POST', '200').inc(1)
        counter.labels('status', 'GET', '200').inc(2)
        counter.labels('list', 'GET', '200').inc(3)
        
        # Generate and return metrics
        return generate_latest(registry).decode("utf-8")
    
    # Add root endpoint for health check
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "status": "ok",
            "service": "gis_export",
            "version": "1.0.0"
        }
    
    return app

def main():
    """Main entry point."""
    try:
        logger.info("Starting GIS Export Service...")
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8083)
    except Exception as e:
        logger.error(f"Failed to start GIS Export Service: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()