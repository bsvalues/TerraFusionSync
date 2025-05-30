"""
TerraFusion SyncService - GIS Analysis Plugin - Router

This module defines the FastAPI router for GIS Analysis endpoints.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.database import get_async_session
from terrafusion_sync.plugins.gis_analysis import metrics
from terrafusion_sync.plugins.gis_analysis.models import GISAnalysisJob, SpatialLayerMetadata
from terrafusion_sync.plugins.gis_analysis.schemas import (
    GISAnalysisRunRequest,
    GISAnalysisJobResponse,
    GISAnalysisResultResponse,
    SpatialLayerResponse,
    GISAnalysisType,
)
from terrafusion_sync.plugins.gis_analysis.service import (
    create_analysis_job, 
    get_analysis_job, 
    list_analysis_jobs,
    get_job_result,
    update_job_status,
    process_analysis_job,
    list_spatial_layers,
    get_spatial_layer,
    get_analysis_statistics,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()


@router.get("/health", summary="Health check for GIS Analysis API")
async def health_check():
    """
    Health check endpoint for the GIS Analysis API.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "plugin": "gis_analysis",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post(
    "/run", 
    response_model=GISAnalysisJobResponse, 
    summary="Submit a GIS analysis job"
)
async def run_analysis(
    request: GISAnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Submit a GIS analysis job for processing.
    
    Args:
        request: The GIS analysis request parameters
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        GISAnalysisJobResponse: The created job information
    """
    try:
        logger.info(f"Received GIS analysis request: {request.analysis_type} for county {request.county_id}")
        
        # Create a job record
        job = await create_analysis_job(
            db=db,
            county_id=request.county_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters,
        )
        
        # Record metric
        metrics.record_job_created(request.county_id, request.analysis_type)
        
        # Start processing in background
        background_tasks.add_task(
            process_analysis_job,
            job_id=job.job_id,
        )
        
        logger.info(f"GIS analysis job created: {job.job_id}")
        
        return {
            "job_id": job.job_id,
            "county_id": job.county_id,
            "analysis_type": job.analysis_type,
            "status": job.status,
            "message": job.message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
    except Exception as e:
        logger.error(f"Failed to run GIS analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to run GIS analysis: {str(e)}")


@router.get(
    "/status/{job_id}", 
    response_model=GISAnalysisJobResponse,
    summary="Get GIS analysis job status"
)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get the status of a GIS analysis job.
    
    Args:
        job_id: The job ID to check
        db: Database session
        
    Returns:
        GISAnalysisJobResponse: The job status information
        
    Raises:
        HTTPException: If the job is not found
    """
    try:
        job = await get_analysis_job(db, job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"GIS analysis job not found: {job_id}")
        
        return {
            "job_id": job.job_id,
            "county_id": job.county_id,
            "analysis_type": job.analysis_type,
            "status": job.status,
            "message": job.message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GIS analysis job status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")


@router.get(
    "/results/{job_id}", 
    response_model=GISAnalysisResultResponse,
    summary="Get GIS analysis job results"
)
async def get_analysis_results(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get the results of a completed GIS analysis job.
    
    Args:
        job_id: The job ID
        db: Database session
        
    Returns:
        GISAnalysisResultResponse: The job results
        
    Raises:
        HTTPException: If the job is not found or not completed
    """
    try:
        job = await get_analysis_job(db, job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"GIS analysis job not found: {job_id}")
        
        if job.status not in ["COMPLETED", "FAILED"]:
            raise HTTPException(
                status_code=400, 
                detail=f"GIS analysis job is not completed. Current status: {job.status}"
            )
        
        result = await get_job_result(db, job_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get GIS analysis job results: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get job results: {str(e)}")


@router.get(
    "/list", 
    response_model=List[GISAnalysisJobResponse],
    summary="List GIS analysis jobs"
)
async def list_jobs(
    county_id: Optional[str] = None,
    analysis_type: Optional[GISAnalysisType] = None,
    status: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    """
    List GIS analysis jobs with optional filtering.
    
    Args:
        county_id: Filter jobs by county ID
        analysis_type: Filter jobs by analysis type
        status: Filter jobs by status
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        db: Database session
        
    Returns:
        List[GISAnalysisJobResponse]: List of GIS analysis jobs
    """
    try:
        jobs = await list_analysis_jobs(
            db=db,
            county_id=county_id,
            analysis_type=analysis_type.value if analysis_type else None,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "job_id": job.job_id,
                "county_id": job.county_id,
                "analysis_type": job.analysis_type,
                "status": job.status,
                "message": job.message,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at,
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Failed to list GIS analysis jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post(
    "/cancel/{job_id}",
    response_model=GISAnalysisJobResponse,
    summary="Cancel a pending or running GIS analysis job"
)
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cancel a pending or running GIS analysis job.
    
    Args:
        job_id: The job ID to cancel
        db: Database session
        
    Returns:
        GISAnalysisJobResponse: The updated job status
        
    Raises:
        HTTPException: If the job is not found or cannot be cancelled
    """
    try:
        job = await get_analysis_job(db, job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"GIS analysis job not found: {job_id}")
        
        if job.status not in ["PENDING", "RUNNING"]:
            raise HTTPException(
                status_code=400, 
                detail=f"GIS analysis job cannot be cancelled. Current status: {job.status}"
            )
        
        # Update job status to cancelled
        updated_job = await update_job_status(
            db=db,
            job_id=job_id,
            status="CANCELLED",
            message="Job cancelled by user",
        )
        
        # Record metric
        metrics.record_job_cancelled(job.county_id, job.analysis_type)
        
        return {
            "job_id": updated_job.job_id,
            "county_id": updated_job.county_id,
            "analysis_type": updated_job.analysis_type,
            "status": updated_job.status,
            "message": updated_job.message,
            "created_at": updated_job.created_at,
            "updated_at": updated_job.updated_at,
            "started_at": updated_job.started_at,
            "completed_at": updated_job.completed_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel GIS analysis job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.get(
    "/layers", 
    response_model=List[SpatialLayerResponse],
    summary="List available spatial layers"
)
async def get_layers(
    county_id: Optional[str] = None,
    layer_type: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    """
    List available spatial layers with optional filtering.
    
    Args:
        county_id: Filter layers by county ID
        layer_type: Filter layers by type (polygon, point, line, etc.)
        limit: Maximum number of layers to return
        offset: Number of layers to skip
        db: Database session
        
    Returns:
        List[SpatialLayerResponse]: List of spatial layers
    """
    try:
        layers = await list_spatial_layers(
            db=db,
            county_id=county_id,
            layer_type=layer_type,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "layer_id": layer.layer_id,
                "county_id": layer.county_id,
                "layer_name": layer.layer_name,
                "layer_type": layer.layer_type,
                "description": layer.description,
                "source": layer.source,
                "attributes": layer.attributes_json,
                "feature_count": layer.feature_count,
                "bounds": layer.bounds_json,
                "created_at": layer.created_at,
                "updated_at": layer.updated_at,
            }
            for layer in layers
        ]
    except Exception as e:
        logger.error(f"Failed to list spatial layers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list layers: {str(e)}")


@router.get(
    "/layers/{layer_id}", 
    response_model=SpatialLayerResponse,
    summary="Get spatial layer details"
)
async def get_layer(
    layer_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get details of a specific spatial layer.
    
    Args:
        layer_id: The layer ID
        db: Database session
        
    Returns:
        SpatialLayerResponse: Spatial layer details
        
    Raises:
        HTTPException: If the layer is not found
    """
    try:
        layer = await get_spatial_layer(db, layer_id)
        
        if not layer:
            raise HTTPException(status_code=404, detail=f"Spatial layer not found: {layer_id}")
        
        return {
            "layer_id": layer.layer_id,
            "county_id": layer.county_id,
            "layer_name": layer.layer_name,
            "layer_type": layer.layer_type,
            "description": layer.description,
            "source": layer.source,
            "attributes": layer.attributes_json,
            "feature_count": layer.feature_count,
            "bounds": layer.bounds_json,
            "created_at": layer.created_at,
            "updated_at": layer.updated_at,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get spatial layer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get layer: {str(e)}")


@router.get(
    "/statistics", 
    summary="Get GIS analysis statistics"
)
async def get_statistics(
    county_id: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get statistics about GIS analysis jobs.
    
    Args:
        county_id: Filter statistics by county ID
        db: Database session
        
    Returns:
        dict: Statistics about GIS analysis jobs
    """
    try:
        stats = await get_analysis_statistics(db, county_id)
        return stats
    except Exception as e:
        logger.error(f"Failed to get GIS analysis statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")