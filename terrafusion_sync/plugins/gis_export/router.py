"""
TerraFusion SyncService - GIS Export Plugin - Router

This module defines the FastAPI router for GIS Export endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status as fastapi_status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import logging
from typing import Optional, Dict, Any, List
import uuid
import asyncio
import time
import datetime
import json

# Import DB session factory
from terrafusion_sync.database import get_async_session, async_session_maker
from terrafusion_sync.core_models import GisExportJob

# Import Prometheus metrics from the metrics module
try:
    from .metrics import (
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL,
        GIS_EXPORT_JOBS_COMPLETED_TOTAL,
        GIS_EXPORT_JOBS_FAILED_TOTAL,
        GIS_EXPORT_PROCESSING_DURATION_SECONDS,
        GIS_EXPORT_FILE_SIZE_KB,
        GIS_EXPORT_RECORD_COUNT
    )
    logging.info("GIS Export metrics loaded successfully")
except ImportError as e:
    # Fallback to dummy metrics if not defined yet
    class DummyCounter:
        def inc(self, amount=1): pass
        def labels(self, *args, **kwargs): return self
    class DummyHistogram:
        def observe(self, amount): pass
        def labels(self, *args, **kwargs): return self
    
    GIS_EXPORT_JOBS_SUBMITTED_TOTAL = DummyCounter()
    GIS_EXPORT_JOBS_COMPLETED_TOTAL = DummyCounter()
    GIS_EXPORT_JOBS_FAILED_TOTAL = DummyCounter()
    GIS_EXPORT_PROCESSING_DURATION_SECONDS = DummyHistogram()
    GIS_EXPORT_FILE_SIZE_KB = DummyHistogram()
    GIS_EXPORT_RECORD_COUNT = DummyHistogram()
    logging.warning(f"GIS Export metrics import failed: {e}. Using dummy metrics.")

from .schemas import (
    GisExportRunRequest, 
    GisExportJobStatusResponse, 
    GisExportResultData,
    GisExportJobResultResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Import service and tasks modules
from .service import GisExportService
from .tasks import process_gis_export_job, cancel_gis_export_job


# --- API Endpoints for GIS Export Plugin ---
@router.post("/run", response_model=GisExportJobStatusResponse, status_code=fastapi_status.HTTP_202_ACCEPTED)
async def run_gis_export_job(
    request_data: GisExportRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Submit a GIS data export job for processing.

    This endpoint accepts parameters for generating a geographic data export
    and queues a background task to process the request.
    
    Returns:
        GisExportJobStatusResponse: The job information and initial status
    """
    try:
        # Create job through service layer
        new_job = await GisExportService.create_export_job(
            request_data.export_format,
            request_data.county_id,
            request_data.area_of_interest,
            request_data.layers,
            request_data.parameters,
            db
        )
        
        # Record submission metric
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL.labels(
            county_id=request_data.county_id, 
            export_format=request_data.export_format,
            status_on_submit="PENDING"
        ).inc()
        
        logger.info(f"GIS export job {new_job.job_id} created and queued for processing")
        
        # Start background task for processing
        background_tasks.add_task(
            process_gis_export_job, 
            new_job.job_id, 
            new_job.export_format, 
            new_job.county_id,
            new_job.area_of_interest_json,
            new_job.layers_json,
            new_job.parameters_json
        )
        
        # Prepare response payload
        response_payload = {
            "job_id": new_job.job_id,
            "export_format": new_job.export_format,
            "county_id": new_job.county_id,
            "status": new_job.status,
            "message": new_job.message,
            "parameters": {
                "area_of_interest": new_job.area_of_interest_json,
                "layers": new_job.layers_json,
                **(new_job.parameters_json or {})
            },
            "created_at": new_job.created_at,
            "updated_at": new_job.updated_at,
            "started_at": new_job.started_at,
            "completed_at": new_job.completed_at
        }
        
        return response_payload
        
    except Exception as e:
        logger.error(f"Failed to create GIS export job: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to initiate GIS export job: {str(e)}"
        )


@router.get("/status/{job_id_str}", response_model=GisExportJobStatusResponse)
async def get_gis_export_job_status(job_id_str: str, db: AsyncSession = Depends(get_async_session)):
    """
    Get the status of a GIS export job.
    
    Args:
        job_id_str: The job ID to check
        db: Database session
        
    Returns:
        GisExportJobStatusResponse: The job status information
        
    Raises:
        HTTPException: If the job is not found
    """
    try:
        # Get job through service layer
        job = await GisExportService.get_job_by_id(job_id_str, db)
        
        if not job:
            logger.warning(f"GIS export job status request for unknown ID: {job_id_str}")
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND, 
                detail=f"GIS export job '{job_id_str}' not found."
            )
        
        # Reconstruct parameters for response
        response_payload = {
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
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at
        }
        return response_payload
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error retrieving GIS export job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job status: {str(e)}"
        )


