"""
GIS Export Metrics Module

This module defines Prometheus metrics for the GIS Export plugin.
It uses a custom registry to avoid conflicts with other plugins.
"""

import os
import logging
from typing import Optional
from prometheus_client import Counter, Histogram, CollectorRegistry, Gauge

logger = logging.getLogger(__name__)

class GisExportMetrics:
    """
    Metrics for the GIS Export plugin.
    
    This class uses a custom registry to avoid conflicts with other plugins when they're
    loaded in the same process. The metrics are initialized with this custom registry.
    
    Environment Variables:
        GIS_EXPORT_USE_CUSTOM_REGISTRY: Set to "1" to use a custom registry
    """
    
    # Class-level registry
    registry: Optional[CollectorRegistry] = None
    initialized: bool = False
    
    # Metrics definitions
    jobs_submitted: Optional[Counter] = None
    jobs_completed: Optional[Counter] = None
    jobs_failed: Optional[Counter] = None
    processing_duration: Optional[Histogram] = None
    file_size: Optional[Histogram] = None
    record_count: Optional[Histogram] = None
    
    @classmethod
    def initialize(cls, use_default_registry: bool = None) -> None:
        """
        Initialize metrics with either the default registry or a custom one.
        
        Args:
            use_default_registry: Whether to use the default registry. If None, determined by env var.
        """
        if cls.initialized:
            logger.info("GIS Export metrics already initialized")
            return
        
        # Determine whether to use a custom registry based on the environment variable
        if use_default_registry is None:
            use_custom_registry = os.environ.get("GIS_EXPORT_USE_CUSTOM_REGISTRY", "0") == "1"
            use_default_registry = not use_custom_registry
        
        # Create a custom registry if needed
        registry = None
        if not use_default_registry:
            logger.info("Initializing GIS Export metrics with custom registry")
            registry = CollectorRegistry()
            cls.registry = registry
        else:
            logger.info("Initializing GIS Export metrics with default registry")
        
        # Create metrics
        cls.jobs_submitted = Counter(
            "gis_export_jobs_submitted_total",
            "Total number of GIS export jobs submitted",
            ["county_id", "export_format", "status_on_submit"],
            registry=registry
        )
        
        cls.jobs_completed = Counter(
            "gis_export_jobs_completed_total",
            "Total number of GIS export jobs completed successfully",
            ["county_id", "export_format"],
            registry=registry
        )
        
        cls.jobs_failed = Counter(
            "gis_export_jobs_failed_total",
            "Total number of GIS export jobs that failed",
            ["county_id", "export_format", "failure_reason"],
            registry=registry
        )
        
        cls.processing_duration = Histogram(
            "gis_export_processing_duration_seconds",
            "Time taken to process GIS export jobs",
            ["county_id", "export_format"],
            buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
            registry=registry
        )
        
        cls.file_size = Histogram(
            "gis_export_file_size_kb",
            "Size of exported GIS files in kilobytes",
            ["county_id", "export_format"],
            buckets=(1, 10, 100, 1000, 10000, 100000, 1000000),
            registry=registry
        )
        
        cls.record_count = Histogram(
            "gis_export_record_count",
            "Number of records in exported GIS files",
            ["county_id", "export_format"],
            buckets=(1, 10, 100, 1000, 10000, 100000, 1000000),
            registry=registry
        )
        
        cls.initialized = True
        logger.info("GIS Export metrics initialized successfully")
    
    @classmethod
    def reset(cls) -> None:
        """Reset all metrics to uninitialized state."""
        cls.registry = None
        cls.jobs_submitted = None
        cls.jobs_completed = None
        cls.jobs_failed = None
        cls.processing_duration = None
        cls.file_size = None
        cls.record_count = None
        cls.initialized = False
        logger.info("GIS Export metrics reset")