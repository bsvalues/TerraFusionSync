"""
TerraFusion SyncService - GIS Export Plugin - Metrics

This module defines Prometheus metrics for the GIS Export plugin.
"""

import logging
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

try:
    # Define Prometheus metrics for GIS Export
    GIS_EXPORT_JOBS_SUBMITTED_TOTAL = Counter(
        "gis_export_jobs_submitted_total",
        "Total number of GIS export jobs submitted",
        ["county_id", "export_format", "status_on_submit"]
    )

    GIS_EXPORT_JOBS_COMPLETED_TOTAL = Counter(
        "gis_export_jobs_completed_total",
        "Total number of GIS export jobs that completed successfully",
        ["county_id", "export_format"]
    )

    GIS_EXPORT_JOBS_FAILED_TOTAL = Counter(
        "gis_export_jobs_failed_total",
        "Total number of GIS export jobs that failed",
        ["county_id", "export_format", "failure_reason"]
    )

    GIS_EXPORT_PROCESSING_DURATION_SECONDS = Histogram(
        "gis_export_processing_duration_seconds",
        "Time spent processing GIS export jobs (seconds)",
        ["county_id", "export_format"],
        buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)  # 1s to 1h
    )

    GIS_EXPORT_FILE_SIZE_KB = Histogram(
        "gis_export_file_size_kb",
        "Size of exported GIS data files in kilobytes",
        ["county_id", "export_format"],
        buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000)  # 10KB to 100MB
    )

    GIS_EXPORT_RECORD_COUNT = Histogram(
        "gis_export_record_count",
        "Number of records included in GIS exports",
        ["county_id", "export_format"],
        buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000)  # 10 to 100K records
    )

    logger.info("GIS Export metrics initialized")
except Exception as e:
    logger.error(f"Failed to initialize GIS Export metrics: {e}", exc_info=True)
    # Define dummy metrics for fallback
    class DummyMetric:
        def inc(self, amount=1): pass
        def observe(self, amount): pass
        def labels(self, **kwargs): return self
    
    GIS_EXPORT_JOBS_SUBMITTED_TOTAL = DummyMetric()
    GIS_EXPORT_JOBS_COMPLETED_TOTAL = DummyMetric()
    GIS_EXPORT_JOBS_FAILED_TOTAL = DummyMetric()
    GIS_EXPORT_PROCESSING_DURATION_SECONDS = DummyMetric()
    GIS_EXPORT_FILE_SIZE_KB = DummyMetric()
    GIS_EXPORT_RECORD_COUNT = DummyMetric()