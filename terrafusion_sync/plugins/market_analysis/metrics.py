"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module defines Prometheus metrics specific to the Market Analysis plugin.
The metrics are registered with the global Prometheus registry for collection
via the /metrics endpoint.
"""

import logging
from functools import wraps
import time
from typing import Callable, Dict, Any

from prometheus_client import Counter, Histogram, Gauge

logger = logging.getLogger(__name__)

# Define plugin-specific metrics

# Counter for market analysis jobs
MARKET_ANALYSIS_JOBS_TOTAL = Counter(
    'market_analysis_jobs_total',
    'Total number of market analysis jobs by type and status',
    ['county_id', 'analysis_type', 'status']
)

# Counter for data points analyzed
MARKET_ANALYSIS_DATA_POINTS_TOTAL = Counter(
    'market_analysis_data_points_total',
    'Total number of data points analyzed by the market analysis plugin',
    ['county_id', 'analysis_type']
)

# Histogram for analysis processing time
MARKET_ANALYSIS_PROCESSING_SECONDS = Histogram(
    'market_analysis_processing_seconds',
    'Time taken to process market analysis jobs',
    ['county_id', 'analysis_type'],
    buckets=[0.1, 0.5, 1, 2.5, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]
)

# Gauge for current property prices by area
MARKET_ANALYSIS_PROPERTY_PRICES = Gauge(
    'market_analysis_property_prices',
    'Current property prices from analysis results',
    ['county_id', 'zip_code', 'property_type', 'metric']
)

# Gauge for market score
MARKET_ANALYSIS_MARKET_SCORE = Gauge(
    'market_analysis_market_score',
    'Market health score from 0-100',
    ['county_id', 'zip_code']
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
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            start_time = time.monotonic()
            
            try:
                # Execute the original function
                result = await func(*args, **kwargs)
                
                # Record success
                MARKET_ANALYSIS_JOBS_TOTAL.labels(
                    county_id=county_id,
                    analysis_type=analysis_type,
                    status="success"
                ).inc()
                
                return result
                
            except Exception as e:
                # Record failure
                MARKET_ANALYSIS_JOBS_TOTAL.labels(
                    county_id=county_id,
                    analysis_type=analysis_type,
                    status="failure"
                ).inc()
                
                # Re-raise the exception
                raise
                
            finally:
                # Record execution time
                execution_time = time.monotonic() - start_time
                MARKET_ANALYSIS_PROCESSING_SECONDS.labels(
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
    MARKET_ANALYSIS_PROPERTY_PRICES.labels(
        county_id=county_id,
        zip_code=zip_code,
        property_type=property_type,
        metric="average"
    ).set(average_price)
    
    MARKET_ANALYSIS_PROPERTY_PRICES.labels(
        county_id=county_id,
        zip_code=zip_code,
        property_type=property_type,
        metric="median"
    ).set(median_price)

def update_market_score(county_id: str, zip_code: str, score: float):
    """
    Update market score metric.
    
    Args:
        county_id: County identifier
        zip_code: ZIP code
        score: Market score (0-100)
    """
    MARKET_ANALYSIS_MARKET_SCORE.labels(
        county_id=county_id,
        zip_code=zip_code
    ).set(score)