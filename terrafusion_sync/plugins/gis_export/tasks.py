"""
TerraFusion SyncService - GIS Export Plugin - Tasks

This module contains background tasks for processing GIS export jobs asynchronously.
These tasks are designed to be run in the background using FastAPI's BackgroundTasks.
"""

import logging
import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.database import async_session_maker
from terrafusion_sync.core_models import GisExportJob
from .service import GisExportService

logger = logging.getLogger(__name__)

async def process_gis_export_job(
    job_id: str,
    export_format: str,
    county_id: str,
    area_of_interest: Optional[Dict[str, Any]],
    layers: List[str],
    parameters: Optional[Dict[str, Any]],
    db_session_factory: Callable = async_session_maker
):
    """
    Background task to process a GIS export job.
    
    This function is designed to be run as a background task with FastAPI.
    It processes a GIS export job asynchronously, updating the job status
    and generating the requested export file.
    
    Args:
        job_id: ID of the job to process
        export_format: Format for the export (GeoJSON, Shapefile, KML, etc.)
        county_id: County ID for the export
        area_of_interest: Spatial area definition (bounding box, polygon, etc.)
        layers: List of data layers to include
        parameters: Additional export parameters
        db_session_factory: Factory function to create database sessions
    """
    logger.info(f"Starting background task for GIS export job {job_id}")
    
    # Create new database session for this background task
    async with db_session_factory() as db:
        try:
            # Get the job from the database
            job = await GisExportService.get_job_by_id(job_id, db)
            
            if not job:
                logger.error(f"Job {job_id} not found when starting background task")
                return
                
            # Process the export through the service layer
            success, message, result = await GisExportService.process_gis_export(job, db)
            
            if not success:
                logger.error(f"GIS export job {job_id} failed: {message}")
                
        except Exception as e:
            logger.error(f"Unhandled exception in GIS export background task for job {job_id}: {e}", exc_info=True)
            
            # Try to update job status to failed if possible
            try:
                await GisExportService.mark_job_failed(
                    job_id,
                    f"Unhandled error in background task: {str(e)}",
                    db,
                    failure_reason="background_task_exception"
                )
            except Exception as mark_ex:
                logger.error(f"Failed to mark job {job_id} as failed: {mark_ex}")

async def cancel_gis_export_job(job_id: str, db_session_factory: Callable = async_session_maker):
    """
    Cancel a running or pending GIS export job.
    
    Args:
        job_id: ID of the job to cancel
        db_session_factory: Factory function to create database sessions
    
    Returns:
        bool: True if cancellation was successful, False otherwise
    """
    logger.info(f"Attempting to cancel GIS export job {job_id}")
    
    async with db_session_factory() as db:
        try:
            # Get the job
            job = await GisExportService.get_job_by_id(job_id, db)
            
            if not job:
                logger.warning(f"Job {job_id} not found when trying to cancel")
                return False
                
            # Can only cancel jobs that aren't completed or failed
            if job.status in ["COMPLETED", "FAILED"]:
                logger.warning(f"Cannot cancel job {job_id} with status {job.status}")
                return False
                
            # Update job status to cancelled
            updated_job = await GisExportService.mark_job_failed(
                job_id,
                "Job cancelled by user request",
                db,
                failure_reason="user_cancelled"
            )
            
            return updated_job is not None
            
        except Exception as e:
            logger.error(f"Error cancelling GIS export job {job_id}: {e}", exc_info=True)
            return False