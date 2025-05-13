#!/usr/bin/env python
"""
Isolated GIS Export Test

This script tests the GIS Export functionality without importing from other plugins.
"""

import os
import sys
import json
import uuid
import datetime
import logging
import asyncio
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status as fastapi_status
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, JSON, Text, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base, DeclarativeMeta
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Create Base class for models
Base = declarative_base()

# GIS Export Job Model
class GisExportJob(Base):
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
    async with async_session_maker() as session:
        yield session

# Mock metrics implementations
class DummyMetric:
    def inc(self, amount=1): pass
    def observe(self, amount): pass
    def labels(self, **kwargs): return self

# Set up dummy metrics
GIS_EXPORT_JOBS_SUBMITTED_TOTAL = DummyMetric()
GIS_EXPORT_JOBS_COMPLETED_TOTAL = DummyMetric()
GIS_EXPORT_JOBS_FAILED_TOTAL = DummyMetric()
GIS_EXPORT_PROCESSING_DURATION_SECONDS = DummyMetric()
GIS_EXPORT_FILE_SIZE_KB = DummyMetric() 
GIS_EXPORT_RECORD_COUNT = DummyMetric()

# Request and response models
class GisExportRunRequest:
    def __init__(self, export_format: str, county_id: str, area_of_interest: Dict[str, Any], 
                layers: List[str], parameters: Optional[Dict[str, Any]] = None):
        self.export_format = export_format
        self.county_id = county_id
        self.area_of_interest = area_of_interest
        self.layers = layers
        self.parameters = parameters or {}

class GisExportJobStatusResponse:
    def __init__(self, job_id: str, export_format: str, county_id: str,
                status: str, message: str, parameters: Dict[str, Any],
                created_at: datetime.datetime, updated_at: datetime.datetime,
                started_at: Optional[datetime.datetime] = None,
                completed_at: Optional[datetime.datetime] = None):
        self.job_id = job_id
        self.export_format = export_format
        self.county_id = county_id
        self.status = status
        self.message = message
        self.parameters = parameters
        self.created_at = created_at
        self.updated_at = updated_at
        self.started_at = started_at
        self.completed_at = completed_at

class GisExportJobResultResponse(GisExportJobStatusResponse):
    def __init__(self, *args, result: Dict[str, Any] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = result or {}

# Define FastAPI app
app = FastAPI(
    title="Isolated GIS Export API",
    description="Isolated API for testing GIS Export functionality",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create the router
@app.post("/gis-export/run", response_model=Dict)
async def run_gis_export_job(request_data: Dict, background_tasks: BackgroundTasks, 
                          db: AsyncSession = Depends(get_async_session)):
    """Submit a GIS export job."""
    try:
        # Parse request data
        export_format = request_data.get("export_format")
        county_id = request_data.get("county_id")
        area_of_interest = request_data.get("area_of_interest")
        layers = request_data.get("layers", [])
        parameters = request_data.get("parameters", {})
        
        # Validate required fields
        if not export_format:
            raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, 
                                detail="export_format is required")
        if not county_id:
            raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, 
                                detail="county_id is required")
        if not area_of_interest:
            raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, 
                                detail="area_of_interest is required")
        if not layers:
            raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, 
                                detail="At least one layer must be specified")
        
        # Create a new job
        now = datetime.datetime.utcnow()
        job_id = str(uuid.uuid4())
        
        new_job = GisExportJob(
            job_id=job_id,
            export_format=export_format,
            county_id=county_id,
            status="PENDING",
            message="GIS export job accepted and queued for processing",
            created_at=now,
            updated_at=now,
            area_of_interest_json=area_of_interest,
            layers_json=layers,
            parameters_json=parameters
        )
        
        # Save the job to the database
        db.add(new_job)
        await db.commit()
        
        # Queue a background task to process the job
        background_tasks.add_task(
            process_export_job,
            job_id=job_id,
            export_format=export_format,
            county_id=county_id
        )
        
        # Log and track metrics
        logger.info(f"Submitted GIS export job {job_id} for county {county_id} in {export_format} format")
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL.labels(
            county_id=county_id,
            export_format=export_format,
            status_on_submit="PENDING"
        ).inc()
        
        # Return the response
        return {
            "job_id": job_id,
            "export_format": export_format,
            "county_id": county_id,
            "status": "PENDING",
            "message": "GIS export job accepted and queued for processing",
            "parameters": {
                "area_of_interest": area_of_interest,
                "layers": layers,
                **parameters
            },
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "started_at": None,
            "completed_at": None
        }
    except Exception as e:
        logger.error(f"Error submitting GIS export job: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit GIS export job: {str(e)}"
        )

