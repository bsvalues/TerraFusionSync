"""
TerraFusion SyncService - GIS Export Plugin - Router

This module defines the FastAPI router for GIS Export endpoints, integrating with county-specific
configurations for proper format validation and default parameters.
"""

from fastapi import APIRouter, Depends, HTTPException, status as fastapi_status, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

# Import DB session factory
from terrafusion_sync.database import get_async_session
from terrafusion_sync.plugins.gis_export.service import GisExportService
from terrafusion_sync.plugins.gis_export.county_config import get_county_config
from terrafusion_sync.plugins.gis_export.schemas import (
    GisExportRunRequest, 
    GisExportJobStatusResponse, 
    GisExportResultData,
    GisExportJobResultResponse
)

# Import Prometheus metrics if available
try:
    from terrafusion_sync.plugins.gis_export.metrics import (
        GisExportMetrics,
        register_metrics
    )
    # Register metrics to ensure they're available
    register_metrics()
    
    # Get references to the metrics for convenience
    from terrafusion_sync.plugins.gis_export.metrics import (
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL,
        GIS_EXPORT_JOBS_COMPLETED_TOTAL,
        GIS_EXPORT_JOBS_FAILED_TOTAL,
        GIS_EXPORT_PROCESSING_DURATION_SECONDS,
        GIS_EXPORT_FILE_SIZE_KB,
        GIS_EXPORT_RECORD_COUNT
    )
    
    metrics_available = True
    logging.info("GIS Export metrics module loaded and metrics registered")
except ImportError:
    metrics_available = False
    logging.warning("GIS Export metrics module not available, metrics will not be recorded")

logger = logging.getLogger(__name__)
router = APIRouter()

# --- API Endpoints for GIS Export Plugin ---

@router.post("/run", 
             response_model=GisExportJobStatusResponse, 
             summary="Submit a GIS export job for processing",
             description="""
             Submit a GIS export job for background processing. 
             
             The export format must be one of the formats supported by the county configuration.
             Default parameters will be applied if not provided in the request.
             """)
