"""
TerraFusion SyncService - Market Analysis Plugin - Router

This module provides the FastAPI router and service logic for the Market Analysis plugin.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, func
import logging
from typing import Dict, Any, Optional, List
import uuid
import asyncio
import time
import datetime

# Database connector
from terrafusion_sync.database import get_db_session
from terrafusion_sync.core_models import MarketAnalysisJob

# Import metrics
from terrafusion_sync.metrics import (
    MARKET_ANALYSIS_JOBS_SUBMITTED,
    MARKET_ANALYSIS_JOBS_COMPLETED,
    MARKET_ANALYSIS_JOBS_FAILED,
    MARKET_ANALYSIS_PROCESSING_DURATION_SECONDS,
    MARKET_ANALYSIS_JOBS_PENDING,
    MARKET_ANALYSIS_JOBS_IN_PROGRESS,
    track_market_analysis_job
)

# Import schemas
from .schemas import (
    MarketAnalysisRunRequest,
    MarketAnalysisJobStatusResponse,
    MarketAnalysisResultData,
    MarketAnalysisJobResultResponse,
    MarketTrendDataPoint
)

logger = logging.getLogger(__name__)
router = APIRouter()

# --- Background Processing Logic ---
async def _process_market_analysis_job(
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters: Optional[Dict[str, Any]],
    db_session_factory
):
    """Background task to process a market analysis job."""
    start_process_time = time.monotonic()
    job_final_status = "UNKNOWN"

    async with db_session_factory() as db:
        try:
            logger.info(f"MarketAnalysisJob {job_id}: Starting background processing for '{analysis_type}', county '{county_id}'")
            # Update job to RUNNING status
            await db.execute(
                update(MarketAnalysisJob)
                .where(MarketAnalysisJob.job_id == job_id)
                .values(
                    status="RUNNING",
                    started_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                    message="Analysis in progress"
                )
            )
            await db.commit()
            
            # Increment the in-progress counter and decrement pending
            MARKET_ANALYSIS_JOBS_PENDING.dec()
            MARKET_ANALYSIS_JOBS_IN_PROGRESS.inc()

            # Simulate processing time - to be replaced with actual analysis logic
            await asyncio.sleep(3)  

            # Based on analysis type, perform different calculations
            result_summary = {}
            trends = []
            
            # Example implementation for price trend analysis
            if analysis_type.lower() == "price_trend_by_zip":
                start_date = parameters.get("start_date") if parameters else "2024-01-01"
                end_date = parameters.get("end_date") if parameters else "2024-12-31"
                zip_codes = parameters.get("zip_codes") if parameters else []
                
                # This would be replaced with actual database queries in production
                # For demonstration, generate sample data
                quarters = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
                for quarter in quarters:
                    trends.append({
                        "period": quarter,
                        "average_price": 450000 + (quarters.index(quarter) * 12500),
                        "median_price": 425000 + (quarters.index(quarter) * 10000),
                        "sales_volume": 125 - (quarters.index(quarter) * 5),
                        "price_per_sqft": 350 + (quarters.index(quarter) * 5.5)
                    })
                
                result_summary = {
                    "key_finding": "Market prices increased by 5% year-over-year",
                    "data_points_analyzed": len(zip_codes) * len(quarters) if zip_codes else len(quarters) * 5,
                    "recommendation": "Market conditions favorable for revaluation",
                    "analyzed_zip_codes": zip_codes if zip_codes else ["90210", "90211", "90212", "90220", "90230"]
                }
            
            # Update job with success status and results
            result_data_location = f"/data/analysis_results/{county_id}/{analysis_type}/{job_id}.parquet"
            
            await db.execute(
                update(MarketAnalysisJob)
                .where(MarketAnalysisJob.job_id == job_id)
                .values(
                    status="COMPLETED",
                    completed_at=datetime.datetime.utcnow(),
                    updated_at=datetime.datetime.utcnow(),
                    message="Analysis completed successfully",
                    result_summary_json=result_summary,
                    result_data_location=result_data_location
                )
            )
            await db.commit()
            
            # Record job completion metric
            MARKET_ANALYSIS_JOBS_COMPLETED.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).inc()
            
            job_final_status = "COMPLETED"
            logger.info(f"MarketAnalysisJob {job_id}: Processing completed successfully")
            
        except Exception as e:
            job_final_status = "FAILED"
            error_message = f"Error processing market analysis job: {str(e)}"
            logger.error(f"MarketAnalysisJob {job_id}: {error_message}", exc_info=True)
            
            # Record failure in database
            try:
                await db.execute(
                    update(MarketAnalysisJob)
                    .where(MarketAnalysisJob.job_id == job_id)
                    .values(
                        status="FAILED",
                        completed_at=datetime.datetime.utcnow(),
                        updated_at=datetime.datetime.utcnow(),
                        message=error_message
                    )
                )
                await db.commit()
            except Exception as db_error:
                logger.error(f"MarketAnalysisJob {job_id}: Failed to update job status in database: {str(db_error)}")
            
            # Record failure metric
            MARKET_ANALYSIS_JOBS_FAILED.labels(
                county_id=county_id,
                analysis_type=analysis_type,
                failure_reason=type(e).__name__
            ).inc()
            
        finally:
            # Always decrement in-progress counter and record duration
            MARKET_ANALYSIS_JOBS_IN_PROGRESS.dec()
            duration = time.monotonic() - start_process_time
            MARKET_ANALYSIS_PROCESSING_DURATION_SECONDS.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).observe(duration)
            
            logger.info(f"MarketAnalysisJob {job_id}: Background task finished. Status: {job_final_status}, Duration: {duration:.2f}s")

# --- API Endpoints ---
@router.post("/run", response_model=MarketAnalysisJobStatusResponse, status_code=status.HTTP_202_ACCEPTED)
async def run_market_analysis(
    request: MarketAnalysisRunRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Run a market analysis job.
    
    This endpoint accepts a market analysis request and queues it for background processing.
    """
    # Generate a new UUID for the job
    job_id = str(uuid.uuid4())
    
    try:
        # Create new job record
        new_job = MarketAnalysisJob(
            job_id=job_id,
            analysis_type=request.analysis_type,
            county_id=request.county_id,
            status="PENDING",
            message="Market analysis job accepted and queued",
            parameters_json=request.parameters,
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        logger.info(f"MarketAnalysisJob {job_id}: Created for analysis type '{request.analysis_type}', county '{request.county_id}'")
        
        # Record job submission metric
        MARKET_ANALYSIS_JOBS_SUBMITTED.labels(
            county_id=request.county_id,
            analysis_type=request.analysis_type
        ).inc()
        
        # Increment pending jobs counter
        MARKET_ANALYSIS_JOBS_PENDING.inc()
        
        # Add background task to process the job
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy.orm import sessionmaker
        
        engine = db.get_bind()
        async_session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        background_tasks.add_task(
            _process_market_analysis_job,
            job_id,
            request.analysis_type,
            request.county_id,
            request.parameters,
            async_session_factory
        )
        
        return MarketAnalysisJobStatusResponse(
            job_id=job_id,
            analysis_type=request.analysis_type,
            county_id=request.county_id,
            status="PENDING",
            message="Market analysis job accepted and queued",
            parameters=request.parameters,
            created_at=new_job.created_at,
            updated_at=new_job.updated_at,
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
    """
    Get the status of a market analysis job.
    """
    result = await db.execute(
        select(MarketAnalysisJob).where(MarketAnalysisJob.job_id == job_id)
    )
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market analysis job with ID {job_id} not found"
        )
    
    return MarketAnalysisJobStatusResponse(
        job_id=str(job.job_id),
        analysis_type=str(job.analysis_type),
        county_id=str(job.county_id),
        status=str(job.status),
        message=str(job.message) if job.message else None,
        parameters=job.parameters_json if job.parameters_json else None,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at
    )

@router.get("/results/{job_id}", response_model=MarketAnalysisJobResultResponse)
async def get_market_analysis_results(job_id: str, db: AsyncSession = Depends(get_db_session)):
    """
    Get the results of a completed market analysis job.
    """
    result = await db.execute(
        select(MarketAnalysisJob).where(MarketAnalysisJob.job_id == job_id)
    )
    job = result.scalars().first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market analysis job with ID {job_id} not found"
        )
    
    if job.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Market analysis job is not completed (current status: {job.status})"
        )
    
    # Prepare trend data if available (in a real implementation, this might be loaded from a file)
    trends = None
    if job.analysis_type.lower() == "price_trend_by_zip" and job.result_summary_json:
        # This would typically be loaded from the result_data_location
        # For demo purposes, generate some trend data
        quarters = ["2024-Q1", "2024-Q2", "2024-Q3", "2024-Q4"]
        trends = [
            MarketTrendDataPoint(
                period=quarter,
                average_price=450000 + (quarters.index(quarter) * 12500),
                median_price=425000 + (quarters.index(quarter) * 10000),
                sales_volume=125 - (quarters.index(quarter) * 5),
                price_per_sqft=350 + (quarters.index(quarter) * 5.5)
            )
            for quarter in quarters
        ]
    
    result_data = MarketAnalysisResultData(
        result_summary=job.result_summary_json,
        trends=trends,
        result_data_location=job.result_data_location
    )
    
    return MarketAnalysisJobResultResponse(
        job_id=job.job_id,
        analysis_type=job.analysis_type,
        county_id=job.county_id,
        status=job.status,
        message=job.message,
        parameters=job.parameters_json,
        created_at=job.created_at,
        updated_at=job.updated_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
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
    """
    List market analysis jobs with optional filtering.
    """
    query = select(MarketAnalysisJob).order_by(MarketAnalysisJob.created_at.desc()).limit(limit)
    
    # Apply filters if provided
    if county_id:
        query = query.where(MarketAnalysisJob.county_id == county_id)
    if analysis_type:
        query = query.where(MarketAnalysisJob.analysis_type == analysis_type)
    if status:
        query = query.where(MarketAnalysisJob.status == status)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return [
        MarketAnalysisJobStatusResponse(
            job_id=job.job_id,
            analysis_type=job.analysis_type,
            county_id=job.county_id,
            status=job.status,
            message=job.message,
            parameters=job.parameters_json,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
        for job in jobs
    ]