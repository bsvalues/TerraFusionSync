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

# --- Placeholder Background Task for GIS Export ---
async def _simulate_gis_export_processing(
    job_id: str, 
    export_format: str, 
    county_id: str, 
    area_of_interest: Optional[Dict[str, Any]],
    layers: List[str],
    parameters: Optional[Dict[str, Any]], 
    db_session_factory: callable
):
    start_process_time = time.monotonic()
    job_final_status_for_metric = "UNKNOWN_FAILURE"
    logger.info(f"GisExportJob {job_id}: Background task initiated. Attempting to get DB session.")

    if not db_session_factory:
        logger.error(f"GisExportJob {job_id}: db_session_factory is None. Cannot proceed.")
        return

    async with db_session_factory() as db:
        logger.info(f"GisExportJob {job_id}: DB session acquired. Processing format '{export_format}', county '{county_id}'.")
        job_query = select(GisExportJob).where(GisExportJob.job_id == job_id)
        
        try:
            result = await db.execute(job_query)
            job = result.scalars().first()
            if not job:
                logger.error(f"GisExportJob {job_id}: Not found in DB at start of background task.")
                GIS_EXPORT_JOBS_FAILED_TOTAL.labels(county_id=county_id, export_format=export_format, failure_reason="job_not_found_in_bg").inc()
                return

            job.status = "RUNNING"
            job.started_at = datetime.datetime.utcnow()
            job.updated_at = datetime.datetime.utcnow()
            await db.commit()
            logger.info(f"GisExportJob {job_id}: Status updated to RUNNING in DB.")

            # --- Actual GIS Export Logic Placeholder ---
            logger.info(f"GisExportJob {job_id}: Simulating GIS export of format '{export_format}' for layers {layers} with AOI {area_of_interest} and params: {parameters}")
            # TODO: Implement actual GIS export logic. This would involve:
            # 1. Parsing area_of_interest and layers.
            # 2. Querying PropertyOperational (and potentially other tables or a PostGIS DB)
            #    using spatial filters based on AOI.
            # 3. Selecting relevant attributes for the specified layers.
            # 4. Converting data to the requested export_format (GeoJSON, Shapefile, KML).
            #    - For Shapefile/KML, this might involve creating multiple files and zipping them.
            #    - Libraries like GeoPandas, Fiona, shapely would be useful here.
            # 5. Storing the resulting file(s) (e.g., to S3 or a temporary file store).
            await asyncio.sleep(6) # Simulate processing time 
            # --- End Actual GIS Export Logic Placeholder ---

            if export_format == "FAIL_FORMAT_SIM": # For testing failure path
                job.status = "FAILED"
                job.message = "Simulated GIS export failure due to format."
                GIS_EXPORT_JOBS_FAILED_TOTAL.labels(county_id=county_id, export_format=export_format, failure_reason="simulated_format_failure").inc()
            else:
                job.status = "COMPLETED"
                job.message = f"GIS export ({export_format}) completed successfully."
                job.result_file_location = f"/gis_exports/{county_id}/{job_id}_{'_'.join(layers)}.{export_format.lower().replace('shapefile','zip')}"
                job.result_file_size_kb = 5120 # Simulated
                job.result_record_count = 2500 # Simulated
                
                # Update metrics
                GIS_EXPORT_JOBS_COMPLETED_TOTAL.labels(county_id=county_id, export_format=export_format).inc()
                GIS_EXPORT_FILE_SIZE_KB.labels(county_id=county_id, export_format=export_format).observe(job.result_file_size_kb)
                GIS_EXPORT_RECORD_COUNT.labels(county_id=county_id, export_format=export_format).observe(job.result_record_count)
            
            job_final_status_for_metric = job.status
            job.completed_at = datetime.datetime.utcnow()
            job.updated_at = datetime.datetime.utcnow()
            await db.commit()
            logger.info(f"GisExportJob {job_id}: Final status '{job.status}' and results committed to DB.")

        except Exception as e:
            job_final_status_for_metric = "EXCEPTION_FAILURE"
            logger.error(f"GisExportJob {job_id}: Unhandled exception during background GIS export: {e}", exc_info=True)
            GIS_EXPORT_JOBS_FAILED_TOTAL.labels(county_id=county_id, export_format=export_format, failure_reason="processing_exception").inc()
            
            # Try to update job status to FAILED
            try:
                job = result.scalars().first()
                if job:
                    job.status = "FAILED"
                    job.message = f"GIS export processing error: {str(e)}"
                    job.completed_at = datetime.datetime.utcnow()
                    job.updated_at = datetime.datetime.utcnow()
                    await db.commit()
                    logger.info(f"GisExportJob {job_id}: Updated status to FAILED after exception.")
            except Exception as update_ex:
                logger.error(f"GisExportJob {job_id}: Failed to update status after exception: {update_ex}")
        finally:
            duration = time.monotonic() - start_process_time
            GIS_EXPORT_PROCESSING_DURATION_SECONDS.labels(county_id=county_id, export_format=export_format).observe(duration)
            logger.info(f"GisExportJob {job_id}: Background task finished. Duration: {duration:.2f}s. Final status: {job_final_status_for_metric}")


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
    job_id = str(uuid.uuid4())
    new_job = GisExportJob(
        job_id=job_id,
        export_format=request_data.export_format,
        county_id=request_data.county_id,
        area_of_interest_json=request_data.area_of_interest,
        layers_json=request_data.layers,
        parameters_json=request_data.parameters,
        status="PENDING",
        message="GIS export job accepted and queued.",
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    
    try:
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        logger.info(f"GisExportJob {new_job.job_id} created in DB for format '{new_job.export_format}', county '{new_job.county_id}'.")
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL.labels(
            county_id=request_data.county_id, 
            export_format=request_data.export_format,
            status_on_submit="PENDING"
        ).inc()
    except Exception as e:
        logger.error(f"Failed to create GIS export job in DB for {request_data.export_format} / {request_data.county_id}: {e}", exc_info=True)
        raise HTTPException(status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initiate GIS export job.")

    # Get appropriate session factory for background task
    db_session_factory = async_session_maker
    
    # Start background task for processing
    background_tasks.add_task(
        _simulate_gis_export_processing, 
        new_job.job_id, 
        new_job.export_format, 
        new_job.county_id,
        new_job.area_of_interest_json,
        new_job.layers_json,
        new_job.parameters_json,
        db_session_factory
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
        job_uuid = job_id_str
    except ValueError:
        raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format.")
    
    logger.debug(f"Fetching status for GisExportJob ID: {job_uuid}")
    result = await db.execute(select(GisExportJob).where(GisExportJob.job_id == job_uuid))
    job = result.scalars().first()
    if not job:
        logger.warning(f"GisExportJob status request for unknown ID: {job_uuid}")
        raise HTTPException(status_code=fastapi_status.HTTP_404_NOT_FOUND, detail=f"GIS export job '{job_uuid}' not found.")
    
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
        job_uuid = job_id_str
    except ValueError:
        raise HTTPException(status_code=fastapi_status.HTTP_400_BAD_REQUEST, detail="Invalid job_id format.")

    logger.debug(f"Fetching results for GisExportJob ID: {job_uuid}")
    result = await db.execute(select(GisExportJob).where(GisExportJob.job_id == job_uuid))
    job = result.scalars().first()
    if not job:
        logger.warning(f"GisExportJob results request for unknown ID: {job_uuid}")
        raise HTTPException(status_code=fastapi_status.HTTP_404_NOT_FOUND, detail=f"GIS export job '{job_uuid}' not found.")

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
        logger.info(f"GisExportJob {job_uuid} results retrieved. File location: {job.result_file_location}")
    else:
        logger.info(f"GisExportJob {job_uuid} not yet completed or failed. Status: {job.status}")
        
    return {**job_status_data, "result": export_result_data}


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
    query = select(GisExportJob).order_by(GisExportJob.created_at.desc())
    
    if county_id:
        query = query.where(GisExportJob.county_id == county_id)
    
    if export_format:
        query = query.where(GisExportJob.export_format == export_format)
    
    if status:
        query = query.where(GisExportJob.status == status)
    
    query = query.limit(limit).offset(offset)
    
    try:
        result = await db.execute(query)
        jobs = result.scalars().all()
        
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
        return response_jobs
    except Exception as e:
        logger.error(f"Failed to list GIS export jobs: {e}", exc_info=True)
        raise HTTPException(status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list GIS export jobs: {str(e)}")


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