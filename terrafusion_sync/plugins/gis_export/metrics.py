"""
TerraFusion SyncService - GIS Export Plugin - Metrics

This module defines Prometheus metrics for monitoring the GIS Export plugin.
"""

import logging
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Define metrics for GIS Export plugin
# Job count metrics
GIS_EXPORT_JOBS_SUBMITTED_TOTAL = Counter(
    'gis_export_jobs_submitted_total',
    'Total number of GIS export jobs submitted',
    ['county_id', 'export_format']
)

GIS_EXPORT_JOBS_COMPLETED_TOTAL = Counter(
    'gis_export_jobs_completed_total',
    'Total number of GIS export jobs completed successfully',
    ['county_id', 'export_format']
)

GIS_EXPORT_JOBS_FAILED_TOTAL = Counter(
    'gis_export_jobs_failed_total',
    'Total number of GIS export jobs that failed',
    ['county_id', 'export_format', 'error_type']
)

# Performance metrics
GIS_EXPORT_PROCESSING_DURATION_SECONDS = Histogram(
    'gis_export_processing_duration_seconds',
    'Duration of GIS export job processing in seconds',
    ['county_id', 'export_format'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600)  # 1s, 5s, 10s, 30s, 1m, 2m, 5m, 10m
)

# Result size metrics
GIS_EXPORT_FILE_SIZE_KB = Histogram(
    'gis_export_file_size_kb',
    'Size of exported GIS files in KB',
    ['county_id', 'export_format'],
    buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000)  # 10KB to 100MB
)

GIS_EXPORT_RECORD_COUNT = Histogram(
    'gis_export_record_count',
    'Number of records in GIS export results',
    ['county_id', 'export_format'],
    buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000)  # 10 to 500k records
)

def register_metrics():
    """Register all metrics to ensure they're initialized."""
    # This function is mainly for documentation purposes
    # Prometheus client automatically registers metrics when they're defined
    logger.info("GIS Export plugin metrics initialized")