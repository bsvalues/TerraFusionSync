"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module provides Prometheus metrics for monitoring the Market Analysis plugin.
It tracks job counts, processing times, and success/failure rates.
"""

import logging
import time
import functools
from typing import Dict, Any, Callable, Awaitable

from prometheus_client import Counter, Gauge, Histogram

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Prometheus metrics
MARKET_ANALYSIS_JOBS_CREATED = Counter(
    'market_analysis_jobs_created_total',
    'Total number of market analysis jobs created',
    ['county_id', 'analysis_type']
)

MARKET_ANALYSIS_JOBS_RUNNING = Gauge(
    'market_analysis_jobs_running',
    'Number of market analysis jobs currently running',
    ['county_id', 'analysis_type']
)

MARKET_ANALYSIS_JOBS_COMPLETED = Counter(
    'market_analysis_jobs_completed_total',
    'Total number of market analysis jobs completed successfully',
    ['county_id', 'analysis_type']
)

MARKET_ANALYSIS_JOBS_FAILED = Counter(
    'market_analysis_jobs_failed_total',
    'Total number of market analysis jobs that failed',
    ['county_id', 'analysis_type']
)

MARKET_ANALYSIS_JOB_DURATION = Histogram(
    'market_analysis_job_duration_seconds',
    'Duration of market analysis job processing in seconds',
    ['county_id', 'analysis_type'],
    buckets=(1, 2, 5, 10, 30, 60, 120, 300, 600)
)

def time_execution(county_id: str, analysis_type: str):
    """
    Decorator to measure and record execution time of analysis functions.
    
    Args:
        county_id: County ID for which the analysis was performed
        analysis_type: Type of analysis performed
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                # Record execution time
                duration = time.time() - start_time
                MARKET_ANALYSIS_JOB_DURATION.labels(
                    county_id=county_id,
                    analysis_type=analysis_type
                ).observe(duration)
                logger.info(f"Analysis {analysis_type} for county {county_id} took {duration:.2f}s")
                return result
            except Exception as e:
                # Still record execution time even if function fails
                duration = time.time() - start_time
                MARKET_ANALYSIS_JOB_DURATION.labels(
                    county_id=county_id,
                    analysis_type=analysis_type
                ).observe(duration)
                logger.error(f"Analysis {analysis_type} for county {county_id} failed after {duration:.2f}s: {e}")
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
    MARKET_ANALYSIS_JOBS_CREATED.labels(
        county_id=county_id,
        analysis_type=analysis_type
    ).inc()
    logger.debug(f"Recorded creation of {analysis_type} job for county {county_id}")

def update_running_jobs(county_id: str, analysis_type: str, increment: bool = True) -> None:
    """
    Update the count of running jobs.
    
    Args:
        county_id: County ID for which the analysis is running
        analysis_type: Type of analysis running
        increment: If True, increment the counter; if False, decrement it
    """
    if increment:
        MARKET_ANALYSIS_JOBS_RUNNING.labels(
            county_id=county_id,
            analysis_type=analysis_type
        ).inc()
        logger.debug(f"Incremented running count for {analysis_type} job for county {county_id}")
    else:
        MARKET_ANALYSIS_JOBS_RUNNING.labels(
            county_id=county_id,
            analysis_type=analysis_type
        ).dec()
        logger.debug(f"Decremented running count for {analysis_type} job for county {county_id}")

def record_job_completion(county_id: str, analysis_type: str) -> None:
    """
    Record the successful completion of a job.
    
    Args:
        county_id: County ID for which the analysis was completed
        analysis_type: Type of analysis completed
    """
    MARKET_ANALYSIS_JOBS_COMPLETED.labels(
        county_id=county_id,
        analysis_type=analysis_type
    ).inc()
    # Ensure running jobs count is decremented
    update_running_jobs(county_id, analysis_type, increment=False)
    logger.debug(f"Recorded completion of {analysis_type} job for county {county_id}")

def record_job_failure(county_id: str, analysis_type: str) -> None:
    """
    Record the failure of a job.
    
    Args:
        county_id: County ID for which the analysis failed
        analysis_type: Type of analysis that failed
    """
    MARKET_ANALYSIS_JOBS_FAILED.labels(
        county_id=county_id,
        analysis_type=analysis_type
    ).inc()
    # Ensure running jobs count is decremented
    update_running_jobs(county_id, analysis_type, increment=False)
    logger.debug(f"Recorded failure of {analysis_type} job for county {county_id}")

def init_metrics() -> None:
    """Initialize metrics collection for the Market Analysis plugin."""
    logger.info("Initialized metrics for Market Analysis plugin")