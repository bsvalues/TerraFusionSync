"""
TerraFusion SyncService - GIS Analysis Plugin - Tasks

This module contains background tasks and job processing logic for GIS analysis.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from terrafusion_sync.plugins.gis_analysis.service import (
    get_analysis_job,
    update_job_status,
    process_analysis_job
)
from terrafusion_sync.plugins.gis_analysis.metrics import (
    record_job_completed,
    record_job_failed,
    record_job_cancelled
)

# Configure logging
logger = logging.getLogger(__name__)


async def process_pending_jobs(max_jobs: int = 5) -> int:
    """
    Process pending GIS analysis jobs.
    
    Args:
        max_jobs: Maximum number of jobs to process
        
    Returns:
        int: Number of jobs processed
    """
    # Import here to avoid circular imports
    from terrafusion_sync.database import async_session_maker
    from terrafusion_sync.plugins.gis_analysis.models import GISAnalysisJob
    import sqlalchemy as sa
    
    logger.info(f"Checking for pending GIS analysis jobs (max: {max_jobs})")
    processed_count = 0
    
    async with async_session_maker() as db:
        # Get pending jobs
        query = sa.select(GISAnalysisJob).where(
            GISAnalysisJob.status == "PENDING"
        ).order_by(
            GISAnalysisJob.created_at
        ).limit(max_jobs)
        
        result = await db.execute(query)
        pending_jobs = result.scalars().all()
        
        if not pending_jobs:
            logger.debug("No pending GIS analysis jobs found")
            return 0
        
        logger.info(f"Found {len(pending_jobs)} pending GIS analysis jobs")
        
        # Process each job
        for job in pending_jobs:
            logger.info(f"Processing GIS analysis job: {job.job_id}")
            
            # Start job processing in a separate task
            asyncio.create_task(process_analysis_job(job.job_id))
            processed_count += 1
    
    return processed_count


async def cleanup_stale_jobs(max_age_hours: int = 24) -> int:
    """
    Clean up stale jobs that are stuck in RUNNING status.
    
    Args:
        max_age_hours: Maximum age in hours for running jobs
        
    Returns:
        int: Number of jobs cleaned up
    """
    # Import here to avoid circular imports
    from terrafusion_sync.database import async_session_maker
    from terrafusion_sync.plugins.gis_analysis.models import GISAnalysisJob
    import sqlalchemy as sa
    from datetime import timedelta
    
    logger.info(f"Checking for stale GIS analysis jobs (max age: {max_age_hours} hours)")
    cleanup_count = 0
    
    async with async_session_maker() as db:
        # Get stale running jobs
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        query = sa.select(GISAnalysisJob).where(
            GISAnalysisJob.status == "RUNNING",
            GISAnalysisJob.updated_at < cutoff_time
        )
        
        result = await db.execute(query)
        stale_jobs = result.scalars().all()
        
        if not stale_jobs:
            logger.debug("No stale GIS analysis jobs found")
            return 0
        
        logger.info(f"Found {len(stale_jobs)} stale GIS analysis jobs")
        
        # Mark each job as failed
        for job in stale_jobs:
            logger.warning(f"Cleaning up stale job: {job.job_id} (last updated: {job.updated_at})")
            
            # Update job status
            await update_job_status(
                db=db,
                job_id=job.job_id,
                status="FAILED",
                message=f"Job timed out after {max_age_hours} hours",
            )
            
            # Record metric
            record_job_failed(job.county_id, job.analysis_type, "timeout")
            
            cleanup_count += 1
    
    return cleanup_count


async def update_layer_metrics() -> Dict[str, int]:
    """
    Update metrics for spatial layers.
    
    Returns:
        Dict[str, int]: Counts of layers by type
    """
    # Import here to avoid circular imports
    from terrafusion_sync.database import async_session_maker
    from terrafusion_sync.plugins.gis_analysis.models import SpatialLayerMetadata
    import sqlalchemy as sa
    from terrafusion_sync.plugins.gis_analysis.metrics import (
        update_spatial_layer_count,
        update_spatial_feature_count
    )
    
    logger.info("Updating spatial layer metrics")
    
    layer_counts = {}
    
    async with async_session_maker() as db:
        # Count layers by type and county
        query = sa.select(
            SpatialLayerMetadata.county_id,
            SpatialLayerMetadata.layer_type,
            sa.func.count().label('count')
        ).group_by(
            SpatialLayerMetadata.county_id,
            SpatialLayerMetadata.layer_type
        )
        
        result = await db.execute(query)
        layer_counts_by_type = result.all()
        
        # Update metrics
        for county_id, layer_type, count in layer_counts_by_type:
            update_spatial_layer_count(county_id, layer_type, count)
            
            if layer_type not in layer_counts:
                layer_counts[layer_type] = 0
            layer_counts[layer_type] += count
        
        # Update feature counts for each layer
        query = sa.select(SpatialLayerMetadata).where(
            SpatialLayerMetadata.feature_count.is_not(None)
        )
        
        result = await db.execute(query)
        layers = result.scalars().all()
        
        for layer in layers:
            update_spatial_feature_count(layer.county_id, layer.layer_id, layer.feature_count)
    
    return layer_counts