@app.get("/gis-export/status/{job_id}", response_model=Dict)
async def get_job_status(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Get the status of a GIS export job."""
    try:
        # Query the job
        query = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job '{job_id}' not found"
            )
        
        # Return job status
        return {
            "job_id": job.job_id,
            "export_format": job.export_format,
            "county_id": job.county_id,
            "status": job.status,
            "message": job.message,
            "parameters": {
                "area_of_interest": job.area_of_interest_json,
                "layers": job.layers_json,
                **(job.parameters_json or {})
            },
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    except Exception as e:
        logger.error(f"Error getting job status: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}"
        )

@app.get("/gis-export/list", response_model=List[Dict])
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
            response_jobs.append({
                "job_id": job.job_id,
                "export_format": job.export_format,
                "county_id": job.county_id,
                "status": job.status,
                "message": job.message,
                "parameters": {
                    "area_of_interest": job.area_of_interest_json,
                    "layers": job.layers_json,
                    **(job.parameters_json or {})
                },
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "updated_at": job.updated_at.isoformat() if job.updated_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })
        
        return response_jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list GIS export jobs: {str(e)}"
        )

@app.post("/gis-export/cancel/{job_id}", response_model=Dict)
async def cancel_job(job_id: str, db: AsyncSession = Depends(get_async_session)):
    """Cancel a GIS export job."""
    try:
        # Query the job
        query = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job '{job_id}' not found"
            )
        
        # Check if job can be cancelled
        if job.status not in ["PENDING", "RUNNING"]:
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status '{job.status}'. Only PENDING or RUNNING jobs can be cancelled."
            )
        
        # Update job status
        now = datetime.datetime.utcnow()
        job.status = "FAILED"
        job.message = "Job cancelled by user request"
        job.updated_at = now
        if job.started_at and not job.completed_at:
            job.completed_at = now
        
        await db.commit()
        
        # Track metrics
        GIS_EXPORT_JOBS_FAILED_TOTAL.labels(
            county_id=job.county_id,
            export_format=job.export_format,
            failure_reason="user_cancelled"
        ).inc()
        
        # Return updated status
        return {
            "job_id": job.job_id,
            "export_format": job.export_format,
            "county_id": job.county_id,
            "status": job.status,
            "message": job.message,
            "parameters": {
                "area_of_interest": job.area_of_interest_json,
                "layers": job.layers_json,
                **(job.parameters_json or {})
            },
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None
        }
    except Exception as e:
        logger.error(f"Error cancelling job: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )

@app.get("/gis-export/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "plugin": "gis_export",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

# Simulated background task for processing jobs
async def process_export_job(job_id: str, export_format: str, county_id: str):
    """Simulate processing a GIS export job in the background."""
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
            if job.status == "FAILED" and "cancelled" in job.message.lower():
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
            GIS_EXPORT_JOBS_COMPLETED_TOTAL.labels(
                county_id=county_id,
                export_format=export_format
            ).inc()
            
            GIS_EXPORT_FILE_SIZE_KB.labels(
                county_id=county_id,
                export_format=export_format
            ).observe(file_size)
            
            GIS_EXPORT_RECORD_COUNT.labels(
                county_id=county_id,
                export_format=export_format
            ).observe(record_count)
            
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
                    GIS_EXPORT_JOBS_FAILED_TOTAL.labels(
                        county_id=county_id,
                        export_format=export_format,
                        failure_reason="processing_error"
                    ).inc()
        except Exception as inner_e:
            logger.error(f"Error updating failed job {job_id}: {inner_e}", exc_info=True)

@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized")

# Main entry point
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8083)