"""
TerraFusion SyncService - Market Analysis Plugin - Router

This module provides the FastAPI router for the Market Analysis plugin,
exposing endpoints for job creation, status checking, and result retrieval.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.database import get_async_session
from terrafusion_sync.plugins.market_analysis.schemas import (
    MarketAnalysisRunRequest,
    MarketAnalysisJobStatusResponse,
    MarketAnalysisJobResultResponse
)
from terrafusion_sync.plugins.market_analysis.service import MarketAnalysisService

# Lazy load dependencies
# This helps prevent circular imports
SERVICE = None

# Configure logger
logger = logging.getLogger(__name__)

# Create router
plugin_router = APIRouter(prefix="/plugins/market-analysis", tags=["Market Analysis"])


def get_service(session_factory=Depends(get_async_session)):
    """Get the Market Analysis service instance with proper dependency injection."""
    global SERVICE
    if SERVICE is None:
        SERVICE = MarketAnalysisService(session_factory)
    return SERVICE


@plugin_router.get("/health", 
    summary="Check the health of the Market Analysis plugin",
    description="Returns basic health information for the Market Analysis plugin")
async def health_check():
    """
    Check if the Market Analysis plugin is healthy.
    """
    # Basic health check
    return {
        "status": "ok",
        "name": "Market Analysis Plugin",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@plugin_router.post("/run", 
    status_code=status.HTTP_202_ACCEPTED,
    summary="Run a market analysis job",
    description="Submit a market analysis job for processing")
async def run_analysis(
    request: MarketAnalysisRunRequest,
    service: MarketAnalysisService = Depends(get_service)
):
    """
    Run a market analysis job.
    """
    try:
        # Create job
        job_id = await service.create_job(
            county_id=request.county_id,
            analysis_type=request.analysis_type,
            parameters=request.parameters
        )
        
        return {
            "job_id": job_id,
            "status": "PENDING",
            "message": "Job created and queued for processing"
        }
    except Exception as e:
        logger.exception(f"Error running analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting job: {str(e)}"
        )


@plugin_router.get("/status/{job_id}", 
    response_model=MarketAnalysisJobStatusResponse,
    summary="Get the status of a market analysis job",
    description="Check the current status of a previously submitted market analysis job")
async def get_job_status(
    job_id: str = Path(..., description="ID of the job to check"),
    service: MarketAnalysisService = Depends(get_service)
):
    """
    Get the current status of a job.
    """
    result = await service.get_job_status(job_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
        
    return result


@plugin_router.get("/results/{job_id}", 
    response_model=MarketAnalysisJobResultResponse,
    summary="Get the results of a completed job",
    description="Retrieve the detailed results of a completed market analysis job")
async def get_job_results(
    job_id: str = Path(..., description="ID of the job to get results for"),
    service: MarketAnalysisService = Depends(get_service)
):
    """
    Get the results of a completed job.
    """
    result = await service.get_job_result(job_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID {job_id} not found"
        )
        
    if result.get("status") != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {result.get('status')}"
        )
        
    return result


@plugin_router.get("/list", 
    summary="List market analysis jobs",
    description="List market analysis jobs, optionally filtered by county")
async def list_jobs(
    county_id: Optional[str] = Query(None, description="Filter jobs by county ID"),
    limit: int = Query(100, description="Maximum number of jobs to return"),
    service: MarketAnalysisService = Depends(get_service)
):
    """
    List jobs, optionally filtered by county.
    """
    jobs = await service.list_jobs(county_id=county_id, limit=limit)
    return {"jobs": jobs, "count": len(jobs)}


@plugin_router.post("/cancel/{job_id}", 
    summary="Cancel a running job",
    description="Cancel a pending or running market analysis job")
async def cancel_job(
    job_id: str = Path(..., description="ID of the job to cancel"),
    service: MarketAnalysisService = Depends(get_service)
):
    """
    Cancel a job.
    """
    success = await service.cancel_job(job_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job cannot be cancelled. It may be completed, failed, or not found."
        )
        
    return {"status": "cancelled", "job_id": job_id}