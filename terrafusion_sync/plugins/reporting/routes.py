"""
TerraFusion SyncService - Reporting Routes

This module defines API routes for the reporting plugin, handling report job creation,
status updates, and result retrieval.
"""

import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.database import get_db_session
from terrafusion_sync.core_models import ReportJob
from terrafusion_sync.metrics import track_api_request
from .schemas import (
    ReportJobCreate,
    ReportJobResponse,
    ReportJobUpdate,
    ReportJobListResponse,
    ErrorResponse,
    ReportJobRunRequest,
    ReportJobStatusResponse,
    ReportJobResultResponse,
    ReportJobResultDetail
)
from .service import (
    create_report_job,
    get_report_job,
    list_report_jobs,
    update_report_job_status,
    simulate_report_generation
)

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter(tags=["reporting"])


# Dependency for database sessions with improved transaction handling for testing
async def get_db():
    """
    Provides a database session for route handlers.
    This version ensures each request gets its own session 
    and tries to handle transaction conflicts.
    """
    async with get_db_session() as session:
        try:
            # No explicit transaction - we'll commit as needed in the handlers
            yield session
            # Try to commit any pending changes at the end
            # This helps with transaction handling in tests
            try:
                await session.commit()
            except Exception as commit_error:
                logger.warning(f"Warning: Could not commit at session end: {str(commit_error)}")
        except Exception as e:
            # If anything goes wrong, try to rollback
            try:
                await session.rollback()
            except Exception as rollback_error:
                logger.error(f"Error in rollback: {str(rollback_error)}")
            # Re-raise the original exception
            raise e
        finally:
            # Make sure the session is closed properly
            try:
                await session.close()
            except Exception as close_error:
                logger.error(f"Error closing session: {str(close_error)}")


