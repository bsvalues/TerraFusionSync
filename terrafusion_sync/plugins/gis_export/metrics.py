"""
TerraFusion SyncService - GIS Export Plugin - Metrics

This module defines Prometheus metrics for the GIS Export plugin.
The metrics use a dedicated registry to avoid conflicts with other plugins.
"""

import logging
import os
from prometheus_client import Counter, Histogram, CollectorRegistry, REGISTRY

logger = logging.getLogger(__name__)

# Create a class-based implementation to avoid initialization issues
class GisExportMetrics:
    """GIS Export plugin metrics container to avoid registry conflicts."""
    
    # Class-level shared registry
    registry = None
    initialized = False
    
    # Dummy metric for fallback
    class DummyMetric:
        def inc(self, amount=1): pass
        def observe(self, amount): pass
        def labels(self, **kwargs): return self
    
    # Initialize metric placeholders
    jobs_submitted = DummyMetric()
    jobs_completed = DummyMetric()
    jobs_failed = DummyMetric()
    processing_duration = DummyMetric()
    file_size = DummyMetric()
    record_count = DummyMetric()
    
    @classmethod
    def initialize(cls, use_default_registry=False):
        """Initialize metrics, optionally with the default registry."""
        if cls.initialized:
            return
            
        try:
            # Use default registry or create a dedicated one
            registry_to_use = REGISTRY if use_default_registry else CollectorRegistry()
            cls.registry = registry_to_use
            
            # Define Prometheus metrics for GIS Export with prefix to avoid conflicts
            cls.jobs_submitted = Counter(
                "gis_export_jobs_submitted_total",
                "Total number of GIS export jobs submitted",
                ["county_id", "export_format", "status_on_submit"],
                registry=registry_to_use
            )
            
            cls.jobs_completed = Counter(
                "gis_export_jobs_completed_total",
                "Total number of GIS export jobs that completed successfully",
                ["county_id", "export_format"],
                registry=registry_to_use
            )
            
            cls.jobs_failed = Counter(
                "gis_export_jobs_failed_total",
                "Total number of GIS export jobs that failed",
                ["county_id", "export_format", "failure_reason"],
                registry=registry_to_use
            )
            
            cls.processing_duration = Histogram(
                "gis_export_processing_duration_seconds",
                "Time spent processing GIS export jobs (seconds)",
                ["county_id", "export_format"],
                buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600),  # 1s to 1h
                registry=registry_to_use
            )
            
            cls.file_size = Histogram(
                "gis_export_file_size_kb",
                "Size of exported GIS data files in kilobytes",
                ["county_id", "export_format"],
                buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000),  # 10KB to 100MB
                registry=registry_to_use
            )
            
            cls.record_count = Histogram(
                "gis_export_record_count",
                "Number of records included in GIS exports",
                ["county_id", "export_format"],
                buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000),  # 10 to 100K records
                registry=registry_to_use
            )
            
            cls.initialized = True
            logger.info("GIS Export metrics initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize GIS Export metrics: {e}", exc_info=True)
            
# Define aliases for backward compatibility and ease of use
# Check environment variable to determine registry usage
use_custom_registry = os.environ.get("GIS_EXPORT_USE_CUSTOM_REGISTRY", "0") == "1"

try:
    if use_custom_registry:
        logger.info("Using custom registry for GIS Export metrics")
        GisExportMetrics.initialize(use_default_registry=False)
    else:
        logger.info("Using default registry for GIS Export metrics")
        GisExportMetrics.initialize(use_default_registry=True)
except Exception as e:
    logger.error(f"Failed to initialize GIS Export metrics: {e}", exc_info=True)
    # No fallback attempt - we'll rely on the dummy metrics if initialization fails

# Public exports
GIS_EXPORT_JOBS_SUBMITTED_TOTAL = GisExportMetrics.jobs_submitted
GIS_EXPORT_JOBS_COMPLETED_TOTAL = GisExportMetrics.jobs_completed
GIS_EXPORT_JOBS_FAILED_TOTAL = GisExportMetrics.jobs_failed
GIS_EXPORT_PROCESSING_DURATION_SECONDS = GisExportMetrics.processing_duration
GIS_EXPORT_FILE_SIZE_KB = GisExportMetrics.file_size
GIS_EXPORT_RECORD_COUNT = GisExportMetrics.record_count