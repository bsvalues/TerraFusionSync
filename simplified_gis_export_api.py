#!/usr/bin/env python
"""
Simplified GIS Export API

This module provides a simplified version of the GIS Export API 
that can be used for testing and development.
"""

import os
import json
import uuid
import asyncio
import datetime
import logging
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, JSON, Text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel

# Set environment variable for custom registry
os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Simplified GIS Export API",
    description="API for exporting GIS data in various formats",
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

# Create Base class for models
Base = declarative_base()

# GIS Export Job Model
class GisExportJob(Base):
    """Database model for GIS export jobs."""
    __tablename__ = "gis_export_jobs"
    
    job_id = Column(String, primary_key=True)
    export_format = Column(String, nullable=False)
    county_id = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # JSON fields for complex data
    area_of_interest_json = Column(JSON)
    layers_json = Column(JSON)
    parameters_json = Column(JSON)
    
    # Result fields
    result_file_location = Column(String)
    result_file_size_kb = Column(Integer)
    result_record_count = Column(Integer)

# Database setup with SQLite for testing
DATABASE_URL = "sqlite+aiosqlite:///./gis_export_test.db"
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Session dependency
async def get_async_session():
    """Get async database session."""
    async with async_session_maker() as session:
        yield session

# Request and response models
class GisExportRunRequest(BaseModel):
    """Request model for GIS export job submission."""
    export_format: str
    county_id: str
    area_of_interest: Dict[str, Any]
    layers: List[str]
    parameters: Optional[Dict[str, Any]] = {}

class GisExportJobStatusResponse(BaseModel):
    """Response model for GIS export job status."""
    job_id: str
    export_format: str
    county_id: str
    status: str
    message: str
    parameters: Dict[str, Any]
    created_at: datetime.datetime
    updated_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

class GisExportJobResultResponse(GisExportJobStatusResponse):
    """Response model for GIS export job results."""
    result: Optional[Dict[str, Any]] = None

# Custom functions for metrics (simplified)
metrics_data = {
    "jobs_submitted": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "processing_times": [],
    "file_sizes": [],
    "record_counts": []
}

def track_job_submitted(county_id: str, export_format: str, status: str) -> None:
    """Track job submission in metrics."""
    metrics_data["jobs_submitted"] += 1

def track_job_completed(county_id: str, export_format: str) -> None:
    """Track job completion in metrics."""
    metrics_data["jobs_completed"] += 1

def track_job_failed(county_id: str, export_format: str, reason: str) -> None:
    """Track job failure in metrics."""
    metrics_data["jobs_failed"] += 1

def track_processing_time(county_id: str, export_format: str, seconds: float) -> None:
    """Track job processing time in metrics."""
    metrics_data["processing_times"].append(seconds)

def track_file_size(county_id: str, export_format: str, kb: int) -> None:
    """Track file size in metrics."""
    metrics_data["file_sizes"].append(kb)

def track_record_count(county_id: str, export_format: str, count: int) -> None:
    """Track record count in metrics."""
    metrics_data["record_counts"].append(count)

