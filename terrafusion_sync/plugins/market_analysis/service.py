"""
TerraFusion SyncService - Market Analysis Plugin - Service Layer

This module provides service functions for the Market Analysis plugin,
handling data access and business logic operations.
"""

import json
import uuid
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from terrafusion_sync.core_models import MarketAnalysisJob

# Configure logging
logger = logging.getLogger(__name__)

# --- Job Management Functions ---

async def create_analysis_job(
    db: AsyncSession,
    county_id: str,
    analysis_type: str,
    parameters: Dict[str, Any]
) -> MarketAnalysisJob:
    """
    Create a new market analysis job.
    
    Args:
        db: Database session
        county_id: County ID
        analysis_type: Type of analysis
        parameters: Analysis parameters
    
    Returns:
        Created MarketAnalysisJob instance
    """
    # Create a new job record
    job_id = str(uuid.uuid4())
    
    # Convert parameters to JSON if needed
    if not isinstance(parameters, str):
        parameters_json = json.dumps(parameters)
    else:
        parameters_json = parameters
    
    # Create job record
    job = MarketAnalysisJob(
        job_id=job_id,
        county_id=county_id,
        analysis_type=analysis_type,
        status="PENDING",
        message="Job created, waiting to run",
        parameters_json=parameters_json
    )
    
    # Save to database
    db.add(job)
    await db.commit()
    await db.refresh(job)
    
    logger.info(f"Created market analysis job {job_id} for county {county_id}")
    return job

async def get_analysis_job(
    db: AsyncSession, 
    job_id: str
) -> Optional[MarketAnalysisJob]:
    """
    Get a market analysis job by ID.
    
    Args:
        db: Database session
        job_id: Job ID
    
    Returns:
        MarketAnalysisJob if found, None otherwise
    """
    # Query the job
    result = await db.execute(
        select(MarketAnalysisJob).where(MarketAnalysisJob.job_id == job_id)
    )
    job = result.scalars().first()
    
    if not job:
        logger.warning(f"Market analysis job {job_id} not found")
    
    return job

async def list_analysis_jobs(
    db: AsyncSession,
    county_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10
) -> List[MarketAnalysisJob]:
    """
    List market analysis jobs with optional filtering.
    
    Args:
        db: Database session
        county_id: Optional county ID filter
        analysis_type: Optional analysis type filter
        status: Optional status filter
        limit: Maximum number of jobs to return
    
    Returns:
        List of MarketAnalysisJob instances
    """
    # Build query with filters
    query = select(MarketAnalysisJob)
    
    # Apply filters
    filters = []
    if county_id:
        filters.append(MarketAnalysisJob.county_id == county_id)
    if analysis_type:
        filters.append(MarketAnalysisJob.analysis_type == analysis_type)
    if status:
        filters.append(MarketAnalysisJob.status == status)
    
    # Apply filters to query
    if filters:
        query = query.where(and_(*filters))
    
    # Order by creation date (newest first)
    query = query.order_by(desc(MarketAnalysisJob.created_at))
    
    # Apply limit
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    return list(jobs)

async def update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    message: Optional[str] = None,
    started_at: Optional[datetime] = None,
    completed_at: Optional[datetime] = None,
    result_summary_json: Optional[Union[str, Dict[str, Any]]] = None,
    result_data_location: Optional[str] = None
) -> Optional[MarketAnalysisJob]:
    """
    Update the status of a market analysis job.
    
    Args:
        db: Database session
        job_id: Job ID
        status: New job status
        message: Status message
        started_at: Job start time
        completed_at: Job completion time
        result_summary_json: Summary of results (JSON string or dict)
        result_data_location: Location of result data
    
    Returns:
        Updated MarketAnalysisJob or None if not found
    """
    # Get the job
    job = await get_analysis_job(db, job_id)
    
    if not job:
        logger.warning(f"Cannot update status for job {job_id}: not found")
        return None
    
    # Update fields
    job.status = status
    
    if message is not None:
        job.message = message
        
    if started_at is not None:
        job.started_at = started_at
        
    if completed_at is not None:
        job.completed_at = completed_at
    
    # Handle result summary
    if result_summary_json is not None:
        # Convert dict to JSON string if needed
        if isinstance(result_summary_json, dict):
            job.result_summary_json = json.dumps(result_summary_json)
        else:
            job.result_summary_json = result_summary_json
    
    # Update result data location
    if result_data_location is not None:
        job.result_data_location = result_data_location
    
    # Always update the updated_at timestamp
    job.updated_at = datetime.now()
    
    # Save changes
    await db.commit()
    await db.refresh(job)
    
    logger.info(f"Updated job {job_id} status to {status}")
    return job

# --- Analysis Management Functions ---

async def get_county_market_overview(
    db: AsyncSession,
    county_id: str
) -> Dict[str, Any]:
    """
    Get a market overview for a county.
    
    Args:
        db: Database session
        county_id: County ID
    
    Returns:
        Dictionary with market overview data
    """
    # Get recent jobs for this county
    result = await db.execute(
        select(MarketAnalysisJob)
        .where(
            and_(
                MarketAnalysisJob.county_id == county_id,
                MarketAnalysisJob.status == "COMPLETED"
            )
        )
        .order_by(desc(MarketAnalysisJob.completed_at))
        .limit(20)
    )
    recent_jobs = result.scalars().all()
    
    # Create overview data
    overview = {
        "county_id": county_id,
        "timestamp": datetime.now().isoformat(),
        "recent_analyses": []
    }
    
    # Extract key metrics from recent analyses
    for job in recent_jobs:
        if not job.result_summary_json:
            continue
            
        # Parse result summary
        if isinstance(job.result_summary_json, str):
            try:
                result_summary = json.loads(job.result_summary_json)
            except:
                continue
        else:
            result_summary = job.result_summary_json
        
        # Extract relevant metrics based on analysis type
        metrics = {}
        if job.analysis_type == "price_trend_by_zip":
            metrics = {
                "zip_code": result_summary.get("zip_code"),
                "average_price": result_summary.get("average_price"),
                "price_change_percentage": result_summary.get("price_change_percentage")
            }
        elif job.analysis_type == "market_valuation":
            metrics = {
                "property_details": result_summary.get("property_details"),
                "estimated_value": result_summary.get("estimated_value"),
                "price_per_sqft": result_summary.get("price_per_sqft")
            }
        elif job.analysis_type == "sales_velocity":
            metrics = {
                "average_days_on_market": result_summary.get("average_days_on_market"),
                "absorption_rate_percentage": result_summary.get("absorption_rate_percentage"),
                "months_of_inventory": result_summary.get("months_of_inventory")
            }
            
        # Add to overview if we have metrics
        if metrics:
            overview["recent_analyses"].append({
                "job_id": job.job_id,
                "analysis_type": job.analysis_type,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "metrics": metrics
            })
    
    return overview