"""
TerraFusion SyncService - Market Analysis Plugin - Service

This module provides service layer functions for the Market Analysis plugin,
handling job lifecycle operations, state transitions, and business logic.
"""

import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_, or_, func, desc

from terrafusion_sync.core_models import MarketAnalysisJob

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
    
    # Create new job record
    new_job = MarketAnalysisJob(
        job_id=job_id,
        analysis_type=analysis_type,
        county_id=county_id,
        status="PENDING",
        message="Market analysis job accepted and queued",
        parameters_json=parameters,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(new_job)
    await db.commit()
    await db.refresh(new_job)
    
    logger.info(f"MarketAnalysisJob {job_id}: Created for analysis type '{analysis_type}', county '{county_id}'")
    
    return new_job

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
    query = select(MarketAnalysisJob).order_by(MarketAnalysisJob.created_at.desc()).limit(limit).offset(offset)
    
    # Apply filters if provided
    if county_id:
        query = query.where(MarketAnalysisJob.county_id == county_id)
    if analysis_type:
        query = query.where(MarketAnalysisJob.analysis_type == analysis_type)
    if status:
        query = query.where(MarketAnalysisJob.status == status)
    
    result = await db.execute(query)
    return list(result.scalars().all())

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
    # Prepare update values
    values = {
        "status": status,
        "updated_at": datetime.utcnow(),
    }
    
    # Add optional fields if provided
    if message is not None:
        values["message"] = message
    
    if result_summary is not None:
        values["result_summary_json"] = result_summary
    
    if result_data_location is not None:
        values["result_data_location"] = result_data_location
    
    # Add timestamps for specific status transitions
    if status == "RUNNING":
        values["started_at"] = datetime.utcnow()
    elif status in ["COMPLETED", "FAILED"]:
        values["completed_at"] = datetime.utcnow()
    
    # Execute update
    await db.execute(
        update(MarketAnalysisJob)
        .where(MarketAnalysisJob.job_id == job_id)
        .values(**values)
    )
    await db.commit()
    
    # Return updated job
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
    # Find jobs that have been running for too long
    timeout_threshold = datetime.utcnow() - datetime.timedelta(minutes=timeout_minutes)
    
    query = (
        select(MarketAnalysisJob)
        .where(
            and_(
                MarketAnalysisJob.status == "RUNNING",
                MarketAnalysisJob.started_at < timeout_threshold,
                MarketAnalysisJob.completed_at.is_(None)
            )
        )
    )
    
    result = await db.execute(query)
    stale_jobs = result.scalars().all()
    expired_job_ids = set()
    
    # Update each stale job
    for job in stale_jobs:
        job_id = job.job_id
        await update_job_status(
            db=db,
            job_id=job_id,
            status="FAILED",
            message=f"Job timed out after {timeout_minutes} minutes"
        )
        expired_job_ids.add(job_id)
        logger.warning(f"MarketAnalysisJob {job_id}: Expired after {timeout_minutes} minutes")
    
    return len(expired_job_ids), expired_job_ids

async def get_metrics_data(db: AsyncSession) -> Dict[str, Any]:
    """
    Get metrics data for the market analysis plugin.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with metrics data
    """
    # Count jobs by status
    status_counts = {}
    for status in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]:
        result = await db.execute(
            select(func.count())
            .where(MarketAnalysisJob.status == status)
        )
        status_counts[status] = result.scalar() or 0
    
    # Count jobs by analysis type
    analysis_type_counts = {}
    result = await db.execute(
        select(MarketAnalysisJob.analysis_type, func.count())
        .group_by(MarketAnalysisJob.analysis_type)
    )
    
    for row in result:
        analysis_type, count = row
        analysis_type_counts[analysis_type] = count
    
    # Count jobs by county
    county_counts = {}
    result = await db.execute(
        select(MarketAnalysisJob.county_id, func.count())
        .group_by(MarketAnalysisJob.county_id)
    )
    
    for row in result:
        county_id, count = row
        county_counts[county_id] = count
    
    return {
        "status_counts": status_counts,
        "analysis_type_counts": analysis_type_counts,
        "county_counts": county_counts,
        "total_jobs": sum(status_counts.values())
    }