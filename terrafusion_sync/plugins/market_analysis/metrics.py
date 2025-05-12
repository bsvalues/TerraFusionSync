"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module provides Prometheus metrics for monitoring the Market Analysis plugin.
It tracks job counts, processing times, and success/failure rates.
"""

import logging
import time
from typing import Dict, Any, Optional

from prometheus_client import Counter, Histogram, Gauge

# Configure logger
logger = logging.getLogger(__name__)

# Define metrics
JOB_CREATED_COUNT = Counter(
    'market_analysis_job_created_total',
    'Total number of market analysis jobs created',
    ['county_id', 'analysis_type']
)

JOB_COMPLETED_COUNT = Counter(
    'market_analysis_job_completed_total',
    'Total number of market analysis jobs completed successfully',
    ['county_id', 'analysis_type']
)

JOB_FAILED_COUNT = Counter(
    'market_analysis_job_failed_total',
    'Total number of market analysis jobs that failed',
    ['county_id', 'analysis_type']
)

JOB_PROCESSING_TIME = Histogram(
    'market_analysis_job_processing_seconds',
    'Time taken to process market analysis jobs',
    ['county_id', 'analysis_type'],
    buckets=(1, 2, 5, 10, 30, 60, 120, 300, 600)
)

JOBS_RUNNING = Gauge(
    'market_analysis_jobs_running',
    'Number of market analysis jobs currently running',
    ['county_id', 'analysis_type']
)

# Timing decorator for function execution
def time_execution(county_id: str, analysis_type: str):
    """
    Decorator to measure and record execution time of analysis functions.
    
    Args:
        county_id: County ID for which the analysis was performed
        analysis_type: Type of analysis performed
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                end_time = time.time()
                JOB_PROCESSING_TIME.labels(county_id=county_id, analysis_type=analysis_type).observe(
                    end_time - start_time
                )
                return result
            except Exception as e:
                end_time = time.time()
                JOB_PROCESSING_TIME.labels(county_id=county_id, analysis_type=analysis_type).observe(
                    end_time - start_time
                )
                raise
        return wrapper
    return decorator


def record_job_creation(county_id: str, analysis_type: str) -> None:
    """
    Record the creation of a new job.
    
    Args:
        county_id: County ID for which the analysis was created
        analysis_type: Type of analysis created
    """
    JOB_CREATED_COUNT.labels(county_id=county_id, analysis_type=analysis_type).inc()
    logger.debug(f"Recorded job creation: {county_id}, {analysis_type}")


def update_running_jobs(county_id: str, analysis_type: str, increment: bool = True) -> None:
    """
    Update the count of running jobs.
    
    Args:
        county_id: County ID for which the analysis is running
        analysis_type: Type of analysis running
        increment: If True, increment the counter; if False, decrement it
    """
    if increment:
        JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).inc()
        logger.debug(f"Incremented running jobs: {county_id}, {analysis_type}")
    else:
        JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).dec()
        logger.debug(f"Decremented running jobs: {county_id}, {analysis_type}")


def record_job_completion(county_id: str, analysis_type: str) -> None:
    """
    Record the successful completion of a job.
    
    Args:
        county_id: County ID for which the analysis was completed
        analysis_type: Type of analysis completed
    """
    JOB_COMPLETED_COUNT.labels(county_id=county_id, analysis_type=analysis_type).inc()
    update_running_jobs(county_id, analysis_type, increment=False)
    logger.debug(f"Recorded job completion: {county_id}, {analysis_type}")


def record_job_failure(county_id: str, analysis_type: str) -> None:
    """
    Record the failure of a job.
    
    Args:
        county_id: County ID for which the analysis failed
        analysis_type: Type of analysis that failed
    """
    JOB_FAILED_COUNT.labels(county_id=county_id, analysis_type=analysis_type).inc()
    update_running_jobs(county_id, analysis_type, increment=False)
    logger.debug(f"Recorded job failure: {county_id}, {analysis_type}")


# Initialize metrics collection
def init_metrics() -> None:
    """Initialize metrics collection for the Market Analysis plugin."""
    logger.info("Initializing Market Analysis plugin metrics")
    # Initialization complete - metrics are defined at module level