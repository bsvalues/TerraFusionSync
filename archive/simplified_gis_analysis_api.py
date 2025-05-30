"""
Simplified GIS Analysis API

This module provides a standalone FastAPI implementation of the GIS Analysis plugin API.
It's designed for faster startup and simpler debugging compared to the full SyncService.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import uvicorn
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="GIS Analysis API")


# Sample in-memory database for testing
DB = {
    "jobs": {},
    "spatial_layers": {}
}


# Define Pydantic models for API (simplified from the full schemas)
class GISAnalysisType(str):
    """Types of GIS analyses supported by the API."""
    PROPERTY_BOUNDARY = "property_boundary"
    FLOOD_ZONE = "flood_zone"
    ZONING_ANALYSIS = "zoning_analysis"
    PROXIMITY_ANALYSIS = "proximity_analysis"
    HEATMAP_GENERATION = "heatmap_generation"
    SPATIAL_QUERY = "spatial_query"
    BUFFER_ANALYSIS = "buffer_analysis"
    INTERSECTION_ANALYSIS = "intersection_analysis"


class GISAnalysisRunRequest(BaseModel):
    """
    Schema for submitting a GIS analysis job.
    """
    county_id: str = Field(..., description="County ID for which to run the analysis")
    analysis_type: str = Field(..., description="Type of GIS analysis to perform")
    parameters: Dict[str, Any] = Field(
        ..., 
        description="Parameters specific to the analysis type"
    )


class GISAnalysisJobResponse(BaseModel):
    """
    Schema for job status response.
    """
    job_id: str
    county_id: str
    analysis_type: str
    status: str
    message: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# Mock processing functions
async def mock_process_job(job_id: str):
    """Simulate job processing."""
    job = DB["jobs"].get(job_id)
    if not job:
        return
    
    # Update to running status
    job["status"] = "RUNNING"
    job["message"] = "Job is being processed"
    job["started_at"] = datetime.utcnow().isoformat()
    job["updated_at"] = datetime.utcnow().isoformat()
    
    # Simulate processing time based on analysis type
    processing_times = {
        "property_boundary": 2,
        "flood_zone": 3,
        "zoning_analysis": 2.5,
        "proximity_analysis": 2.5,
        "heatmap_generation": 4,
        "spatial_query": 3,
        "buffer_analysis": 2,
        "intersection_analysis": 2.5,
    }
    processing_time = processing_times.get(job["analysis_type"], 3)
    await asyncio.sleep(processing_time)
    
    # Update to completed status
    job["status"] = "COMPLETED"
    job["message"] = "Job completed successfully"
    job["completed_at"] = datetime.utcnow().isoformat()
    job["updated_at"] = datetime.utcnow().isoformat()
    
    # Add mock results based on analysis type
    job["result_json"] = json.dumps({
        "analysis_type": job["analysis_type"],
        "parameters": json.loads(job["parameters_json"]),
        "sample_result": f"Sample result for {job['analysis_type']}",
        "completion_time": job["completed_at"]
    })
    
    job["result_summary_json"] = json.dumps({
        "analysis_type": job["analysis_type"],
        "status": "COMPLETED",
        "processing_time_seconds": processing_time
    })
    
    logger.info(f"Job {job_id} completed with status: {job['status']}")


# API Routes
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "plugin": "gis_analysis_simplified",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/gis-analysis/run", response_model=GISAnalysisJobResponse, tags=["GIS Analysis"])
async def run_analysis(request: GISAnalysisRunRequest, background_tasks: BackgroundTasks):
    """Submit a GIS analysis job."""
    job_id = f"gis-{uuid.uuid4()}"
    now = datetime.utcnow().isoformat()
    
    # Create job
    DB["jobs"][job_id] = {
        "job_id": job_id,
        "county_id": request.county_id,
        "analysis_type": request.analysis_type,
        "parameters_json": json.dumps(request.parameters),
        "status": "PENDING",
        "message": "Job queued for processing",
        "created_at": now,
        "updated_at": now,
        "started_at": None,
        "completed_at": None,
        "result_json": None,
        "result_summary_json": None,
        "geojson_result": None
    }
    
    logger.info(f"Created GIS analysis job: {job_id}")
    
    # Start processing in background
    background_tasks.add_task(mock_process_job, job_id)
    
    return DB["jobs"][job_id]


@app.get("/api/gis-analysis/status/{job_id}", response_model=GISAnalysisJobResponse, tags=["GIS Analysis"])
async def get_job_status(job_id: str):
    """Get status of a GIS analysis job."""
    job = DB["jobs"].get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"GIS analysis job not found: {job_id}")
    
    return job


@app.get("/api/gis-analysis/list", response_model=List[GISAnalysisJobResponse], tags=["GIS Analysis"])
async def list_jobs(
    county_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List GIS analysis jobs with optional filtering."""
    # Apply filters
    filtered_jobs = DB["jobs"].values()
    
    if county_id:
        filtered_jobs = [j for j in filtered_jobs if j["county_id"] == county_id]
    
    if analysis_type:
        filtered_jobs = [j for j in filtered_jobs if j["analysis_type"] == analysis_type]
    
    if status:
        filtered_jobs = [j for j in filtered_jobs if j["status"] == status]
    
    # Sort by creation time (descending)
    sorted_jobs = sorted(filtered_jobs, key=lambda j: j["created_at"], reverse=True)
    
    # Apply pagination
    paginated_jobs = sorted_jobs[offset:offset+limit]
    
    return paginated_jobs


