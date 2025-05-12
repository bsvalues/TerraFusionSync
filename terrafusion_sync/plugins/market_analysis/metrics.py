"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module sets up Prometheus metrics for the Market Analysis plugin,
helping track performance, errors, and usage statistics.
"""

import logging
from prometheus_client import Counter, Gauge, Histogram
from typing import Dict, Any

# Configure logger
logger = logging.getLogger(__name__)

# Metrics for job tracking
JOB_SUBMISSIONS = Counter(
    'market_analysis_job_submissions_total',
    'Number of market analysis jobs submitted',
    ['county_id', 'analysis_type']
)

JOB_COMPLETIONS = Counter(
    'market_analysis_job_completions_total',
    'Number of market analysis jobs completed successfully',
    ['county_id', 'analysis_type']
)

JOB_FAILURES = Counter(
    'market_analysis_job_failures_total',
    'Number of market analysis jobs that failed',
    ['county_id', 'analysis_type', 'reason']
)

RUNNING_JOBS = Gauge(
    'market_analysis_jobs_running',
    'Number of market analysis jobs currently running',
    ['county_id', 'analysis_type']
)

JOB_PROCESSING_TIME = Histogram(
    'market_analysis_job_processing_seconds',
    'Time taken to process market analysis jobs',
    ['county_id', 'analysis_type'],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0)
)

# Metrics for property valuation
PROPERTY_VALUATION = Histogram(
    'market_analysis_property_valuation_dollars',
    'Property valuation in dollars',
    ['county_id', 'property_type'],
    buckets=(
        100000, 200000, 300000, 400000, 500000,
        750000, 1000000, 1500000, 2000000, 3000000,
        5000000, 10000000
    )
)

PRICE_PER_SQFT = Histogram(
    'market_analysis_price_per_sqft_dollars',
    'Price per square foot in dollars',
    ['county_id', 'property_type'],
    buckets=(100, 200, 300, 400, 500, 750, 1000, 1500, 2000, 3000, 5000)
)

MARKET_AREA_COUNT = Gauge(
    'market_analysis_comparable_areas_count', 
    'Number of comparable market areas identified',
    ['county_id', 'zip_code']
)

SALES_VELOCITY = Gauge(
    'market_analysis_sales_velocity_per_month',
    'Number of properties sold per month',
    ['county_id', 'zip_code']
)

DAYS_ON_MARKET = Gauge(
    'market_analysis_avg_days_on_market',
    'Average number of days properties stay on market',
    ['county_id', 'zip_code']
)

# Function-based metrics API for easy consumption

def record_job_submission(county_id: str, analysis_type: str):
    """Record a job submission metric."""
    JOB_SUBMISSIONS.labels(county_id=county_id, analysis_type=analysis_type).inc()
    logger.debug(f"Recorded job submission for {county_id}, type: {analysis_type}")


def record_job_completion(county_id: str, analysis_type: str):
    """Record a job completion metric."""
    JOB_COMPLETIONS.labels(county_id=county_id, analysis_type=analysis_type).inc()
    logger.debug(f"Recorded job completion for {county_id}, type: {analysis_type}")


def record_job_failure(county_id: str, analysis_type: str, reason: str):
    """Record a job failure metric."""
    JOB_FAILURES.labels(county_id=county_id, analysis_type=analysis_type, reason=reason).inc()
    logger.debug(f"Recorded job failure for {county_id}, type: {analysis_type}, reason: {reason}")


def update_running_jobs(county_id: str, analysis_type: str, count: int):
    """Update the number of running jobs."""
    RUNNING_JOBS.labels(county_id=county_id, analysis_type=analysis_type).set(count)
    logger.debug(f"Updated running jobs count for {county_id}, type: {analysis_type}: {count}")


def record_job_processing_time(county_id: str, analysis_type: str, seconds: float):
    """Record job processing time in seconds."""
    JOB_PROCESSING_TIME.labels(county_id=county_id, analysis_type=analysis_type).observe(seconds)
    logger.debug(f"Recorded processing time for {county_id}, type: {analysis_type}: {seconds}s")


def record_property_valuation(county_id: str, property_type: str, value: float):
    """Record a property valuation in dollars."""
    PROPERTY_VALUATION.labels(county_id=county_id, property_type=property_type).observe(value)
    logger.debug(f"Recorded property valuation for {county_id}, type: {property_type}: ${value}")


def record_price_per_sqft(county_id: str, property_type: str, value: float):
    """Record a price per square foot in dollars."""
    PRICE_PER_SQFT.labels(county_id=county_id, property_type=property_type).observe(value)
    logger.debug(f"Recorded price per sqft for {county_id}, type: {property_type}: ${value}/sqft")


def record_comparable_areas_count(county_id: str, zip_code: str, count: int):
    """Record the number of comparable market areas identified."""
    MARKET_AREA_COUNT.labels(county_id=county_id, zip_code=zip_code).set(count)
    logger.debug(f"Recorded comparable areas count for {county_id}, zip: {zip_code}: {count}")


def record_sales_velocity(county_id: str, zip_code: str, sales_per_month: float):
    """Record the sales velocity (sales per month) for a zip code."""
    SALES_VELOCITY.labels(county_id=county_id, zip_code=zip_code).set(sales_per_month)
    logger.debug(f"Recorded sales velocity for {county_id}, zip: {zip_code}: {sales_per_month}/month")


def record_days_on_market(county_id: str, zip_code: str, avg_days: float):
    """Record the average days on market for a zip code."""
    DAYS_ON_MARKET.labels(county_id=county_id, zip_code=zip_code).set(avg_days)
    logger.debug(f"Recorded avg days on market for {county_id}, zip: {zip_code}: {avg_days} days")


def get_metrics_data(county_id: str = None) -> Dict[str, Any]:
    """
    Get a summary of metrics for a county or all counties.
    
    Returns dictionary with metrics summaries.
    """
    # In a production environment, we would query the Prometheus API
    # or use direct access to metric values. For this implementation,
    # we'll return a simple structure with the current values.
    
    data = {
        "job_metrics": {
            "submissions": {
                "total": sum(JOB_SUBMISSIONS._metrics.values()) if hasattr(JOB_SUBMISSIONS, '_metrics') else 0
            },
            "completions": {
                "total": sum(JOB_COMPLETIONS._metrics.values()) if hasattr(JOB_COMPLETIONS, '_metrics') else 0
            },
            "failures": {
                "total": sum(JOB_FAILURES._metrics.values()) if hasattr(JOB_FAILURES, '_metrics') else 0
            },
            "running": {
                "total": sum(RUNNING_JOBS._metrics.values()) if hasattr(RUNNING_JOBS, '_metrics') else 0
            }
        },
        "property_metrics": {
            "avg_valuation": {},
            "avg_price_per_sqft": {}
        },
        "market_metrics": {
            "avg_days_on_market": {},
            "avg_sales_velocity": {}
        }
    }
    
    # We would normally compute these values from the actual metrics data
    # For now, we'll just return the structure
    
    return data


# Utility functions for updating metrics in batch
def update_property_price_metrics(county_id: str, property_type: str, avg_value: float, avg_ppsf: float):
    """Update both property value and price per sqft metrics in one call."""
    record_property_valuation(county_id, property_type, avg_value)
    record_price_per_sqft(county_id, property_type, avg_ppsf)


def update_market_score(county_id: str, zip_code: str, sales_per_month: float, avg_days: float):
    """Update market velocity metrics in one call."""
    record_sales_velocity(county_id, zip_code, sales_per_month)
    record_days_on_market(county_id, zip_code, avg_days)