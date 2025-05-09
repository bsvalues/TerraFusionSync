"""
TerraFusion SyncService - FastAPI Application

This module provides the FastAPI application for the TerraFusion SyncService platform.
It initializes the database and sets up routes for property assessment synchronization.
"""

import logging
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import database and models
from terrafusion_sync.database import get_db_session, initialize_db, get_db_status
from terrafusion_sync.core_models import (
    PropertyOperational,
    PropertyValuation,
    PropertyImprovement,
    SyncSourceSystem,
    ImportJob
)

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TerraFusion SyncService",
    description="Enterprise data synchronization platform for County Property Assessment",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting TerraFusion SyncService...")
    try:
        await initialize_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Check the health of the SyncService.
    
    Returns:
        dict: Health status information
    """
    db_status = await get_db_status()
    return {
        "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
        "version": "0.1.0",
        "database": db_status,
        "environment": os.getenv("ENV", "development")
    }


# Property endpoints
@app.get("/properties", tags=["Properties"], response_model=List[Dict[str, Any]])
async def get_properties(
    county_id: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get properties with optional filtering.
    
    Args:
        county_id: Filter by county ID
        property_type: Filter by property type
        limit: Maximum number of properties to return
        offset: Offset for pagination
        db: Database session dependency
        
    Returns:
        List of property dictionaries
    """
    query = select(PropertyOperational)
    
    # Apply filters if provided
    if county_id:
        query = query.where(PropertyOperational.county_id == county_id)
    if property_type:
        query = query.where(PropertyOperational.property_type == property_type)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    try:
        result = await db.execute(query)
        properties = result.scalars().all()
        return [prop.to_dict() for prop in properties]
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching properties: {str(e)}"
        )


@app.get("/properties/{property_id}", tags=["Properties"], response_model=Dict[str, Any])
async def get_property(
    property_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get a property by ID.
    
    Args:
        property_id: The property ID
        db: Database session dependency
        
    Returns:
        Property as a dictionary
        
    Raises:
        HTTPException: If property not found
    """
    query = select(PropertyOperational).where(PropertyOperational.property_id == property_id)
    
    try:
        result = await db.execute(query)
        property = result.scalar_one_or_none()
        
        if not property:
            raise HTTPException(
                status_code=404,  # HTTP_404_NOT_FOUND
                detail=f"Property with ID {property_id} not found"
            )
            
        return property.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching property: {str(e)}"
        )


# Sync Source System endpoints
@app.get("/sync-sources", tags=["Sync"], response_model=List[Dict[str, Any]])
async def get_sync_sources(
    county_id: Optional[str] = None,
    system_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get sync source systems with optional filtering.
    
    Args:
        county_id: Filter by county ID
        system_type: Filter by system type
        db: Database session dependency
        
    Returns:
        List of sync source system dictionaries
    """
    query = select(SyncSourceSystem)
    
    # Apply filters if provided
    if county_id:
        query = query.where(SyncSourceSystem.county_id == county_id)
    if system_type:
        query = query.where(SyncSourceSystem.system_type == system_type)
    
    try:
        result = await db.execute(query)
        systems = result.scalars().all()
        return [
            {
                "id": system.id,
                "name": system.name,
                "system_type": system.system_type,
                "county_id": system.county_id,
                "connection_type": system.connection_type,
                "is_active": system.is_active,
                "last_successful_sync": system.last_successful_sync.isoformat() if system.last_successful_sync else None,
                "created_at": system.created_at.isoformat()
            }
            for system in systems
        ]
    except Exception as e:
        logger.error(f"Error fetching sync sources: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching sync sources: {str(e)}"
        )


# Import Job endpoints
@app.get("/import-jobs", tags=["Import"], response_model=List[Dict[str, Any]])
async def get_import_jobs(
    source_system_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Get import jobs with optional filtering.
    
    Args:
        source_system_id: Filter by source system ID
        status: Filter by job status
        limit: Maximum number of jobs to return
        offset: Offset for pagination
        db: Database session dependency
        
    Returns:
        List of import job dictionaries
    """
    query = select(ImportJob).order_by(ImportJob.created_at.desc())
    
    # Apply filters if provided
    if source_system_id:
        query = query.where(ImportJob.source_system_id == source_system_id)
    if status:
        query = query.where(ImportJob.status == status)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    try:
        result = await db.execute(query)
        jobs = result.scalars().all()
        return [
            {
                "id": job.id,
                "source_system_id": job.source_system_id,
                "job_type": job.job_type,
                "status": job.status,
                "total_records": job.total_records,
                "processed_records": job.processed_records,
                "successful_records": job.successful_records,
                "failed_records": job.failed_records,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "created_at": job.created_at.isoformat(),
                "created_by": job.created_by,
                "progress_percentage": job.progress_percentage,
                "success_rate": job.success_rate,
                "duration_seconds": job.duration_seconds
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error fetching import jobs: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching import jobs: {str(e)}"
        )