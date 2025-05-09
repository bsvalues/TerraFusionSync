"""
TerraFusion SyncService - Reporting Service

This module provides the core functionality for the reporting plugin,
including report job creation, tracking, and generation.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.core_models import ReportJob

# Configure logging
logger = logging.getLogger(__name__)


async def create_report_job(
    db: AsyncSession,
    report_type: str,
    county_id: str,
    parameters: Optional[Dict[str, Any]] = None
) -> ReportJob:
    """
    Create a new report job and save it to the database.
    
    Args:
        db: The database session
        report_type: Type of report to generate (e.g., 'sales_ratio_study', 'assessment_roll')
        county_id: County identifier
        parameters: Optional parameters for report generation
    
    Returns:
        ReportJob: The created job object
    """
    job = ReportJob(
        report_id=str(uuid.uuid4()),
        report_type=report_type,
        county_id=county_id,
        status="PENDING",
        parameters_json=parameters,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    try:
        db.add(job)
        await db.commit()
        await db.refresh(job)
        logger.info(f"Created report job {job.report_id} of type {report_type} for county {county_id}")
        return job
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating report job: {e}")
        raise


async def get_report_job(db: AsyncSession, report_id: str) -> Optional[ReportJob]:
    """
    Retrieve a report job by its ID.
    
    Args:
        db: The database session
        report_id: ID of the report job to retrieve
    
    Returns:
        Optional[ReportJob]: The report job if found, None otherwise
    """
    try:
        query = select(ReportJob).where(ReportJob.report_id == report_id)
        result = await db.execute(query)
        job = result.scalars().first()
        return job
    except Exception as e:
        logger.error(f"Error retrieving report job {report_id}: {e}")
        raise


async def list_report_jobs(
    db: AsyncSession,
    county_id: Optional[str] = None,
    report_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[ReportJob]:
    """
    List report jobs with optional filtering.
    
    Args:
        db: The database session
        county_id: Optional county ID to filter by
        report_type: Optional report type to filter by
        status: Optional status to filter by
        limit: Maximum number of results to return
        offset: Offset for pagination
    
    Returns:
        List[ReportJob]: List of matching report jobs
    """
    try:
        # Start with base query
        query = select(ReportJob)
        
        # Add filters if provided
        if county_id:
            query = query.where(ReportJob.county_id == county_id)
        if report_type:
            query = query.where(ReportJob.report_type == report_type)
        if status:
            query = query.where(ReportJob.status == status)
        
        # Add ordering and pagination
        query = query.order_by(ReportJob.created_at.desc()).limit(limit).offset(offset)
        
        # Execute query
        result = await db.execute(query)
        jobs = result.scalars().all()
        return jobs
    except Exception as e:
        logger.error(f"Error listing report jobs: {e}")
        raise


async def update_report_job_status(
    db: AsyncSession,
    report_id: str,
    status: str,
    message: Optional[str] = None,
    result_location: Optional[str] = None,
    result_metadata: Optional[Dict[str, Any]] = None
) -> Optional[ReportJob]:
    """
    Update the status of a report job.
    
    Args:
        db: The database session
        report_id: ID of the report job to update
        status: New status (PENDING, RUNNING, COMPLETED, FAILED)
        message: Optional status message or error details
        result_location: Optional location of the generated report
        result_metadata: Optional metadata about the report result
    
    Returns:
        Optional[ReportJob]: The updated job if found, None otherwise
    """
    try:
        # Prepare update values
        values = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        # Set optional fields if provided
        if message is not None:
            values["message"] = message
        
        if status == "RUNNING" and not await _is_job_already_running(db, report_id):
            values["started_at"] = datetime.utcnow()
        
        if status in ("COMPLETED", "FAILED"):
            values["completed_at"] = datetime.utcnow()
            
        if result_location:
            values["result_location"] = result_location
            
        if result_metadata:
            values["result_metadata_json"] = result_metadata
        
        # Execute update
        stmt = (
            update(ReportJob)
            .where(ReportJob.report_id == report_id)
            .values(**values)
            .returning(ReportJob)
        )
        
        result = await db.execute(stmt)
        await db.commit()
        
        # Get the updated job
        updated_job = result.scalar_one_or_none()
        
        if updated_job:
            logger.info(f"Updated report job {report_id} status to {status}")
        else:
            logger.warning(f"Report job {report_id} not found for status update")
            
        return updated_job
    except Exception as e:
        await db.rollback()
        logger.error(f"Error updating report job {report_id}: {e}")
        raise


async def _is_job_already_running(db: AsyncSession, report_id: str) -> bool:
    """
    Check if a job is already in RUNNING status.
    
    Args:
        db: The database session
        report_id: ID of the report job to check
    
    Returns:
        bool: True if the job is already running, False otherwise
    """
    job = await get_report_job(db, report_id)
    return job is not None and job.status == "RUNNING" and job.started_at is not None