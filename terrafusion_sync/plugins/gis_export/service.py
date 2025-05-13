"""
TerraFusion SyncService - GIS Export Plugin - Service

This module contains the core business logic for GIS data export operations.
It is responsible for processing export requests, generating GIS data files,
and managing the export job lifecycle.
"""

import logging
import uuid
import json
import datetime
import time
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, and_

from terrafusion_sync.core_models import GisExportJob, PropertyOperational
from .metrics import (
    GIS_EXPORT_JOBS_COMPLETED_TOTAL,
    GIS_EXPORT_JOBS_FAILED_TOTAL,
    GIS_EXPORT_PROCESSING_DURATION_SECONDS,
    GIS_EXPORT_FILE_SIZE_KB,
    GIS_EXPORT_RECORD_COUNT
)

logger = logging.getLogger(__name__)

class GisExportService:
    """Service class for GIS export operations."""

    @staticmethod
    async def create_export_job(
        export_format: str,
        county_id: str,
        area_of_interest: Optional[Dict[str, Any]],
        layers: List[str],
        parameters: Optional[Dict[str, Any]],
        db: AsyncSession
    ) -> GisExportJob:
        """
        Create a new GIS export job and store it in the database.
        
        Args:
            export_format: The format to export (GeoJSON, Shapefile, KML, etc.)
            county_id: County identifier
            area_of_interest: Spatial area definition (e.g., bounding box, polygon)
            layers: List of data layers to include
            parameters: Additional export parameters
            db: Database session
            
        Returns:
            GisExportJob: The created job
        """
        job_id = str(uuid.uuid4())
        new_job = GisExportJob(
            job_id=job_id,
            export_format=export_format,
            county_id=county_id,
            area_of_interest_json=area_of_interest,
            layers_json=layers,
            parameters_json=parameters,
            status="PENDING",
            message="GIS export job accepted and queued for processing.",
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        
        db.add(new_job)
        await db.commit()
        await db.refresh(new_job)
        
        logger.info(f"Created GIS export job {job_id} for {county_id} in {export_format} format")
        return new_job

    @staticmethod
    async def get_job_by_id(job_id: str, db: AsyncSession) -> Optional[GisExportJob]:
        """
        Retrieve a GIS export job by its ID.
        
        Args:
            job_id: The job ID to find
            db: Database session
            
        Returns:
            Optional[GisExportJob]: The job if found, None otherwise
        """
        result = await db.execute(select(GisExportJob).where(GisExportJob.job_id == job_id))
        return result.scalars().first()

    @staticmethod
    async def list_jobs(
        county_id: Optional[str] = None,
        export_format: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
        db: AsyncSession
    ) -> List[GisExportJob]:
        """
        List GIS export jobs with optional filtering.
        
        Args:
            county_id: Filter by county ID
            export_format: Filter by export format
            status: Filter by status
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip
            db: Database session
            
        Returns:
            List[GisExportJob]: List of matching jobs
        """
        query = select(GisExportJob).order_by(GisExportJob.created_at.desc())
        
        if county_id:
            query = query.where(GisExportJob.county_id == county_id)
        
        if export_format:
            query = query.where(GisExportJob.export_format == export_format)
        
        if status:
            query = query.where(GisExportJob.status == status)
        
        query = query.limit(limit).offset(offset)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_job_status(
        job_id: str,
        status: str,
        message: str,
        db: AsyncSession
    ) -> Optional[GisExportJob]:
        """
        Update the status of a GIS export job.
        
        Args:
            job_id: The job ID to update
            status: New status value
            message: Status message
            db: Database session
            
        Returns:
            Optional[GisExportJob]: Updated job if found, None otherwise
        """
        result = await db.execute(
            update(GisExportJob)
            .where(GisExportJob.job_id == job_id)
            .values(
                status=status,
                message=message,
                updated_at=datetime.datetime.utcnow()
            )
            .returning(GisExportJob)
        )
        
        await db.commit()
        updated_job = result.scalars().first()
        
        if updated_job:
            logger.info(f"Updated job {job_id} status to {status}: {message}")
        else:
            logger.warning(f"Failed to update job {job_id} - not found")
            
        return updated_job

    @staticmethod
    async def mark_job_running(
        job_id: str,
        db: AsyncSession
    ) -> Optional[GisExportJob]:
        """
        Mark a job as running and record the start time.
        
        Args:
            job_id: The job ID to update
            db: Database session
            
        Returns:
            Optional[GisExportJob]: Updated job if found, None otherwise
        """
        now = datetime.datetime.utcnow()
        result = await db.execute(
            update(GisExportJob)
            .where(GisExportJob.job_id == job_id)
            .values(
                status="RUNNING",
                message="GIS export job is being processed.",
                started_at=now,
                updated_at=now
            )
            .returning(GisExportJob)
        )
        
        await db.commit()
        updated_job = result.scalars().first()
        
        if updated_job:
            logger.info(f"Marked job {job_id} as RUNNING")
        else:
            logger.warning(f"Failed to mark job {job_id} as RUNNING - not found")
            
        return updated_job

    @staticmethod
    async def mark_job_completed(
        job_id: str,
        result_file_location: str,
        result_file_size_kb: int,
        result_record_count: int,
        db: AsyncSession
    ) -> Optional[GisExportJob]:
        """
        Mark a job as completed and store result information.
        
        Args:
            job_id: The job ID to update
            result_file_location: Where the export file is stored
            result_file_size_kb: Size of the exported file in KB
            result_record_count: Number of records in the export
            db: Database session
            
        Returns:
            Optional[GisExportJob]: Updated job if found, None otherwise
        """
        now = datetime.datetime.utcnow()
        result = await db.execute(
            update(GisExportJob)
            .where(GisExportJob.job_id == job_id)
            .values(
                status="COMPLETED",
                message="GIS export completed successfully.",
                completed_at=now,
                updated_at=now,
                result_file_location=result_file_location,
                result_file_size_kb=result_file_size_kb,
                result_record_count=result_record_count
            )
            .returning(GisExportJob)
        )
        
        await db.commit()
        updated_job = result.scalars().first()
        
        if updated_job:
            logger.info(f"Marked job {job_id} as COMPLETED with file at {result_file_location}")
            
            # Update metrics
            GIS_EXPORT_JOBS_COMPLETED_TOTAL.labels(
                county_id=updated_job.county_id, 
                export_format=updated_job.export_format
            ).inc()
            
            GIS_EXPORT_FILE_SIZE_KB.labels(
                county_id=updated_job.county_id, 
                export_format=updated_job.export_format
            ).observe(result_file_size_kb)
            
            GIS_EXPORT_RECORD_COUNT.labels(
                county_id=updated_job.county_id, 
                export_format=updated_job.export_format
            ).observe(result_record_count)
            
        else:
            logger.warning(f"Failed to mark job {job_id} as COMPLETED - not found")
            
        return updated_job

    @staticmethod
    async def mark_job_failed(
        job_id: str,
        error_message: str,
        db: AsyncSession,
        failure_reason: str = "processing_error"
    ) -> Optional[GisExportJob]:
        """
        Mark a job as failed with an error message.
        
        Args:
            job_id: The job ID to update
            error_message: Descriptive error message
            db: Database session
            failure_reason: Category of failure for metrics
            
        Returns:
            Optional[GisExportJob]: Updated job if found, None otherwise
        """
        now = datetime.datetime.utcnow()
        result = await db.execute(
            update(GisExportJob)
            .where(GisExportJob.job_id == job_id)
            .values(
                status="FAILED",
                message=f"GIS export failed: {error_message}",
                completed_at=now,
                updated_at=now
            )
            .returning(GisExportJob)
        )
        
        await db.commit()
        updated_job = result.scalars().first()
        
        if updated_job:
            logger.error(f"Marked job {job_id} as FAILED: {error_message}")
            
            # Update metrics
            GIS_EXPORT_JOBS_FAILED_TOTAL.labels(
                county_id=updated_job.county_id, 
                export_format=updated_job.export_format, 
                failure_reason=failure_reason
            ).inc()
            
        else:
            logger.warning(f"Failed to mark job {job_id} as FAILED - not found")
            
        return updated_job

    @staticmethod
    async def process_gis_export(
        job: GisExportJob,
        db: AsyncSession
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process a GIS export job to generate data files.
        
        This is the core function that performs the actual GIS data export.
        It would typically:
        1. Retrieve property data based on the area of interest
        2. Filter for the requested layers
        3. Transform the data to the requested format
        4. Write the file and return metadata
        
        Args:
            job: The job to process
            db: Database session
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: Success flag, message, and result data
        """
        logger.info(f"Processing GIS export job {job.job_id} [{job.export_format}]")
        
        # Record start time for metrics
        start_time = time.monotonic()
        
        try:
            # Extract job parameters
            export_format = job.export_format
            county_id = job.county_id
            area_of_interest = job.area_of_interest_json
            layers = job.layers_json if job.layers_json else []
            parameters = job.parameters_json if job.parameters_json else {}
            
            # Mark job as running
            await GisExportService.mark_job_running(job.job_id, db)
            
            # In a real implementation, this would:
            # 1. Execute spatial queries based on area_of_interest
            # 2. Apply layer filtering
            # 3. Format data according to export_format
            # 4. Generate/store the output file(s)
            
            # The demo implementation simply waits and returns simulated data
            await asyncio.sleep(5)  # Simulate processing time
            
            # Simulated failure scenario for testing
            if export_format == "FAIL_FORMAT_SIM":
                raise ValueError("Simulated failure for testing purposes")
            
            # Calculate simulated file path and metadata
            file_path = f"/gis_exports/{county_id}/{job.job_id}_{'_'.join(layers)}.{export_format.lower().replace('shapefile','zip')}"
            file_size_kb = 5120  # Simulated
            record_count = 2500  # Simulated
            
            # Mark job as completed
            await GisExportService.mark_job_completed(
                job.job_id,
                file_path,
                file_size_kb,
                record_count,
                db
            )
            
            # Record processing time
            processing_time = time.monotonic() - start_time
            GIS_EXPORT_PROCESSING_DURATION_SECONDS.labels(
                county_id=county_id,
                export_format=export_format
            ).observe(processing_time)
            
            logger.info(f"GIS export job {job.job_id} completed in {processing_time:.2f}s")
            
            # Return success result
            return (True, "Export completed successfully", {
                "file_path": file_path,
                "file_size_kb": file_size_kb,
                "record_count": record_count
            })
            
        except Exception as e:
            error_msg = f"Error processing GIS export: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # Mark job as failed
            await GisExportService.mark_job_failed(job.job_id, str(e), db)
            
            # Record processing time for failed job too
            processing_time = time.monotonic() - start_time
            GIS_EXPORT_PROCESSING_DURATION_SECONDS.labels(
                county_id=job.county_id,
                export_format=job.export_format
            ).observe(processing_time)
            
            # Return failure result
            return (False, error_msg, None)