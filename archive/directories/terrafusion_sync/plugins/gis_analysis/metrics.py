"""
TerraFusion SyncService - GIS Analysis Plugin - Metrics

This module defines Prometheus metrics for the GIS Analysis plugin.
"""

import logging
from typing import Dict, Any, Optional

from prometheus_client import Counter, Gauge, Histogram

# Configure logging
logger = logging.getLogger(__name__)

# Define metrics
GIS_ANALYSIS_JOBS_CREATED = Counter(
    'gis_analysis_jobs_created',
    'Total number of GIS analysis jobs created',
    ['county_id', 'analysis_type']
)

GIS_ANALYSIS_JOBS_COMPLETED = Counter(
    'gis_analysis_jobs_completed',
    'Total number of GIS analysis jobs completed successfully',
    ['county_id', 'analysis_type']
)

GIS_ANALYSIS_JOBS_FAILED = Counter(
    'gis_analysis_jobs_failed',
    'Total number of GIS analysis jobs failed',
    ['county_id', 'analysis_type', 'error_type']
)

GIS_ANALYSIS_JOBS_CANCELLED = Counter(
    'gis_analysis_jobs_cancelled',
    'Total number of GIS analysis jobs cancelled by user',
    ['county_id', 'analysis_type']
)

GIS_ANALYSIS_JOBS_RUNNING = Gauge(
    'gis_analysis_jobs_running',
    'Number of GIS analysis jobs currently running',
    ['county_id', 'analysis_type']
)

GIS_ANALYSIS_JOB_PROCESSING_TIME = Histogram(
    'gis_analysis_job_processing_time_seconds',
    'Time taken to process GIS analysis jobs',
    ['county_id', 'analysis_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

GIS_SPATIAL_LAYER_COUNT = Gauge(
    'gis_spatial_layer_count',
    'Number of spatial layers available for GIS analysis',
    ['county_id', 'layer_type']
)

GIS_SPATIAL_FEATURE_COUNT = Gauge(
    'gis_spatial_feature_count',
    'Number of features in spatial layers',
    ['county_id', 'layer_id']
)

# Module initialization flag
_metrics_initialized = False


def init_metrics() -> None:
    """Initialize plugin metrics."""
    global _metrics_initialized
    
    if _metrics_initialized:
        logger.debug("GIS Analysis metrics already initialized")
        return
    
    logger.info("Initializing GIS Analysis plugin metrics")
    _metrics_initialized = True


def record_job_created(county_id: str, analysis_type: str) -> None:
    """
    Record a new GIS analysis job creation.
    
    Args:
        county_id: The county ID
        analysis_type: The type of analysis
    """
    try:
        GIS_ANALYSIS_JOBS_CREATED.labels(county_id=county_id, analysis_type=analysis_type).inc()
        GIS_ANALYSIS_JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).inc()
    except Exception as e:
        logger.error(f"Failed to record job creation metrics: {e}")


def record_job_completed(county_id: str, analysis_type: str, processing_time_seconds: float) -> None:
    """
    Record a GIS analysis job completion.
    
    Args:
        county_id: The county ID
        analysis_type: The type of analysis
        processing_time_seconds: Time taken to process the job in seconds
    """
    try:
        GIS_ANALYSIS_JOBS_COMPLETED.labels(county_id=county_id, analysis_type=analysis_type).inc()
        GIS_ANALYSIS_JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).dec()
        GIS_ANALYSIS_JOB_PROCESSING_TIME.labels(county_id=county_id, analysis_type=analysis_type).observe(processing_time_seconds)
    except Exception as e:
        logger.error(f"Failed to record job completion metrics: {e}")


def record_job_failed(county_id: str, analysis_type: str, error_type: str) -> None:
    """
    Record a GIS analysis job failure.
    
    Args:
        county_id: The county ID
        analysis_type: The type of analysis
        error_type: Type of error that caused the failure
    """
    try:
        GIS_ANALYSIS_JOBS_FAILED.labels(county_id=county_id, analysis_type=analysis_type, error_type=error_type).inc()
        GIS_ANALYSIS_JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).dec()
    except Exception as e:
        logger.error(f"Failed to record job failure metrics: {e}")


def record_job_cancelled(county_id: str, analysis_type: str) -> None:
    """
    Record a GIS analysis job cancellation.
    
    Args:
        county_id: The county ID
        analysis_type: The type of analysis
    """
    try:
        GIS_ANALYSIS_JOBS_CANCELLED.labels(county_id=county_id, analysis_type=analysis_type).inc()
        GIS_ANALYSIS_JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).dec()
    except Exception as e:
        logger.error(f"Failed to record job cancellation metrics: {e}")


def update_spatial_layer_count(county_id: str, layer_type: str, count: int) -> None:
    """
    Update the count of spatial layers for a county.
    
    Args:
        county_id: The county ID
        layer_type: Type of spatial layer (polygon, point, line, etc.)
        count: Number of layers
    """
    try:
        GIS_SPATIAL_LAYER_COUNT.labels(county_id=county_id, layer_type=layer_type).set(count)
    except Exception as e:
        logger.error(f"Failed to update spatial layer count metrics: {e}")


def update_spatial_feature_count(county_id: str, layer_id: str, count: int) -> None:
    """
    Update the count of features in a spatial layer.
    
    Args:
        county_id: The county ID
        layer_id: The layer ID
        count: Number of features
    """
    try:
        GIS_SPATIAL_FEATURE_COUNT.labels(county_id=county_id, layer_id=layer_id).set(count)
    except Exception as e:
        logger.error(f"Failed to update spatial feature count metrics: {e}")