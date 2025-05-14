"""
TerraFusion SyncService - GIS Export Plugin - Service Layer

This module provides service layer functionality for the GIS Export plugin,
handling business logic and database operations.
"""

import uuid
import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_

from terrafusion_sync.core_models import GisExportJob
from terrafusion_sync.plugins.gis_export.county_config import get_county_config

logger = logging.getLogger(__name__)

class GisExportService:
    """Service class for GIS Export operations."""

    @classmethod
    async def create_export_job(
        cls,
        export_format: str,
        county_id: str,
        area_of_interest: Dict[str, Any],
        layers: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        db: AsyncSession = None
    ) -> GisExportJob:
        """
        Create a new GIS export job.
        
        Args:
            export_format: Format of the export (e.g., GeoJSON, Shapefile, KML)
            county_id: ID of the county
            area_of_interest: GeoJSON object defining the area of interest
            layers: List of layers to export
            parameters: Additional parameters for the export
            db: Database session
            
        Returns:
            The created GisExportJob instance
            
        Raises:
            ValueError: If export format is not supported for the county or if db is None
        """
        if db is None:
            raise ValueError("Database session is required")
            
        # Validate export format against county configuration
        county_config = get_county_config()
        if not county_config.validate_export_format(county_id, export_format):
            valid_formats = county_config.get_available_formats(county_id)
            raise ValueError(
                f"Export format '{export_format}' is not supported for county '{county_id}'. "
                f"Supported formats are: {', '.join(valid_formats)}"
            )
        
        # Create the new job
        new_job = GisExportJob(
            job_id=str(uuid.uuid4()),
            export_format=export_format,
            county_id=county_id,
            area_of_interest_json=area_of_interest,
            layers_json=layers,
            parameters_json=parameters or {},
            status="PENDING",
            message="Job created and pending processing",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to database
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        logger.info(f"Created GIS export job {new_job.job_id} for county {county_id} in format {export_format}")
        
        return new_job
    
    @classmethod
    async def get_job_by_id(cls, job_id: str, db: AsyncSession) -> Optional[GisExportJob]:
        """
        Get a GIS export job by ID.
        
        Args:
            job_id: ID of the job to retrieve
            db: Database session
            
        Returns:
            The GisExportJob instance or None if not found
        """
        stmt = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(stmt)
        job = result.scalars().first()
        
        if not job:
            logger.warning(f"GIS export job {job_id} not found")
        
        return job
    
    @classmethod
    async def update_job_status(
        cls, 
        job_id: str, 
        status: str, 
        message: Optional[str] = None,
        result_file_location: Optional[str] = None,
        result_file_size_kb: Optional[int] = None,
        result_record_count: Optional[int] = None,
        db: AsyncSession = None
    ) -> Optional[GisExportJob]:
        """
        Update the status of a GIS export job.
        
        Args:
            job_id: ID of the job to update
            status: New status of the job
            message: Optional status message
            result_file_location: Optional location of the result file
            result_file_size_kb: Optional size of the result file in KB
            result_record_count: Optional count of records in the result
            db: Database session
            
        Returns:
            The updated GisExportJob instance or None if not found
            
        Raises:
            ValueError: If db is None
        """
        if db is None:
            raise ValueError("Database session is required")
            
        # Prepare update values
        values = {"status": status, "updated_at": datetime.utcnow()}
        
        # Add optional fields if provided
        if message is not None:
            values["message"] = message
        
        if result_file_location is not None:
            values["result_file_location"] = result_file_location
        
        if result_file_size_kb is not None:
            values["result_file_size_kb"] = result_file_size_kb
        
        if result_record_count is not None:
            values["result_record_count"] = result_record_count
        
        # Update timestamps based on status
        if status == "RUNNING":
            values["started_at"] = datetime.utcnow()
        
        if status in ["COMPLETED", "FAILED", "CANCELLED"]:
            values["completed_at"] = datetime.utcnow()
        
        # Update in database
        stmt = (
            update(GisExportJob)
            .where(GisExportJob.job_id == job_id)
            .values(**values)
            .returning(GisExportJob)
        )
        
        result = await db.execute(stmt)
        updated_job = result.scalars().first()
        
        if not updated_job:
            logger.warning(f"Failed to update GIS export job {job_id}: Job not found")
            return None
        
        await db.commit()
        
        logger.info(f"Updated GIS export job {job_id} status to {status}")
        
        return updated_job
    
    @classmethod
    async def list_jobs(
        cls,
        county_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        db: AsyncSession = None
    ) -> List[GisExportJob]:
        """
        List GIS export jobs with optional filtering.
        
        Args:
            county_id: Optional county ID to filter by
            status: Optional status to filter by
            limit: Maximum number of jobs to return
            offset: Offset for pagination
            db: Database session
            
        Returns:
            List of GisExportJob instances
            
        Raises:
            ValueError: If db is None
        """
        if db is None:
            raise ValueError("Database session is required")
            
        # Build query conditions
        conditions = []
        
        if county_id:
            conditions.append(GisExportJob.county_id == county_id)
        
        if status:
            conditions.append(GisExportJob.status == status)
        
        # Create base query
        if conditions:
            stmt = (
                select(GisExportJob)
                .where(and_(*conditions))
                .order_by(GisExportJob.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        else:
            stmt = (
                select(GisExportJob)
                .order_by(GisExportJob.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        
        # Execute query
        result = await db.execute(stmt)
        jobs = list(result.scalars().all())  # Convert to list explicitly
        
        logger.info(f"Retrieved {len(jobs)} GIS export jobs")
        
        return jobs
    
    @classmethod
    async def cancel_job(cls, job_id: str, db: AsyncSession) -> Optional[GisExportJob]:
        """
        Cancel a running or pending GIS export job.
        
        Args:
            job_id: ID of the job to cancel
            db: Database session
            
        Returns:
            The updated GisExportJob instance or None if not found or cannot be cancelled
            
        Raises:
            ValueError: If the job is already completed, failed, or cancelled
        """
        # Get the job first
        stmt = select(GisExportJob).where(GisExportJob.job_id == job_id)
        result = await db.execute(stmt)
        job = result.scalars().first()
        
        if not job:
            logger.warning(f"Cannot cancel GIS export job {job_id}: Job not found")
            return None
        
        # Check if job can be cancelled
        # String comparison for status to avoid ColumnElement.__bool__ issues
        if str(job.status) in ["COMPLETED", "FAILED", "CANCELLED"]:
            logger.warning(f"Cannot cancel GIS export job {job_id}: Job is already {job.status}")
            raise ValueError(f"Cannot cancel job that is already {job.status}")
        
        # Update job status to CANCELLING or CANCELLED
        # String comparison for status to avoid ColumnElement.__bool__ issues
        new_status = "CANCELLING" if str(job.status) == "RUNNING" else "CANCELLED"
        message = "Job cancellation requested" if str(job.status) == "RUNNING" else "Job cancelled before processing started"
        
        # Update the job
        return await cls.update_job_status(
            job_id=job_id,
            status=new_status,
            message=message,
            db=db
        )
    
    @classmethod
    def get_default_export_parameters(cls, county_id: str) -> Dict[str, Any]:
        """
        Get default export parameters for a county.
        
        Args:
            county_id: ID of the county
            
        Returns:
            Dictionary of default parameters
        """
        return get_county_config().get_default_parameters(county_id)