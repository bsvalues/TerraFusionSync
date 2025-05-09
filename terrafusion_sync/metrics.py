"""
Prometheus metrics for TerraFusion SyncService.

This module defines Prometheus metrics for tracking the performance and health
of various components of the TerraFusion SyncService, particularly the
Valuation Plugin.
"""
import time
from typing import Callable, Dict, Any
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Summary

# === Global Metrics ===

# Counter for API requests
API_REQUESTS = Counter(
    'terrafusion_api_requests_total',
    'Total number of API requests',
    ['endpoint', 'method', 'status']
)

# Histogram for API request duration
API_REQUEST_DURATION = Histogram(
    'terrafusion_api_request_duration_seconds',
    'API request duration in seconds',
    ['endpoint', 'method'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60]
)

# Gauge for active database connections
DB_CONNECTIONS_ACTIVE = Gauge(
    'terrafusion_db_connections_active',
    'Number of active database connections'
)

# === Valuation Plugin Metrics ===

# Counter for valuation job submissions
VALUATION_JOBS_SUBMITTED = Counter(
    'terrafusion_valuation_jobs_submitted_total',
    'Total number of valuation jobs submitted',
    ['county_id', 'valuation_method']
)

# Counter for valuation job completions
VALUATION_JOBS_COMPLETED = Counter(
    'terrafusion_valuation_jobs_completed_total',
    'Total number of valuation jobs completed',
    ['county_id', 'valuation_method', 'status']
)

# Histogram for valuation job duration
VALUATION_JOB_DURATION = Histogram(
    'terrafusion_valuation_job_duration_seconds',
    'Valuation job processing duration in seconds',
    ['county_id', 'valuation_method'],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, 600]
)

# Gauge for pending valuation jobs
VALUATION_JOBS_PENDING = Gauge(
    'terrafusion_valuation_jobs_pending',
    'Number of valuation jobs in pending state'
)

# Gauge for valuation jobs in progress
VALUATION_JOBS_IN_PROGRESS = Gauge(
    'terrafusion_valuation_jobs_in_progress',
    'Number of valuation jobs currently being processed'
)

# Summary for valuation job result metrics
VALUATION_CONFIDENCE_SCORE = Summary(
    'terrafusion_valuation_confidence_score',
    'Confidence scores for valuations',
    ['county_id', 'valuation_method']
)


def track_api_request(endpoint: str):
    """
    Decorator to track API request metrics.
    
    Args:
        endpoint: API endpoint name for labeling metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            method = kwargs.get('method', 'UNKNOWN')
            start_time = time.time()
            
            status = 'unknown'
                try:
                    result = await func(*args, **kwargs)
                    status = result.status_code if hasattr(result, 'status_code') else 'success'
                    return result
                except Exception as e:
                    status = 'error'
                    raise e
                finally:
                    duration = time.time() - start_time
                    API_REQUESTS.labels(endpoint=endpoint, method=method, status=status).inc()
                    API_REQUEST_DURATION.labels(endpoint=endpoint, method=method).observe(duration)
        
        return wrapper
    return decorator


def track_valuation_job(func: Callable) -> Callable:
    """
    Decorator to track valuation job metrics.
    
    This will record job submission, completion, and duration metrics.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        county_id = kwargs.get('county_id', 'unknown')
        valuation_method = kwargs.get('valuation_method_hint', 'unknown')
        
        # Record job submission
        VALUATION_JOBS_SUBMITTED.labels(
            county_id=county_id,
            valuation_method=valuation_method
        ).inc()
        
        # Increment pending jobs
        VALUATION_JOBS_PENDING.inc()
        
        start_time = time.time()
        
        try:
            # Just before processing starts, update gauges
            VALUATION_JOBS_PENDING.dec()
            VALUATION_JOBS_IN_PROGRESS.inc()
            
            # Process the job
            result = await func(*args, **kwargs)
            
            # Record completion with success status
            VALUATION_JOBS_COMPLETED.labels(
                county_id=county_id,
                valuation_method=valuation_method,
                status='success'
            ).inc()
            
            # If result has a confidence score, record it
            if hasattr(result, 'confidence_score') and result.confidence_score is not None:
                VALUATION_CONFIDENCE_SCORE.labels(
                    county_id=county_id,
                    valuation_method=valuation_method
                ).observe(result.confidence_score)
            
            return result
            
        except Exception as e:
            # Record completion with error status
            VALUATION_JOBS_COMPLETED.labels(
                county_id=county_id,
                valuation_method=valuation_method,
                status='error'
            ).inc()
            raise e
            
        finally:
            # Always decrement in-progress counter and record duration
            VALUATION_JOBS_IN_PROGRESS.dec()
            duration = time.time() - start_time
            VALUATION_JOB_DURATION.labels(
                county_id=county_id,
                valuation_method=valuation_method
            ).observe(duration)
    
    return wrapper


def update_metrics_from_database(db_metrics: Dict[str, Any]):
    """
    Update metrics based on data from the database.
    
    Args:
        db_metrics: Dictionary containing current metrics from the database
    """
    # Update pending and in-progress job counts from DB
    if 'valuation_jobs_pending' in db_metrics:
        VALUATION_JOBS_PENDING.set(db_metrics['valuation_jobs_pending'])
    
    if 'valuation_jobs_in_progress' in db_metrics:
        VALUATION_JOBS_IN_PROGRESS.set(db_metrics['valuation_jobs_in_progress'])
    
    # Update active DB connections
    if 'db_connections_active' in db_metrics:
        DB_CONNECTIONS_ACTIVE.set(db_metrics['db_connections_active'])