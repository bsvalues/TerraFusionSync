"""
TerraFusion SyncService - Market Analysis Plugin - Service

This module provides service layer functions for the Market Analysis plugin,
handling job lifecycle operations, state transitions, and business logic.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, func, desc, text

from terrafusion_sync.core_models import MarketAnalysisJob
from terrafusion_sync.metrics import (
    MARKET_ANALYSIS_JOBS_FAILED,
    MARKET_ANALYSIS_JOBS_PENDING,
    MARKET_ANALYSIS_JOBS_IN_PROGRESS
)

logger = logging.getLogger(__name__)

async def create_analysis_job(
    db: AsyncSession,
    county_id: str,
    analysis_type: str,
    parameters: Optional[Dict[str, Any]] = None,
) -> MarketAnalysisJob:
    """
    Create a new market analysis job.
    
    Args:
        db: Database session
        county_id: County identifier
        analysis_type: Type of market analysis to perform
        parameters: Parameters for the analysis
        
    Returns:
        Created MarketAnalysisJob instance
    """
    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    job = MarketAnalysisJob(
        job_id=job_id,
        county_id=county_id,
        analysis_type=analysis_type,
        status="PENDING",
        message="Market analysis job created and queued",
        parameters_json=parameters,
        created_at=now,
        updated_at=now
    )
    
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    # Update metrics
    MARKET_ANALYSIS_JOBS_PENDING.inc()
    
    logger.info(f"Created market analysis job {job_id} for {county_id}, type: {analysis_type}")
    return job

async def get_analysis_job(db: AsyncSession, job_id: str) -> Optional[MarketAnalysisJob]:
    """
    Get a market analysis job by ID.
    
    Args:
        db: Database session
        job_id: Job identifier
        
    Returns:
        MarketAnalysisJob if found, None otherwise
    """
    result = await db.execute(
        select(MarketAnalysisJob).where(MarketAnalysisJob.job_id == job_id)
    )
    return result.scalars().first()

async def list_analysis_jobs(
    db: AsyncSession,
    county_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[MarketAnalysisJob]:
    """
    List market analysis jobs with optional filtering.
    
    Args:
        db: Database session
        county_id: Optional filter by county ID
        analysis_type: Optional filter by analysis type
        status: Optional filter by job status
        limit: Maximum number of records to return
        offset: Number of records to skip
        
    Returns:
        List of MarketAnalysisJob instances
    """
    query = select(MarketAnalysisJob).order_by(desc(MarketAnalysisJob.created_at))
    
    # Apply filters
    if county_id:
        query = query.where(MarketAnalysisJob.county_id == county_id)
    if analysis_type:
        query = query.where(MarketAnalysisJob.analysis_type == analysis_type)
    if status:
        query = query.where(MarketAnalysisJob.status == status)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()

async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    message: Optional[str] = None,
    result_summary: Optional[Dict[str, Any]] = None,
    result_data_location: Optional[str] = None
) -> Optional[MarketAnalysisJob]:
    """
    Update a market analysis job's status and related fields.
    
    Args:
        db: Database session
        job_id: Job identifier
        status: New status
        message: Optional status message
        result_summary: Optional result summary JSON
        result_data_location: Optional result data location
        
    Returns:
        Updated MarketAnalysisJob instance or None if not found
    """
    # Get the current job state to track metrics changes
    current_job = await get_analysis_job(db, job_id)
    if not current_job:
        logger.warning(f"Cannot update status for job {job_id}: job not found")
        return None
    
    # Prepare update values
    update_values = {
        "status": status,
        "updated_at": datetime.utcnow()
    }
    
    if message:
        update_values["message"] = message
        
    # Update timestamps based on status transition
    if status == "RUNNING" and current_job.status != "RUNNING":
        update_values["started_at"] = datetime.utcnow()
        
        # Update metrics for transition to RUNNING
        MARKET_ANALYSIS_JOBS_PENDING.dec()
        MARKET_ANALYSIS_JOBS_IN_PROGRESS.inc()
        
    if status in ["COMPLETED", "FAILED"] and current_job.status not in ["COMPLETED", "FAILED"]:
        update_values["completed_at"] = datetime.utcnow()
        
        # Update metrics for job completion or failure
        if current_job.status == "RUNNING":
            MARKET_ANALYSIS_JOBS_IN_PROGRESS.dec()
        elif current_job.status == "PENDING":
            MARKET_ANALYSIS_JOBS_PENDING.dec()
            
        # Track failures with reason
        if status == "FAILED":
            failure_reason = "unknown"
            if message:
                # Extract a short failure reason from message
                failure_reason = message.split(":")[0] if ":" in message else message
                failure_reason = failure_reason[:50]  # Truncate if too long
                
            MARKET_ANALYSIS_JOBS_FAILED.labels(
                county_id=current_job.county_id,
                analysis_type=current_job.analysis_type,
                failure_reason=failure_reason
            ).inc()
    
    # Add result data if provided
    if result_summary is not None:
        update_values["result_summary_json"] = result_summary
    
    if result_data_location is not None:
        update_values["result_data_location"] = result_data_location
    
    # Execute update
    await db.execute(
        update(MarketAnalysisJob)
        .where(MarketAnalysisJob.job_id == job_id)
        .values(**update_values)
    )
    await db.commit()
    
    # Return the updated job
    return await get_analysis_job(db, job_id)

async def expire_stale_jobs(
    db: AsyncSession, 
    timeout_minutes: int = 30
) -> Tuple[int, Set[str]]:
    """
    Find and expire stale market analysis jobs that have been running for too long.
    
    Args:
        db: Database session
        timeout_minutes: Timeout in minutes for running jobs
        
    Returns:
        Tuple of (count of expired jobs, set of expired job IDs)
    """
    # Calculate cutoff time
    cutoff_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
    
    # Find stale jobs
    query = select(MarketAnalysisJob).where(
        (MarketAnalysisJob.status == "RUNNING") &
        (MarketAnalysisJob.started_at < cutoff_time)
    )
    
    result = await db.execute(query)
    stale_jobs = result.scalars().all()
    
    expired_ids = set()
    expire_count = 0
    
    # Update each stale job
    for job in stale_jobs:
        job_id = job.job_id
        logger.warning(f"Expiring stale market analysis job {job_id} started at {job.started_at}")
        
        timeout_message = f"Job timed out after running for {timeout_minutes} minutes"
        result_summary = {
            "reason": "timeout",
            "message": timeout_message,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "expired_at": datetime.utcnow().isoformat()
        }
        
        await update_job_status(
            db=db,
            job_id=job_id,
            status="FAILED",
            message=timeout_message,
            result_summary=result_summary
        )
        
        expire_count += 1
        expired_ids.add(job_id)
        
        # Track failure with reason 'timeout'
        MARKET_ANALYSIS_JOBS_FAILED.labels(
            county_id=job.county_id,
            analysis_type=job.analysis_type,
            failure_reason="timeout"
        ).inc()
    
    return expire_count, expired_ids

async def get_metrics_data(db: AsyncSession) -> Dict[str, Any]:
    """
    Get metrics data for the market analysis plugin.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with metrics data
    """
    # Get counts by status
    result = await db.execute(
        select(
            MarketAnalysisJob.status,
            func.count().label("count")
        ).group_by(MarketAnalysisJob.status)
    )
    status_counts = {row[0]: row[1] for row in result.all()}
    
    # Get counts by analysis type
    result = await db.execute(
        select(
            MarketAnalysisJob.analysis_type,
            func.count().label("count")
        ).group_by(MarketAnalysisJob.analysis_type)
    )
    type_counts = {row[0]: row[1] for row in result.all()}
    
    # Get counts by county
    result = await db.execute(
        select(
            MarketAnalysisJob.county_id,
            func.count().label("count")
        ).group_by(MarketAnalysisJob.county_id)
    )
    county_counts = {row[0]: row[1] for row in result.all()}
    
    # Calculate average processing time for completed jobs
    result = await db.execute(
        select(
            func.avg(
                func.extract('epoch', MarketAnalysisJob.completed_at) - 
                func.extract('epoch', MarketAnalysisJob.started_at)
            ).label("avg_processing_time")
        ).where(
            (MarketAnalysisJob.status == "COMPLETED") &
            (MarketAnalysisJob.started_at.isnot(None)) &
            (MarketAnalysisJob.completed_at.isnot(None))
        )
    )
    avg_time = result.scalar() or 0
    
    return {
        "status_counts": status_counts,
        "type_counts": type_counts,
        "county_counts": county_counts,
        "avg_processing_time_seconds": float(avg_time),
        "total_jobs": sum(status_counts.values()),
        "timestamp": datetime.utcnow().isoformat()
    }