@app.get("/api/gis-analysis/results/{job_id}", tags=["GIS Analysis"])
async def get_analysis_results(job_id: str):
    """Get results of a GIS analysis job."""
    job = DB["jobs"].get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"GIS analysis job not found: {job_id}")
    
    if job["status"] not in ["COMPLETED", "FAILED"]:
        raise HTTPException(
            status_code=400, 
            detail=f"GIS analysis job is not completed. Current status: {job['status']}"
        )
    
    # Parse JSON fields
    parameters = json.loads(job["parameters_json"]) if job["parameters_json"] else {}
    results = json.loads(job["result_json"]) if job["result_json"] else {}
    geojson_result = json.loads(job["geojson_result"]) if job["geojson_result"] else None
    
    return {
        "job_id": job["job_id"],
        "county_id": job["county_id"],
        "analysis_type": job["analysis_type"],
        "status": job["status"],
        "message": job["message"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "parameters": parameters,
        "results": results,
        "geojson_result": geojson_result,
    }


@app.get("/api/gis-analysis/layers", tags=["GIS Analysis"])
async def list_layers(
    county_id: Optional[str] = None,
    layer_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List available spatial layers."""
    # Create some sample layers if empty
    if not DB["spatial_layers"]:
        for i in range(1, 6):
            layer_id = f"layer-{i}"
            layer_type = ["polygon", "point", "line"][i % 3]
            DB["spatial_layers"][layer_id] = {
                "layer_id": layer_id,
                "county_id": "county-123",
                "layer_name": f"Sample Layer {i}",
                "layer_type": layer_type,
                "description": f"Sample description for layer {i}",
                "source": "Sample Source",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "feature_count": i * 10
            }
    
    # Apply filters
    filtered_layers = DB["spatial_layers"].values()
    
    if county_id:
        filtered_layers = [l for l in filtered_layers if l["county_id"] == county_id]
    
    if layer_type:
        filtered_layers = [l for l in filtered_layers if l["layer_type"] == layer_type]
    
    # Sort by name
    sorted_layers = sorted(filtered_layers, key=lambda l: l["layer_name"])
    
    # Apply pagination
    paginated_layers = sorted_layers[offset:offset+limit]
    
    return paginated_layers


@app.get("/api/gis-analysis/statistics", tags=["GIS Analysis"])
async def get_statistics(county_id: Optional[str] = None):
    """Get statistics about GIS analysis jobs."""
    # Filter jobs by county if specified
    jobs = DB["jobs"].values()
    if county_id:
        jobs = [j for j in jobs if j["county_id"] == county_id]
    
    # Count by status
    status_counts = {}
    for job in jobs:
        status = job["status"]
        if status not in status_counts:
            status_counts[status] = 0
        status_counts[status] += 1
    
    # Count by analysis type
    type_counts = {}
    for job in jobs:
        analysis_type = job["analysis_type"]
        if analysis_type not in type_counts:
            type_counts[analysis_type] = 0
        type_counts[analysis_type] += 1
    
    # Get 5 most recent jobs
    sorted_jobs = sorted(jobs, key=lambda j: j["created_at"], reverse=True)
    recent_jobs = sorted_jobs[:5]
    recent_jobs_list = [
        {
            "job_id": job["job_id"],
            "analysis_type": job["analysis_type"],
            "status": job["status"],
            "created_at": job["created_at"]
        }
        for job in recent_jobs
    ]
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_jobs": len(jobs),
        "jobs_by_status": status_counts,
        "jobs_by_type": type_counts,
        "recent_jobs": recent_jobs_list
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting simplified GIS Analysis API on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)