# API Routes
@app.post("/plugins/v1/gis-export/run", response_model=GisExportJobStatusResponse)
async def run_gis_export_job(
    request: GisExportRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """Submit a GIS export job."""
    try:
        logger.info(f"Received GIS export job request: {request}")
        
        # Create a new job
        now = datetime.datetime.utcnow()
        job_id = str(uuid.uuid4())
        
        new_job = GisExportJob(
            job_id=job_id,
            export_format=request.export_format,
            county_id=request.county_id,
            status="PENDING",
            message="GIS export job accepted and queued for processing",
            created_at=now,
            updated_at=now,
            area_of_interest_json=request.area_of_interest,
            layers_json=request.layers,
            parameters_json=request.parameters
        )
        
        # Save the job to the database
        db.add(new_job)
        await db.commit()
        
        # Queue a background task to process the job
        background_tasks.add_task(
            process_export_job,
            job_id=job_id,
            export_format=request.export_format,
            county_id=request.county_id
        )
        
        # Track metrics
        track_job_submitted(request.county_id, request.export_format, "PENDING")
        
        # Return the response
        return GisExportJobStatusResponse(
            job_id=job_id,
            export_format=request.export_format,
            county_id=request.county_id,
            status="PENDING",
            message="GIS export job accepted and queued for processing",
            parameters={
                "area_of_interest": request.area_of_interest,
                "layers": request.layers,
                **request.parameters
            },
            created_at=now,
            updated_at=now
        )
    except Exception as e:
        logger.error(f"Error submitting GIS export job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit GIS export job: {str(e)}"
        )

@app.get("/plugins/v1/gis-export/status/{job_id}", response_model=GisExportJobStatusResponse)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Get the status of a GIS export job."""
    try:
        # Query the job
        query = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job '{job_id}' not found"
            )
        
        # Return job status
        return GisExportJobStatusResponse(
            job_id=job.job_id,
            export_format=job.export_format,
            county_id=job.county_id,
            status=job.status,
            message=job.message,
            parameters={
                "area_of_interest": job.area_of_interest_json,
                "layers": job.layers_json,
                **(job.parameters_json or {})
            },
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}"
        )

@app.get("/plugins/v1/gis-export/list", response_model=List[GisExportJobStatusResponse])
async def list_jobs(
    county_id: Optional[str] = None,
    export_format: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session)
):
    """List all GIS export jobs with optional filtering."""
    try:
        # Build query with filters
        query = select(GisExportJob).order_by(GisExportJob.created_at.desc())
        
        if county_id:
            query = query.where(GisExportJob.county_id == county_id)
        
        if export_format:
            query = query.where(GisExportJob.export_format == export_format)
        
        if status:
            query = query.where(GisExportJob.status == status)
        
        query = query.limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        # Build response
        response_jobs = []
        for job in jobs:
            response_jobs.append(GisExportJobStatusResponse(
                job_id=job.job_id,
                export_format=job.export_format,
                county_id=job.county_id,
                status=job.status,
                message=job.message,
                parameters={
                    "area_of_interest": job.area_of_interest_json,
                    "layers": job.layers_json,
                    **(job.parameters_json or {})
                },
                created_at=job.created_at,
                updated_at=job.updated_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            ))
        
        return response_jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list GIS export jobs: {str(e)}"
        )

@app.post("/plugins/v1/gis-export/cancel/{job_id}", response_model=GisExportJobStatusResponse)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Cancel a GIS export job."""
    try:
        # Query the job
        query = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job '{job_id}' not found"
            )
        
        # Check if job can be cancelled
        if job.status not in ["PENDING", "RUNNING"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status '{job.status}'. Only PENDING or RUNNING jobs can be cancelled."
            )
        
        # Update job status
        now = datetime.datetime.utcnow()
        job.status = "CANCELLED"
        job.message = "Job cancelled by user request"
        job.updated_at = now
        if job.started_at and not job.completed_at:
            job.completed_at = now
        
        await db.commit()
        
        # Track metrics
        track_job_failed(job.county_id, job.export_format, "user_cancelled")
        
        # Return updated status
        return GisExportJobStatusResponse(
            job_id=job.job_id,
            export_format=job.export_format,
            county_id=job.county_id,
            status=job.status,
            message=job.message,
            parameters={
                "area_of_interest": job.area_of_interest_json,
                "layers": job.layers_json,
                **(job.parameters_json or {})
            },
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )

@app.get("/plugins/v1/gis-export/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "plugin": "gis_export",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "gis_export",
        "version": "1.0.0"
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return {
        "metrics": metrics_data
    }

# Background job processor
async def process_export_job(job_id: str, export_format: str, county_id: str):
    """Process a GIS export job in the background."""
    logger.info(f"Processing GIS export job {job_id}")
    
    try:
        # Create a new session
        async with async_session_maker() as session:
            # Get the job from the database
            query = select(GisExportJob).where(GisExportJob.job_id == job_id)
            result = await session.execute(query)
            job = result.scalar_one_or_none()
            
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update job status to RUNNING
            now = datetime.datetime.utcnow()
            job.status = "RUNNING"
            job.message = "Processing export job"
            job.updated_at = now
            job.started_at = now
            
            await session.commit()
            
            # Simulate processing time
            await asyncio.sleep(2)
            
            # Check if job was cancelled
            await session.refresh(job)
            if job.status == "CANCELLED":
                logger.info(f"Job {job_id} was cancelled, stopping processing")
                return
            
            # Update job as completed
            now = datetime.datetime.utcnow()
            
            # Simulate results
            file_size = 1024  # 1KB
            record_count = 100
            
            job.status = "COMPLETED"
            job.message = "Export completed successfully"
            job.updated_at = now
            job.completed_at = now
            job.result_file_location = f"/exports/{county_id}/{job_id}.{export_format.lower()}"
            job.result_file_size_kb = file_size
            job.result_record_count = record_count
            
            await session.commit()
            
            # Track metrics
            track_job_completed(county_id, export_format)
            track_file_size(county_id, export_format, file_size)
            track_record_count(county_id, export_format, record_count)
            
            # Calculate processing time
            if job.started_at and job.completed_at:
                processing_time = (job.completed_at - job.started_at).total_seconds()
                track_processing_time(county_id, export_format, processing_time)
            
            logger.info(f"Completed GIS export job {job_id}")
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {e}", exc_info=True)
        
        # Update job as failed
        try:
            async with async_session_maker() as session:
                query = select(GisExportJob).where(GisExportJob.job_id == job_id)
                result = await session.execute(query)
                job = result.scalar_one_or_none()
                
                if job:
                    job.status = "FAILED"
                    job.message = f"Export failed: {str(e)}"
                    job.updated_at = datetime.datetime.utcnow()
                    
                    await session.commit()
                    
                    # Track metrics
                    track_job_failed(county_id, export_format, "processing_error")
        except Exception as inner_e:
            logger.error(f"Error updating failed job {job_id}: {inner_e}", exc_info=True)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")