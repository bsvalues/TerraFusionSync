"""
Fix Market Analysis Router

This script rebuilds the router.py file for the Market Analysis plugin with 
proper import structure to avoid circular dependencies.
"""

import os
import shutil

# Define the path to the market analysis router
ROUTER_PATH = "terrafusion_sync/plugins/market_analysis/router.py"

# Create a backup of the existing file
if os.path.exists(ROUTER_PATH):
    backup_path = f"{ROUTER_PATH}.bak"
    shutil.copy2(ROUTER_PATH, backup_path)
    print(f"Created backup at {backup_path}")

# Define the new content for the router file
ROUTER_CONTENT = """\"\"\"
TerraFusion SyncService - Market Analysis Plugin - Router

This module provides the FastAPI router for the Market Analysis plugin,
connecting HTTP endpoints to service layer functions.
\"\"\"

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime as dt
import uuid

# Import database and model dependencies
from terrafusion_sync.database import get_db_session
from terrafusion_sync.core_models import MarketAnalysisJob

# Import schemas
from .schemas import (
    MarketAnalysisRunRequest,
    MarketAnalysisJobStatusResponse,
    MarketAnalysisResultData,
    MarketAnalysisJobResultResponse,
    MarketTrendDataPoint
)

# Import service functionality - NOT tasks which causes circular imports
from .service import (
    create_analysis_job,
    get_analysis_job,
    list_analysis_jobs,
    update_job_status,
    expire_stale_jobs,
    get_metrics_data
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize router with proper prefix
router = APIRouter(prefix="/plugins/market-analysis", tags=["Market Analysis"])

# Log successful import
print("[✅] market_analysis.router module loaded successfully.")

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    \"\"\"
    Health check endpoint for the Market Analysis plugin.
    \"\"\"
    return {
        "status": "ok",
        "plugin": "market_analysis",
        "version": "1.0.0",
        "timestamp": dt.now().isoformat()
    }

# --- Utility Functions ---

def _convert_model_to_schema_dict(model):
    \"\"\"
    Convert a SQLAlchemy model instance to a dict with compatible Python types for Pydantic schemas.
    \"\"\"
    if model is None:
        return None
        
    result = {}
    for column in inspect(model).mapper.column_attrs:
        name = column.key
        value = getattr(model, name)
        
        # Ensure value is a Python native type
        if value is not None:
            # Handle specific type conversions
            if isinstance(value, dt):
                result[name] = value
            elif hasattr(value, '_sa_instance_state'):
                # Handle nested SQLAlchemy models
                result[name] = _convert_model_to_schema_dict(value)
            else:
                # Convert to string if not a basic type
                if not isinstance(value, (str, int, float, bool, dict, list)):
                    result[name] = str(value)
                else:
                    result[name] = value
        else:
            result[name] = None
    
    return result

# --- API Endpoints ---

@router.post("/run", response_model=MarketAnalysisJobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_market_analysis(
    request: MarketAnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    \"\"\"
    Run a market analysis job.
    
    This endpoint accepts a market analysis request and queues it for background processing.
    \"\"\"
    # Ensure we're using the db session correctly
    if hasattr(db, '__aenter__') and not hasattr(db, 'execute'):
        # We have a session factory or context manager, not a session
        async with db as session:
            return await _run_market_analysis_impl(request, background_tasks, session)
    else:
        # We already have a session
        return await _run_market_analysis_impl(request, background_tasks, db)

async def _run_market_analysis_impl(
    request: MarketAnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession
) -> MarketAnalysisJobStatusResponse:
    \"\"\"Implementation of job run logic.\"\"\"
    try:
        # Create a new job record using the service function
        job = await create_analysis_job(
            db=db,
            county_id=request.county_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters
        )
        
        # Record job submission metric with core metrics
        # Uses dynamic import to avoid circular dependencies
        import terrafusion_sync.metrics as core_metrics
        core_metrics.MARKET_ANALYSIS_JOBS_SUBMITTED.labels(
            county_id=request.county_id,
            analysis_type=request.analysis_type
        ).inc()
        
        # Lazily import tasks module to avoid circular import
        from .tasks import run_analysis_job
        
        # Add background task to process the job
        background_tasks.add_task(
            run_analysis_job,
            get_db_session,  # Pass the session factory
            str(job.job_id),
            str(job.analysis_type),
            str(job.county_id),
            job.parameters_json
        )
        
        # Return the job status response
        return MarketAnalysisJobStatusResponse(
            job_id=str(job.job_id),
            analysis_type=str(job.analysis_type),
            county_id=str(job.county_id),
            status=str(job.status),
            message=str(job.message) if job.message else None,
            parameters=job.parameters_json,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=None,
            completed_at=None
        )
        
    except Exception as e:
        logger.error(f"Failed to create market analysis job: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate market analysis job: {str(e)}"
        )

@router.get("/status/{job_id}", response_model=MarketAnalysisJobStatusResponse)
async def get_market_analysis_status(job_id: str, db: AsyncSession = Depends(get_db_session)):
    \"\"\"
    Get the status of a market analysis job.
    \"\"\"
    # Ensure we're using the db session correctly
    if hasattr(db, '__aenter__') and not hasattr(db, 'execute'):
        # We have a session factory or context manager, not a session
        async with db as session:
            return await _get_market_analysis_status_impl(job_id, session)
    else:
        # We already have a session
        return await _get_market_analysis_status_impl(job_id, db)

async def _get_market_analysis_status_impl(job_id: str, db: AsyncSession) -> MarketAnalysisJobStatusResponse:
    \"\"\"Implementation of job status retrieval logic.\"\"\"
    # Use service function to get the job
    job = await get_analysis_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market analysis job with ID {job_id} not found"
        )
    
    # Convert to response model
    return MarketAnalysisJobStatusResponse(
        job_id=str(job.job_id),
        analysis_type=str(job.analysis_type),
        county_id=str(job.county_id),
        status=str(job.status),
        message=str(job.message) if job.message else None,
        parameters=job.parameters_json,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )

@router.get("/results/{job_id}", response_model=MarketAnalysisJobResultResponse)
async def get_market_analysis_results(job_id: str, db: AsyncSession = Depends(get_db_session)):
    \"\"\"
    Get the results of a completed market analysis job.
    \"\"\"
    # Ensure we're using the db session correctly
    if hasattr(db, '__aenter__') and not hasattr(db, 'execute'):
        # We have a session factory or context manager, not a session
        async with db as session:
            return await _get_market_analysis_results_impl(job_id, session)
    else:
        # We already have a session
        return await _get_market_analysis_results_impl(job_id, db)

async def _get_market_analysis_results_impl(job_id: str, db: AsyncSession) -> MarketAnalysisJobResultResponse:
    \"\"\"Implementation of job results retrieval logic.\"\"\"
    # Use service function to get the job
    job = await get_analysis_job(db, job_id)
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market analysis job with ID {job_id} not found"
        )
    
    # Check if job is completed
    if str(job.status) != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market analysis job is not completed (current status: {job.status})"
        )
    
    # Create base job status response
    job_status_response = MarketAnalysisJobStatusResponse(
        job_id=str(job.job_id),
        analysis_type=str(job.analysis_type),
        county_id=str(job.county_id),
        status=str(job.status),
        message=str(job.message) if job.message else None,
        parameters=job.parameters_json,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )

    # Prepare result data
    trends = None
    result_summary = None
    result_data_location = None
    
    # Extract result data from job
    if job.result_summary_json:
        result_summary = job.result_summary_json
        
        # Extract trends if available
        if result_summary and 'trends' in result_summary:
            trends = result_summary.pop('trends', None)
    
    # Get result location if available
    if job.result_data_location:
        result_data_location = str(job.result_data_location)
    
    # Create the result data model
    result_data = MarketAnalysisResultData(
        result_summary=result_summary,
        result_data_location=result_data_location,
        trends=trends
    )
    
    # Return the full response with job status and results
    return MarketAnalysisJobResultResponse(
        **job_status_response.model_dump(),  # Use all fields from status response
        result=result_data
    )

@router.get("/list", response_model=List[MarketAnalysisJobStatusResponse])
async def list_market_analysis_jobs(
    county_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db_session)
):
    \"\"\"
    List market analysis jobs with optional filtering.
    \"\"\"
    # Ensure we're using the db session correctly
    if hasattr(db, '__aenter__') and not hasattr(db, 'execute'):
        # We have a session factory or context manager, not a session
        async with db as session:
            return await _list_market_analysis_jobs_impl(
                session, county_id, analysis_type, status, limit
            )
    else:
        # We already have a session
        return await _list_market_analysis_jobs_impl(
            db, county_id, analysis_type, status, limit
        )

async def _list_market_analysis_jobs_impl(
    db: AsyncSession,
    county_id: Optional[str],
    analysis_type: Optional[str],
    status: Optional[str],
    limit: int
) -> List[MarketAnalysisJobStatusResponse]:
    \"\"\"Implementation of job listing logic.\"\"\"
    # Use service function to list jobs with filters
    jobs = await list_analysis_jobs(
        db=db,
        county_id=county_id,
        analysis_type=analysis_type,
        status=status,
        limit=limit
    )
    
    # Convert each job to response model with proper type handling
    job_responses = []
    for job in jobs:
        # Create response for each job
        job_responses.append(
            MarketAnalysisJobStatusResponse(
                job_id=str(job.job_id),
                analysis_type=str(job.analysis_type),
                county_id=str(job.county_id),
                status=str(job.status),
                message=str(job.message) if job.message else None,
                parameters=job.parameters_json,
                created_at=job.created_at,
                updated_at=job.updated_at,
                started_at=job.started_at,
                completed_at=job.completed_at
            )
        )
    
    return job_responses
"""

# Write the new content to the router file
with open(ROUTER_PATH, "w") as f:
    f.write(ROUTER_CONTENT)

print(f"Successfully updated the Market Analysis router at {ROUTER_PATH}")
print("Restart the syncservice workflow to apply changes.")