async def run_gis_export_job(
    request_data: GisExportRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Submit a GIS data export job for processing.

    This endpoint accepts parameters for generating a geographic data export
    and queues a background task to process the request.
    """
    try:
        # Get default parameters from county configuration if not provided
        if request_data.parameters is None:
            request_data.parameters = GisExportService.get_default_export_parameters(request_data.county_id)
        
        # Create job
        job = await GisExportService.create_export_job(
            export_format=request_data.format,
            county_id=request_data.county_id,
            area_of_interest=request_data.area_of_interest,
            layers=request_data.layers,
            parameters=request_data.parameters,
            db=db
        )
        
        # Record metrics if available
        if metrics_available:
            GIS_EXPORT_JOBS_SUBMITTED_TOTAL.labels(
                county_id=request_data.county_id,
                export_format=request_data.format
            ).inc()
        
        # Start processing in background
        background_tasks.add_task(
            _process_gis_export_job,
            job.job_id,
            db
        )
        
        # Prepare response
        response = GisExportJobStatusResponse(
            job_id=job.job_id,
            county_id=job.county_id,
            export_format=job.export_format,
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
        
        return response
        
    except ValueError as e:
        # Handle validation errors
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Error creating GIS export job: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create export job: {str(e)}"
        )

@router.get("/status/{job_id}", 
            response_model=GisExportJobStatusResponse,
            summary="Check the status of a GIS export job",
            description="Get the current status of a previously submitted GIS export job.")
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get the status of a GIS export job.
    
    Args:
        job_id: The ID of the job to check
    """
    try:
        # Get job from database
        job = await GisExportService.get_job_by_id(job_id, db)
        
        if not job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job {job_id} not found"
            )
        
        # Create response
        return GisExportJobStatusResponse(
            job_id=job.job_id,
            county_id=job.county_id,
            export_format=job.export_format,
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
        logger.error(f"Error getting GIS export job status: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/results/{job_id}", 
           response_model=GisExportJobResultResponse,
           summary="Get the results of a completed GIS export job",
           description="Retrieve the results of a completed GIS export job, including file location and metadata.")
async def get_job_results(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get the results of a completed GIS export job.
    
    Args:
        job_id: The ID of the job
    """
    try:
        # Get job from database
        job = await GisExportService.get_job_by_id(job_id, db)
        
        if not job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job {job_id} not found"
            )
        
        # Check if job is completed
        if job.status != "COMPLETED":
            raise HTTPException(
                status_code=fastapi_status.HTTP_400_BAD_REQUEST,
                detail=f"GIS export job {job_id} is not completed (current status: {job.status})"
            )
        
        # Create result data
        result_data = GisExportResultData(
            file_location=job.result_file_location,
            file_size_kb=job.result_file_size_kb,
            record_count=job.result_record_count
        )
        
        # Create response
        return GisExportJobResultResponse(
            job_id=job.job_id,
            county_id=job.county_id,
            export_format=job.export_format,
            status=job.status,
            message=job.message,
            parameters={
                "area_of_interest": job.area_of_interest_json,
                "layers": job.layers_json,
                **(job.parameters_json or {})
            },
            created_at=job.created_at,
            completed_at=job.completed_at,
            result=result_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting GIS export job results: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job results: {str(e)}"
        )

@router.post("/cancel/{job_id}", 
            response_model=GisExportJobStatusResponse,
            summary="Cancel a running or pending GIS export job",
            description="Cancel a GIS export job that is currently running or pending.")
async def cancel_job(
    job_id: str,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Cancel a GIS export job.
    
    Args:
        job_id: The ID of the job to cancel
    """
    try:
        # Cancel job
        cancelled_job = await GisExportService.cancel_job(job_id, db)
        
        if not cancelled_job:
            raise HTTPException(
                status_code=fastapi_status.HTTP_404_NOT_FOUND,
                detail=f"GIS export job {job_id} not found"
            )
        
        # Create response
        return GisExportJobStatusResponse(
            job_id=cancelled_job.job_id,
            county_id=cancelled_job.county_id,
            export_format=cancelled_job.export_format,
            status=cancelled_job.status,
            message=cancelled_job.message,
            parameters={
                "area_of_interest": cancelled_job.area_of_interest_json,
                "layers": cancelled_job.layers_json,
                **(cancelled_job.parameters_json or {})
            },
            created_at=cancelled_job.created_at,
            updated_at=cancelled_job.updated_at,
            started_at=cancelled_job.started_at,
            completed_at=cancelled_job.completed_at
        )
    
    except ValueError as e:
        # Handle validation errors (e.g., job already completed)
        raise HTTPException(
            status_code=fastapi_status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling GIS export job: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel job: {str(e)}"
        )

@router.get("/list", 
           response_model=List[GisExportJobStatusResponse],
           summary="List GIS export jobs with optional filtering",
           description="Get a list of GIS export jobs with optional filtering by county, status, etc.")
async def list_jobs(
    county_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_session)
):
    """
    List GIS export jobs with optional filtering.
    
    Args:
        county_id: Optional county ID to filter by
        status: Optional status to filter by
        limit: Maximum number of jobs to return (default: 100)
        offset: Offset for pagination (default: 0)
    """
    try:
        # Get jobs from database
        jobs = await GisExportService.list_jobs(county_id, status, limit, offset, db)
        
        # Create response
        return [
            GisExportJobStatusResponse(
                job_id=job.job_id,
                county_id=job.county_id,
                export_format=job.export_format,
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
            for job in jobs
        ]
    
    except Exception as e:
        logger.error(f"Error listing GIS export jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list jobs: {str(e)}"
        )

@router.get("/formats/{county_id}", 
           response_model=List[str],
           summary="Get supported export formats for a county",
           description="Get a list of supported export formats for a specific county based on its configuration.")
async def get_supported_formats(county_id: str):
    """
    Get supported export formats for a county.
    
    Args:
        county_id: The ID of the county
    """
    try:
        # Get formats from county configuration
        formats = get_county_config().get_available_formats(county_id)
        return formats
    
    except Exception as e:
        logger.error(f"Error getting supported formats for county {county_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported formats: {str(e)}"
        )

@router.get("/defaults/{county_id}", 
           response_model=Dict[str, Any],
           summary="Get default export parameters for a county",
           description="Get the default export parameters for a specific county based on its configuration.")
async def get_county_defaults(county_id: str):
    """
    Get default export parameters for a county.
    
    Args:
        county_id: The ID of the county
    """
    try:
        # Get defaults from service
        defaults = GisExportService.get_default_export_parameters(county_id)
        return defaults
    
    except Exception as e:
        logger.error(f"Error getting default parameters for county {county_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=fastapi_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get default parameters: {str(e)}"
        )

@router.get("/health", 
           summary="Health check for GIS Export API",
           description="Check if the GIS Export plugin is healthy and operational.")
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
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Background processing functions ---

async def _process_gis_export_job(job_id: str, db: AsyncSession):
    """
    Process a GIS export job in the background.
    
    Args:
        job_id: The ID of the job to process
        db: Database session
    """
    # Create a new database session for the background task
    async with get_async_session() as db_session:
        try:
            # Get the job
            job = await GisExportService.get_job_by_id(job_id, db_session)
            
            if not job:
                logger.error(f"GIS export job {job_id} not found for processing")
                return
            
            # Update job status to RUNNING
            await GisExportService.update_job_status(
                job_id=job_id,
                status="RUNNING",
                message="Job processing started",
                db=db_session
            )
            
            # Record start time for metrics
            start_time = datetime.utcnow()
            
            # Simulate GIS export processing (in a real implementation, this would perform the actual export)
            result_location, result_size_kb, record_count = await _simulate_gis_export_processing(
                job.county_id, 
                job.export_format, 
                job.area_of_interest_json, 
                job.layers_json, 
                job.parameters_json
            )
            
            # Calculate processing duration for metrics
            processing_duration = (datetime.utcnow() - start_time).total_seconds()
            
            # Update job status to COMPLETED
            await GisExportService.update_job_status(
                job_id=job_id,
                status="COMPLETED",
                message="Export completed successfully",
                result_file_location=result_location,
                result_file_size_kb=result_size_kb,
                result_record_count=record_count,
                db=db_session
            )
            
            # Record metrics if available
            if metrics_available:
                GIS_EXPORT_JOBS_COMPLETED_TOTAL.labels(
                    county_id=job.county_id,
                    export_format=job.export_format
                ).inc()
                
                GIS_EXPORT_PROCESSING_DURATION_SECONDS.labels(
                    county_id=job.county_id,
                    export_format=job.export_format
                ).observe(processing_duration)
                
                if result_size_kb:
                    GIS_EXPORT_FILE_SIZE_KB.labels(
                        county_id=job.county_id,
                        export_format=job.export_format
                    ).observe(result_size_kb)
                
                if record_count:
                    GIS_EXPORT_RECORD_COUNT.labels(
                        county_id=job.county_id,
                        export_format=job.export_format
                    ).observe(record_count)
            
            logger.info(f"GIS export job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error processing GIS export job {job_id}: {e}", exc_info=True)
            
            # Update job status to FAILED
            try:
                await GisExportService.update_job_status(
                    job_id=job_id,
                    status="FAILED",
                    message=f"Export failed: {str(e)}",
                    db=db_session
                )
                
                # Record failure metric if available
                if metrics_available:
                    GIS_EXPORT_JOBS_FAILED_TOTAL.labels(
                        county_id=job.county_id if job else "unknown",
                        export_format=job.export_format if job else "unknown",
                        error_type=type(e).__name__
                    ).inc()
                    
            except Exception as update_error:
                logger.error(f"Error updating failed job status: {update_error}", exc_info=True)

async def _simulate_gis_export_processing(
    county_id: str, 
    export_format: str, 
    area_of_interest: Dict[str, Any], 
    layers: List[str], 
    parameters: Dict[str, Any]
) -> Tuple[str, int, int]:
    """
    Simulate processing a GIS export job (for development/testing).
    
    In a real implementation, this would:
    1. Connect to the county's geospatial database
    2. Query the data based on area_of_interest and layers
    3. Format the data according to export_format
    4. Save the result to storage (e.g., S3, Azure Blob)
    5. Return the file location and metadata
    
    Args:
        county_id: ID of the county
        export_format: Format of the export
        area_of_interest: GeoJSON object defining the area of interest
        layers: List of layers to export
        parameters: Additional parameters for the export
        
    Returns:
        Tuple of (file_location, file_size_kb, record_count)
        
    Raises:
        Exception: If processing fails
    """
    import asyncio
    import random
    from datetime import datetime
    
    # Get county configuration for realistic processing
    county_config = get_county_config()
    
    # Check if this is a test for failure (special test format)
    if export_format == "FAIL_FORMAT_SIM":
        raise Exception("Simulated failure for testing purposes")
    
    # Simulate processing delay (1-3 seconds)
    await asyncio.sleep(random.uniform(1, 3))
    
    # Generate a realistic file location based on county and format
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    # For testing, we just return a file path, but in reality this would be a storage URL
    file_location = f"https://storage.terrafusion.com/{county_id}/exports/{timestamp}_{county_id}_export.{export_format.lower()}"
    
    # Calculate a realistic file size based on the number of layers and area size
    # In a real implementation, this would be the actual file size
    base_size = 250  # Base size in KB
    layer_factor = len(layers) * 50  # Each layer adds 50KB
    
    # Use the county's configuration for realistic sizes
    coordinate_system = parameters.get("coordinate_system", 
                                     county_config.get_default_coordinate_system(county_id))
    simplify_tolerance = parameters.get("simplify_tolerance", 0.0001)
    
    # Adjust size based on simplification (more simplification = smaller file)
    simplify_factor = 1.0 / (simplify_tolerance * 10000) if simplify_tolerance > 0 else 1.0
    simplify_factor = min(simplify_factor, 5.0)  # Cap the factor
    
    # Calculate final size
    file_size_kb = int((base_size + layer_factor) * simplify_factor)
    
    # Calculate a realistic record count based on the area and layers
    # In reality, this would be the actual count of records exported
    record_count = random.randint(100, 5000) * len(layers)
    
    # Return the simulated results
    return file_location, file_size_kb, record_count