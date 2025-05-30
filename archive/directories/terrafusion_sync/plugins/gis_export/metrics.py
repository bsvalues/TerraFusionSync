"""
TerraFusion SyncService - GIS Export Plugin - Metrics

This module defines Prometheus metrics for monitoring the GIS Export plugin.
"""

import os
import logging
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

logger = logging.getLogger(__name__)

class GisExportMetrics:
    """Class to manage GIS Export metrics with optional custom registry."""
    
    # Class variables for the registry and metrics
    registry = None
    
    # Metrics
    jobs_submitted = None
    jobs_completed = None 
    jobs_failed = None
    processing_duration = None
    file_size = None
    record_count = None
    
    @classmethod
    def initialize(cls, use_default_registry=True):
        """
        Initialize metrics with optional custom registry.
        
        Args:
            use_default_registry: If False, use a custom registry
        """
        # Determine if we should use a custom registry
        use_custom = os.environ.get("GIS_EXPORT_USE_CUSTOM_REGISTRY", "0") == "1"
        use_custom = use_custom or not use_default_registry
        
        if use_custom:
            logger.info("Initializing GIS Export metrics with custom registry")
            cls.registry = CollectorRegistry()
        else:
            logger.info("Initializing GIS Export metrics with default registry")
            cls.registry = None
        
        # Create metrics
        registry_arg = cls.registry if use_custom else None
        
        # Job count metrics
        cls.jobs_submitted = Counter(
            'gis_export_jobs_submitted_total',
            'Total number of GIS export jobs submitted',
            ['county_id', 'export_format'],
            registry=registry_arg
        )
        
        cls.jobs_completed = Counter(
            'gis_export_jobs_completed_total',
            'Total number of GIS export jobs completed successfully',
            ['county_id', 'export_format'],
            registry=registry_arg
        )
        
        cls.jobs_failed = Counter(
            'gis_export_jobs_failed_total',
            'Total number of GIS export jobs that failed',
            ['county_id', 'export_format', 'error_type'],
            registry=registry_arg
        )
        
        # Performance metrics
        cls.processing_duration = Histogram(
            'gis_export_processing_duration_seconds',
            'Duration of GIS export job processing in seconds',
            ['county_id', 'export_format'],
            buckets=(1, 5, 10, 30, 60, 120, 300, 600),  # 1s, 5s, 10s, 30s, 1m, 2m, 5m, 10m
            registry=registry_arg
        )
        
        # Result size metrics
        cls.file_size = Histogram(
            'gis_export_file_size_kb',
            'Size of exported GIS files in KB',
            ['county_id', 'export_format'],
            buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000),  # 10KB to 100MB
            registry=registry_arg
        )
        
        cls.record_count = Histogram(
            'gis_export_record_count',
            'Number of records in GIS export results',
            ['county_id', 'export_format'],
            buckets=(10, 100, 500, 1000, 5000, 10000, 50000, 100000, 500000),  # 10 to 500k records
            registry=registry_arg
        )
        
        logger.info("GIS Export metrics initialized successfully")

    @classmethod
    def get_metrics(cls):
        """
        Get metrics as Prometheus-formatted text.
        
        Returns:
            String with Prometheus format metrics
        """
        if cls.registry:
            return generate_latest(cls.registry).decode('utf-8')
        return "# GIS Export metrics are using the default registry"

# For backward compatibility - create top-level variables
# These will be populated by the router importing directly
GIS_EXPORT_JOBS_SUBMITTED_TOTAL = None
GIS_EXPORT_JOBS_COMPLETED_TOTAL = None
GIS_EXPORT_JOBS_FAILED_TOTAL = None
GIS_EXPORT_PROCESSING_DURATION_SECONDS = None
GIS_EXPORT_FILE_SIZE_KB = None
GIS_EXPORT_RECORD_COUNT = None

def register_metrics():
    """Register all metrics to ensure they're initialized."""
    # Initialize metrics
    GisExportMetrics.initialize(use_default_registry=True)
    
    # Update top-level variables for backward compatibility
    global GIS_EXPORT_JOBS_SUBMITTED_TOTAL, GIS_EXPORT_JOBS_COMPLETED_TOTAL, GIS_EXPORT_JOBS_FAILED_TOTAL
    global GIS_EXPORT_PROCESSING_DURATION_SECONDS, GIS_EXPORT_FILE_SIZE_KB, GIS_EXPORT_RECORD_COUNT
    
    GIS_EXPORT_JOBS_SUBMITTED_TOTAL = GisExportMetrics.jobs_submitted
    GIS_EXPORT_JOBS_COMPLETED_TOTAL = GisExportMetrics.jobs_completed
    GIS_EXPORT_JOBS_FAILED_TOTAL = GisExportMetrics.jobs_failed
    GIS_EXPORT_PROCESSING_DURATION_SECONDS = GisExportMetrics.processing_duration
    GIS_EXPORT_FILE_SIZE_KB = GisExportMetrics.file_size
    GIS_EXPORT_RECORD_COUNT = GisExportMetrics.record_count
    
    logger.info("GIS Export global metrics registered")