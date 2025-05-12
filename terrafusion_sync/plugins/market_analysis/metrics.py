"""
TerraFusion SyncService - Market Analysis Plugin - Metrics

This module sets up Prometheus metrics for the Market Analysis plugin,
helping track performance, errors, and usage statistics.
"""

import logging
from prometheus_client import Counter, Gauge, Histogram

# Configure logging
logger = logging.getLogger(__name__)

# --- Counters ---

# Track job submissions
JOB_SUBMISSIONS = Counter(
    "market_analysis_jobs_submitted_total",
    "Total number of market analysis jobs submitted",
    ["county_id", "analysis_type"]
)

# Track job completions
JOB_COMPLETIONS = Counter(
    "market_analysis_jobs_completed_total",
    "Total number of market analysis jobs successfully completed",
    ["county_id", "analysis_type"]
)

# Track job failures
JOB_FAILURES = Counter(
    "market_analysis_jobs_failed_total",
    "Total number of market analysis jobs that failed",
    ["county_id", "analysis_type", "reason"]
)

# --- Gauges ---

# Track currently running jobs
JOBS_RUNNING = Gauge(
    "market_analysis_jobs_running",
    "Number of market analysis jobs currently running",
    ["county_id", "analysis_type"]
)

# Track job queue sizes
JOB_QUEUE_SIZE = Gauge(
    "market_analysis_job_queue_size",
    "Number of market analysis jobs in the queue",
    ["county_id", "analysis_type"]
)

# --- Histograms ---

# Track job processing times
JOB_PROCESSING_TIME = Histogram(
    "market_analysis_job_processing_seconds",
    "Time taken to process market analysis jobs",
    ["county_id", "analysis_type"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)  # 1s, 5s, 10s, 30s, 1m, 2m, 5m, 10m
)

# Track property valuation distribution
PROPERTY_VALUATION = Histogram(
    "market_analysis_property_valuation_dollars",
    "Distribution of property valuations in dollars",
    ["county_id", "property_type"],
    buckets=(100000, 200000, 300000, 400000, 500000, 750000, 1000000, 1500000, 2000000)
)

# Track price per square foot distribution
PRICE_PER_SQFT = Histogram(
    "market_analysis_price_per_sqft_dollars",
    "Distribution of price per square foot in dollars",
    ["county_id", "property_type"],
    buckets=(100, 150, 200, 250, 300, 350, 400, 500, 750, 1000)
)

# --- Utility Functions ---

def record_job_submission(county_id: str, analysis_type: str):
    """Record a job submission metric."""
    try:
        JOB_SUBMISSIONS.labels(county_id=county_id, analysis_type=analysis_type).inc()
        logger.debug(f"Recorded job submission: county={county_id}, type={analysis_type}")
    except Exception as e:
        logger.error(f"Failed to record job submission metric: {str(e)}")

def record_job_completion(county_id: str, analysis_type: str):
    """Record a job completion metric."""
    try:
        JOB_COMPLETIONS.labels(county_id=county_id, analysis_type=analysis_type).inc()
        logger.debug(f"Recorded job completion: county={county_id}, type={analysis_type}")
    except Exception as e:
        logger.error(f"Failed to record job completion metric: {str(e)}")

def record_job_failure(county_id: str, analysis_type: str, reason: str):
    """Record a job failure metric."""
    try:
        JOB_FAILURES.labels(
            county_id=county_id, 
            analysis_type=analysis_type,
            reason=reason
        ).inc()
        logger.debug(f"Recorded job failure: county={county_id}, type={analysis_type}, reason={reason}")
    except Exception as e:
        logger.error(f"Failed to record job failure metric: {str(e)}")

def update_running_jobs(county_id: str, analysis_type: str, count: int):
    """Update the number of running jobs."""
    try:
        JOBS_RUNNING.labels(county_id=county_id, analysis_type=analysis_type).set(count)
        logger.debug(f"Updated running jobs: county={county_id}, type={analysis_type}, count={count}")
    except Exception as e:
        logger.error(f"Failed to update running jobs metric: {str(e)}")

def record_job_processing_time(county_id: str, analysis_type: str, seconds: float):
    """Record job processing time in seconds."""
    try:
        JOB_PROCESSING_TIME.labels(county_id=county_id, analysis_type=analysis_type).observe(seconds)
        logger.debug(f"Recorded job processing time: county={county_id}, type={analysis_type}, seconds={seconds:.2f}")
    except Exception as e:
        logger.error(f"Failed to record job processing time metric: {str(e)}")

def record_property_valuation(county_id: str, property_type: str, value: float):
    """Record a property valuation in dollars."""
    try:
        PROPERTY_VALUATION.labels(county_id=county_id, property_type=property_type).observe(value)
        logger.debug(f"Recorded property valuation: county={county_id}, type={property_type}, value=${value:.2f}")
    except Exception as e:
        logger.error(f"Failed to record property valuation metric: {str(e)}")

def record_price_per_sqft(county_id: str, property_type: str, value: float):
    """Record a price per square foot in dollars."""
    try:
        PRICE_PER_SQFT.labels(county_id=county_id, property_type=property_type).observe(value)
        logger.debug(f"Recorded price per sqft: county={county_id}, type={property_type}, value=${value:.2f}")
    except Exception as e:
        logger.error(f"Failed to record price per sqft metric: {str(e)}")

# Initialize metrics on module load
logger.info("Market Analysis plugin metrics initialized")