"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module defines Prometheus metrics specific to the Market Analysis plugin
and functions to interact with these metrics.
"""

import time
import functools
from typing import Dict, Any, Callable, Optional

from prometheus_client import Counter, Gauge, Histogram

# Import metrics from core module
from terrafusion_sync.metrics import (
    MARKET_ANALYSIS_JOBS_SUBMITTED,
    MARKET_ANALYSIS_JOBS_COMPLETED,
    MARKET_ANALYSIS_JOBS_FAILED,
    MARKET_ANALYSIS_PROCESSING_DURATION as MARKET_ANALYSIS_JOB_DURATION,
    MARKET_ANALYSIS_JOBS_PENDING,
    MARKET_ANALYSIS_JOBS_IN_PROGRESS
)

# Property price metrics
PROPERTY_AVERAGE_PRICE = Gauge(
    'property_average_price_dollars',
    'Average property price in dollars',
    ['county_id', 'zip_code', 'property_type']
)

PROPERTY_MEDIAN_PRICE = Gauge(
    'property_median_price_dollars',
    'Median property price in dollars',
    ['county_id', 'zip_code', 'property_type']
)

# Market score (0-100)
MARKET_SCORE = Gauge(
    'market_score',
    'Market score from 0-100',
    ['county_id', 'zip_code']
)

# Queue metrics
MARKET_ANALYSIS_QUEUE_SIZE = Gauge(
    'market_analysis_queue_size',
    'Number of market analysis jobs in queue',
    ['status']
)

def track_market_analysis_job(analysis_type: str, county_id: str) -> Callable:
    """
    Decorator to track market analysis job execution time.
    
    Args:
        analysis_type: Type of market analysis
        county_id: County identifier
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Record job start
            start_time = time.time()
            
            try:
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Record successful completion
                MARKET_ANALYSIS_JOBS_COMPLETED.labels(
                    county_id=county_id,
                    analysis_type=analysis_type
                ).inc()
                
                return result
                
            except Exception as e:
                # Record failure
                MARKET_ANALYSIS_JOBS_FAILED.labels(
                    county_id=county_id,
                    analysis_type=analysis_type
                ).inc()
                
                # Re-raise the exception
                raise e
                
            finally:
                # Record duration
                execution_time = time.time() - start_time
                MARKET_ANALYSIS_JOB_DURATION.labels(
                    county_id=county_id,
                    analysis_type=analysis_type
                ).observe(execution_time)
                
        return wrapper
    return decorator

def update_property_price_metrics(
    county_id: str,
    zip_code: str,
    property_type: str,
    average_price: float,
    median_price: float
):
    """
    Update property price metrics.
    
    Args:
        county_id: County identifier
        zip_code: ZIP code
        property_type: Property type (e.g., residential, commercial)
        average_price: Average property price
        median_price: Median property price
    """
    PROPERTY_AVERAGE_PRICE.labels(
        county_id=county_id,
        zip_code=zip_code,
        property_type=property_type
    ).set(average_price)
    
    PROPERTY_MEDIAN_PRICE.labels(
        county_id=county_id,
        zip_code=zip_code,
        property_type=property_type
    ).set(median_price)

def update_market_score(county_id: str, zip_code: str, score: float):
    """
    Update market score metric.
    
    Args:
        county_id: County identifier
        zip_code: ZIP code
        score: Market score (0-100)
    """
    MARKET_SCORE.labels(
        county_id=county_id,
        zip_code=zip_code
    ).set(score)

def update_queue_metrics(queue_status: Dict[str, int]):
    """
    Update queue metrics.
    
    Args:
        queue_status: Dictionary mapping status to count
    """
    for status, count in queue_status.items():
        MARKET_ANALYSIS_QUEUE_SIZE.labels(status=status).set(count)