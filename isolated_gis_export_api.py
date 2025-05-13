"""
TerraFusion SyncService - Isolated GIS Export API

This is a completely isolated version of the GIS Export API that avoids
importing any other plugins or modules that might cause conflicts.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TerraFusion GIS Export API",
    description="Isolated GIS Export API service",
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

# Define models
class GisExportRequest(BaseModel):
    county_id: str = Field(..., description="ID of the county")
    username: str = Field(..., description="Username of the requester")
    format: str = Field(..., description="Export format (geojson, shapefile, kml)")
    area_of_interest: Dict[str, Any] = Field(..., description="GeoJSON defining the area of interest")
    layers: List[str] = Field(..., description="Layers to include in the export")
    
    class Config:
        schema_extra = {
            "example": {
                "county_id": "county123",
                "username": "user@example.com",
                "format": "geojson",
                "area_of_interest": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "layers": ["parcels", "buildings", "roads"]
            }
        }

class GisExportJobBase(BaseModel):
    job_id: int
    county_id: str
    username: str
    status: str
    created_at: datetime

class GisExportJobDetail(GisExportJobBase):
    format: str
    area_of_interest: Dict[str, Any]
    layers: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    message: Optional[str] = None

# In-memory storage for jobs
JOB_ID_COUNTER = 0
EXPORT_JOBS = {}

def get_next_job_id():
    global JOB_ID_COUNTER
    JOB_ID_COUNTER += 1
    return JOB_ID_COUNTER

def process_export_job(job_id: int):
    """
    Process an export job in the background.
    This simulates the actual processing without doing any real work.
    """
    import time
    
    # Get the job
    job = EXPORT_JOBS[job_id]
    
    # Update job status to RUNNING
    job["status"] = "RUNNING"
    job["started_at"] = datetime.now(timezone.utc)
    job["message"] = "Processing export job"
    
    # Simulate processing time
    time.sleep(2)
    
    # Update job status to COMPLETED
    job["status"] = "COMPLETED"
    job["completed_at"] = datetime.now(timezone.utc)
    job["download_url"] = f"/api/v1/gis-export/download/{job_id}"
    job["message"] = "Export completed successfully"

# API endpoints
@app.post("/plugins/v1/gis-export/run", response_model=GisExportJobBase)
async def create_export_job(request: GisExportRequest, background_tasks: BackgroundTasks):
    """Create a new GIS export job."""
    job_id = get_next_job_id()
    
    job = {
        "job_id": job_id,
        "county_id": request.county_id,
        "username": request.username,
        "format": request.format,
        "area_of_interest": request.area_of_interest,
        "layers": request.layers,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc),
        "message": "Job created, waiting to be processed"
    }
    
    EXPORT_JOBS[job_id] = job
    
    # Start processing the job in the background
    background_tasks.add_task(process_export_job, job_id)
    
    return job

@app.get("/plugins/v1/gis-export/status/{job_id}", response_model=GisExportJobDetail)
async def get_job_status(job_id: int):
    """Get the status of a GIS export job."""
    if job_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return EXPORT_JOBS[job_id]

@app.get("/plugins/v1/gis-export/list", response_model=List[GisExportJobBase])
async def list_jobs(
    county_id: Optional[str] = None,
    username: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List GIS export jobs with optional filtering."""
    # Filter jobs based on query parameters
    filtered_jobs = EXPORT_JOBS.values()
    
    if county_id:
        filtered_jobs = [job for job in filtered_jobs if job["county_id"] == county_id]
    
    if username:
        filtered_jobs = [job for job in filtered_jobs if job["username"] == username]
    
    if status:
        filtered_jobs = [job for job in filtered_jobs if job["status"] == status]
    
    # Sort by created_at (newest first) and apply pagination
    sorted_jobs = sorted(filtered_jobs, key=lambda job: job["created_at"], reverse=True)
    paginated_jobs = sorted_jobs[offset:offset + limit]
    
    return paginated_jobs

@app.delete("/plugins/v1/gis-export/cancel/{job_id}", response_model=GisExportJobBase)
async def cancel_job(job_id: int):
    """Cancel a GIS export job."""
    if job_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = EXPORT_JOBS[job_id]
    
    if job["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job['status']}")
    
    job["status"] = "CANCELLED"
    job["message"] = "Job cancelled by user"
    
    return job

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
        "time": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)