@router.post(
    "/reports",
    response_model=ReportJobResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Create a new report job",
    description="Create a new report generation job with specified parameters. "
                "Returns the created job details including a unique report_id."
)
@track_api_request(endpoint="create_report_job")
async def create_new_report(
    request: ReportJobCreate,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobResponse:
    """Create a new report generation job."""
    try:
        job = await create_report_job(
            db=db,
            report_type=request.report_type,
            county_id=request.county_id,
            parameters=request.parameters
        )
        # Model to Pydantic conversion
        return ReportJobResponse.model_validate(job)
    except Exception as e:
        logger.error(f"Failed to create report job: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create report job: {str(e)}"
        )


@router.get(
    "/reports/{report_id}",
    response_model=ReportJobResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get report job details",
    description="Retrieve details for a specific report job by its ID."
)
@track_api_request(endpoint="get_report_details")
async def get_report_details(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobResponse:
    """Get details for a specific report job."""
    job = await get_report_job(db, report_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Report job with ID {report_id} not found"
        )
    return ReportJobResponse.model_validate(job)


@router.get(
    "/reports",
    response_model=ReportJobListResponse,
    responses={
        500: {"model": ErrorResponse}
    },
    summary="List report jobs",
    description="Retrieve a list of report jobs with optional filtering by county, type, status, and creation date."
)
@track_api_request(endpoint="list_reports")
async def list_reports(
    county_id: Optional[str] = Query(None, description="Filter by county ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    created_after: Optional[datetime] = Query(None, description="Filter jobs created after this datetime (ISO format)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobListResponse:
    """List report jobs with optional filtering."""
    try:
        jobs = await list_report_jobs(
            db=db,
            county_id=county_id,
            report_type=report_type,
            status=status,
            created_after=created_after,
            limit=limit,
            offset=offset
        )
        
        # Convert ORM objects to response schema
        return ReportJobListResponse(
            items=[ReportJobResponse.model_validate(job) for job in jobs],
            count=len(jobs)
        )
    except Exception as e:
        logger.error(f"Failed to list report jobs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list report jobs: {str(e)}"
        )


@router.patch(
    "/reports/{report_id}",
    response_model=ReportJobResponse,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Update report job status",
    description="Update the status of a report job and optionally provide result information."
)
@track_api_request(endpoint="update_report_status")
async def update_report_status(
    report_id: str,
    update_data: ReportJobUpdate,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobResponse:
    """Update the status of a report job."""
    try:
        # Validate status
        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
        if update_data.status and update_data.status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Update job
        updated_job = await update_report_job_status(
            db=db,
            report_id=report_id,
            status=update_data.status,
            message=update_data.message,
            result_location=update_data.result_location,
            result_metadata=update_data.result_metadata
        )
        
        if not updated_job:
            raise HTTPException(
                status_code=404,
                detail=f"Report job with ID {report_id} not found"
            )
            
        return ReportJobResponse.model_validate(updated_job)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to update report job status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update report job status: {str(e)}"
        )


@router.post(
    "/run",
    response_model=ReportJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Start a new report generation",
    description="Create and start a new report generation job with the specified parameters. "
                "Returns immediately with the created job in PENDING status."
)
@track_api_request(endpoint="run_report")
async def run_report(
    request: ReportJobRunRequest,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobResponse:
    """Create and start a new report generation job."""
    try:
        # Create the job first - this ensures it exists with PENDING status
        job = await create_report_job(
            db=db,
            report_type=request.report_type,
            county_id=request.county_id,
            parameters=request.parameters
        )
        
        # Explicitly commit the job creation
        await db.commit()
        logger.info(f"Created report job {job.report_id} with PENDING status")

        # Set a short processing delay based on complexity 
        # This simulates real-world processing time without using background tasks
        import random
        from datetime import datetime
        
        processing_time = random.uniform(0.2, 0.5)  # Shorter processing time for tests
        
        # Update to RUNNING status first
        await update_report_job_status(
            db=db,
            report_id=job.report_id,
            status="RUNNING",
            message="Report generation in progress"
        )
        # Commit the RUNNING status update
        await db.commit()
        logger.info(f"Updated report job {job.report_id} to RUNNING status")

        # For immediate simulation of results without background tasks
        if request.report_type == "FAILING_REPORT_SIM":
            # Simulate a failed report
            await update_report_job_status(
                db=db,
                report_id=job.report_id,
                status="FAILED",
                message="Simulated report generation failure"
            )
        else:
            # Simulate a successful report
            result_location = f"s3://terrafusion-reports/{job.county_id}/{job.report_type}/{job.report_id}.pdf"
            result_metadata = {
                "file_size_kb": 1024, 
                "pages": 10,
                "generation_time_seconds": processing_time,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            await update_report_job_status(
                db=db,
                report_id=job.report_id,
                status="COMPLETED",
                message="Report generation completed successfully",
                result_location=result_location,
                result_metadata=result_metadata
            )
        
        # Commit the final status update
        await db.commit()
        
        # Get the latest job state with a fresh query
        updated_job = await get_report_job(db, job.report_id)
        
        logger.info(f"Successfully completed report job {job.report_id} (type: {request.report_type}, status: {updated_job.status})")
        return ReportJobResponse.model_validate(updated_job)
    
    except Exception as e:
        # Attempt to rollback in case of error
        try:
            await db.rollback()
        except Exception as rollback_error:
            logger.error(f"Failed to rollback after error: {rollback_error}")
            
        logger.error(f"Failed to process report generation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start report generation: {str(e)}"
        )


@router.get(
    "/status/{report_id}",
    response_model=ReportJobStatusResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Check report job status",
    description="Get the current status of a report generation job."
)
@track_api_request(endpoint="get_report_status")
async def get_report_status(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobStatusResponse:
    """Get the status of a report job."""
    job = await get_report_job(db, report_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Report job with ID {report_id} not found"
        )
    
    # Map to the status response model
    return ReportJobStatusResponse(
        report_id=job.report_id,
        report_type=job.report_type,
        county_id=job.county_id,
        status=job.status,
        message=job.message,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.get(
    "/results/{report_id}",
    response_model=ReportJobResultResponse,
    responses={
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    },
    summary="Get report results",
    description="Get the results of a completed report job. Returns result location and metadata for completed jobs."
)
@track_api_request(endpoint="get_report_results")
async def get_report_results(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    req: Request = None
) -> ReportJobResultResponse:
    """Get the results of a completed report job."""
    job = await get_report_job(db, report_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Report job with ID {report_id} not found"
        )
    
    # Prepare response
    response = ReportJobResultResponse(
        report_id=job.report_id,
        report_type=job.report_type,
        county_id=job.county_id,
        status=job.status,
        message=job.message,
        result=None  # Default to None
    )
    
    # If the job is completed and has results, include them
    if job.status == "COMPLETED" and job.result_location:
        response.result = ReportJobResultDetail(
            result_location=job.result_location,
            result_metadata=job.result_metadata_json or {}
        )
    
    return response