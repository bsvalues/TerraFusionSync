#!/usr/bin/env python3
"""
Isolated GIS Export Metrics API

This script runs a completely isolated GIS Export metrics API
that doesn't depend on importing the main module to avoid conflicts.
"""

import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
import uvicorn
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create a standalone FastAPI app
app = FastAPI(
    title="Isolated GIS Export Metrics API",
    description="Completely isolated API for GIS Export metrics",
    version="1.0.0",
)

# Create a custom registry
registry = CollectorRegistry()

# Create metrics with our isolated registry
gis_export_jobs_submitted = Counter(
    'gis_export_jobs_submitted_total',
    'Total number of GIS export jobs submitted',
    ['county_id', 'export_format'],
    registry=registry
)

gis_export_jobs_completed = Counter(
    'gis_export_jobs_completed_total',
    'Total number of GIS export jobs completed successfully',
    ['county_id', 'export_format'],
    registry=registry
)

gis_export_jobs_failed = Counter(
    'gis_export_jobs_failed_total',
    'Total number of GIS export jobs that failed',
    ['county_id', 'export_format', 'error_type'],
    registry=registry
)

gis_export_processing_duration = Histogram(
    'gis_export_processing_duration_seconds',
    'Duration of GIS export job processing in seconds',
    ['county_id', 'export_format'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry
)

gis_export_file_size = Histogram(
    'gis_export_file_size_kb',
    'Size of exported GIS files in KB',
    ['county_id', 'export_format'],
    buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000),
    registry=registry
)

gis_export_record_count = Histogram(
    'gis_export_record_count',
    'Number of records in GIS export results',
    ['county_id', 'export_format'],
    buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000),
    registry=registry
)

# Keep track of job data for metrics
job_data = {}

@app.get("/metrics", 
       summary="Get GIS Export plugin metrics",
       description="Get Prometheus metrics for the GIS Export plugin.",
       response_class=PlainTextResponse)
async def get_metrics():
    """
    Get Prometheus metrics for the GIS Export plugin.
    
    This endpoint provides metrics specific to the GIS Export plugin
    in Prometheus format.
    
    Returns:
        Response: Prometheus-formatted metrics text
    """
    try:
        metrics_text = generate_latest(registry).decode('utf-8')
        return metrics_text
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
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
        "plugin": "gis_export_metrics_isolated",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/record/job_submitted")
async def record_job_submitted(data: dict):
    """Record a job submission in the metrics."""
    try:
        county_id = data.get("county_id", "unknown")
        export_format = data.get("format", "unknown")
        job_id = data.get("job_id")
        
        # Record the metric
        gis_export_jobs_submitted.labels(
            county_id=county_id,
            export_format=export_format
        ).inc()
        
        # Store job data for future updates
        if job_id:
            job_data[job_id] = {
                "county_id": county_id,
                "export_format": export_format,
                "status": "SUBMITTED",
                "submitted_at": datetime.utcnow().isoformat()
            }
        
        return {"status": "success", "message": "Job submission recorded"}
    except Exception as e:
        logger.error(f"Error recording job submission: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record job submission: {str(e)}"
        )

@app.post("/record/job_completed")
async def record_job_completed(data: dict):
    """Record a job completion in the metrics."""
    try:
        job_id = data.get("job_id")
        county_id = data.get("county_id", "unknown")
        export_format = data.get("format", "unknown")
        duration_seconds = data.get("duration_seconds", 0)
        file_size_kb = data.get("file_size_kb", 0)
        record_count = data.get("record_count", 0)
        
        # Use stored job data if available
        if job_id and job_id in job_data:
            county_id = job_data[job_id].get("county_id", county_id)
            export_format = job_data[job_id].get("export_format", export_format)
        
        # Record metrics
        gis_export_jobs_completed.labels(
            county_id=county_id,
            export_format=export_format
        ).inc()
        
        gis_export_processing_duration.labels(
            county_id=county_id,
            export_format=export_format
        ).observe(duration_seconds)
        
        gis_export_file_size.labels(
            county_id=county_id,
            export_format=export_format
        ).observe(file_size_kb)
        
        gis_export_record_count.labels(
            county_id=county_id,
            export_format=export_format
        ).observe(record_count)
        
        # Update job data
        if job_id and job_id in job_data:
            job_data[job_id].update({
                "status": "COMPLETED",
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": duration_seconds,
                "file_size_kb": file_size_kb,
                "record_count": record_count
            })
        
        return {"status": "success", "message": "Job completion recorded"}
    except Exception as e:
        logger.error(f"Error recording job completion: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record job completion: {str(e)}"
        )

@app.post("/record/job_failed")
async def record_job_failed(data: dict):
    """Record a job failure in the metrics."""
    try:
        job_id = data.get("job_id")
        county_id = data.get("county_id", "unknown")
        export_format = data.get("format", "unknown")
        error_type = data.get("error_type", "unknown_error")
        
        # Use stored job data if available
        if job_id and job_id in job_data:
            county_id = job_data[job_id].get("county_id", county_id)
            export_format = job_data[job_id].get("export_format", export_format)
        
        # Record the metric
        gis_export_jobs_failed.labels(
            county_id=county_id,
            export_format=export_format,
            error_type=error_type
        ).inc()
        
        # Update job data
        if job_id and job_id in job_data:
            job_data[job_id].update({
                "status": "FAILED",
                "failed_at": datetime.utcnow().isoformat(),
                "error_type": error_type
            })
        
        return {"status": "success", "message": "Job failure recorded"}
    except Exception as e:
        logger.error(f"Error recording job failure: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record job failure: {str(e)}"
        )

@app.get("/jobs")
async def get_jobs():
    """Get all job data for debugging."""
    return job_data

def main():
    """Run the isolated GIS Export metrics API."""
    parser = argparse.ArgumentParser(description="Run Isolated GIS Export Metrics API")
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8090, help='Port to use')
    parser.add_argument('--reload', action='store_true', help='Enable auto-reload')
    
    args = parser.parse_args()
    
    logger.info(f"Starting Isolated GIS Export Metrics API on {args.host}:{args.port}")
    
    # Generate some sample metrics for testing
    gis_export_jobs_submitted.labels(county_id="test_county", export_format="GeoJSON").inc()
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()