@router.get("/results/{job_id_str}", response_model=GisExportJobResultResponse)
async def get_gis_export_job_results(job_id_str: str, db: AsyncSession = Depends(get_async_session)):
    """
    Get the results of a completed GIS export job.
    
    Args:
        job_id_str: The job ID
        db: Database session
        
    Returns:
        GisExportJobResultResponse: The job results
        
    Raises:
        HTTPException: If the job is not found or not completed
    """
    try:
        # Get job through service layer
        job = await GisExportService.get_job_by_id(job_id_str, db)
        
        if not job:
            logger.warning(f"GIS export job results request for unknown ID: {job_id_str}")
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND, 
                detail=f"GIS export job '{job_id_str}' not found."
            )

        # Prepare job status response
        job_status_data = {
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
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "started_at": job.started_at,
            "completed_at": job.completed_at
        }

        export_result_data = None

        if job.status == "COMPLETED":
            export_result_data = {
                "result_file_location": job.result_file_location,
                "result_file_size_kb": job.result_file_size_kb,
                "result_record_count": job.result_record_count
            }
            logger.info(f"GIS export job {job_id_str} results retrieved. File: {job.result_file_location}")
        else:
            logger.info(f"GIS export job {job_id_str} not yet completed. Status: {job.status}")
        
        return {**job_status_data, "result": export_result_data}
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error retrieving GIS export job results: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job results: {str(e)}"
        )


@router.get("/list", response_model=List[GisExportJobStatusResponse])
async def list_gis_export_jobs(
    county_id: Optional[str] = None,
    export_format: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_session)
):
    """
    List GIS export jobs with optional filtering.
    
    Args:
        county_id: Filter jobs by county ID
        export_format: Filter jobs by export format
        status: Filter jobs by status
        limit: Maximum number of jobs to return
        offset: Number of jobs to skip
        db: Database session
        
    Returns:
        List[GisExportJobStatusResponse]: List of GIS export jobs
    """
    try:
        # Get jobs through service layer
        jobs = await GisExportService.list_jobs(
            county_id=county_id,
            export_format=export_format,
            status=status,
            limit=limit,
            offset=offset,
            db=db
        )
        
        # Build response list
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
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "started_at": job.started_at,
                "completed_at": job.completed_at
            })
            
        logger.info(f"Listed {len(response_jobs)} GIS export jobs (filters: county_id={county_id}, format={export_format}, status={status})")
        return response_jobs
        
    except Exception as e:
        logger.error(f"Failed to list GIS export jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to list GIS export jobs: {str(e)}"
        )


@router.post("/cancel/{job_id_str}", response_model=GisExportJobStatusResponse)
async def cancel_gis_export_job_endpoint(job_id_str: str, db: AsyncSession = Depends(get_async_session)):
    """
    Cancel a pending or running GIS export job.
    
    Args:
        job_id_str: The job ID to cancel
        db: Database session
        
    Returns:
        GisExportJobStatusResponse: Updated job status
        
    Raises:
        HTTPException: If the job is not found or cannot be cancelled
    """
    try:
        # Get the job first
        job = await GisExportService.get_job_by_id(job_id_str, db)
        
        if not job:
            logger.warning(f"GIS export job cancellation request for unknown ID: {job_id_str}")
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND, 
                detail=f"GIS export job '{job_id_str}' not found."
            )
            
        # Can only cancel jobs that are pending or running
        if job.status not in ["PENDING", "RUNNING"]:
            logger.warning(f"Cannot cancel GIS export job {job_id_str} with status {job.status}")
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel job with status '{job.status}'. Only PENDING or RUNNING jobs can be cancelled."
            )
            
        # Mark job as failed with cancellation message
        updated_job = await GisExportService.mark_job_failed(
            job_id_str,
            "Job cancelled by user request",
            db,
            failure_reason="user_cancelled"
        )
        
        if not updated_job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel job due to database error."
            )
            
        logger.info(f"GIS export job {job_id_str} cancelled successfully")
        
        # Return updated job status
        return {
            "job_id": updated_job.job_id,
            "export_format": updated_job.export_format,
            "county_id": updated_job.county_id,
            "status": updated_job.status,
            "message": updated_job.message,
            "parameters": {
                "area_of_interest": updated_job.area_of_interest_json,
                "layers": updated_job.layers_json,
                **(updated_job.parameters_json or {})
            },
            "created_at": updated_job.created_at,
            "updated_at": updated_job.updated_at,
            "started_at": updated_job.started_at,
            "completed_at": updated_job.completed_at
        }
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error cancelling GIS export job: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )


@router.get("/health", summary="Health check for GIS Export API")
async def health_check():
    """
    Health check endpoint for the GIS Export API.
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "healthy",
        "plugin": "gis_export",
        "version": "1.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }