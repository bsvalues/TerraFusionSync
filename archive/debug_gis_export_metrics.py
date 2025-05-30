#!/usr/bin/env python3
"""
Debug script for GIS Export metrics.

This script directly initializes the metrics module and tests its functionality.
"""

import os
import sys
import logging
import importlib
from pprint import pprint

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_metrics_initialization():
    """Debug metrics initialization and registration."""
    logger.info("Testing GIS Export metrics initialization...")
    
    try:
        # Import the metrics modules
        logger.debug("Importing metrics module...")
        from terrafusion_sync.plugins.gis_export.metrics import (
            GisExportMetrics, 
            register_metrics,
            GIS_EXPORT_JOBS_SUBMITTED_TOTAL
        )
        
        # Check initial state
        logger.debug(f"Initial state - GisExportMetrics.registry: {GisExportMetrics.registry}")
        logger.debug(f"Initial state - GisExportMetrics.jobs_submitted: {GisExportMetrics.jobs_submitted}")
        
        # Register metrics
        logger.info("Calling register_metrics()...")
        register_metrics()
        
        # Check registered state
        logger.debug(f"After registration - GisExportMetrics.registry: {GisExportMetrics.registry}")
        logger.debug(f"After registration - GisExportMetrics.jobs_submitted: {GisExportMetrics.jobs_submitted}")
        logger.debug(f"Global GIS_EXPORT_JOBS_SUBMITTED_TOTAL: {GIS_EXPORT_JOBS_SUBMITTED_TOTAL}")
        
        # Test direct increment
        logger.info("Testing direct increment of jobs_submitted...")
        GisExportMetrics.jobs_submitted.labels(
            county_id="TEST_COUNTY", 
            export_format="TEST_FORMAT"
        ).inc()
        
        # Test global variable increment
        logger.info("Testing global variable increment...")
        GIS_EXPORT_JOBS_SUBMITTED_TOTAL.labels(
            county_id="TEST_COUNTY_2", 
            export_format="TEST_FORMAT_2"
        ).inc()
        
        # Import prometheus_client to check metrics
        logger.info("Getting metrics from prometheus_client...")
        from prometheus_client import REGISTRY, generate_latest
        
        # Get metrics from default registry
        metrics_text = generate_latest(REGISTRY).decode("utf-8")
        
        # Check for our metrics
        logger.info("Checking metrics text for our metrics...")
        for line in metrics_text.split("\n"):
            if "gis_export" in line:
                logger.info(f"Found metric: {line}")
        
        return True
    except Exception as e:
        logger.error(f"Error in metrics debug: {e}", exc_info=True)
        return False

def check_router_initialization():
    """Check router initialization and metrics usage."""
    logger.info("Testing GIS Export router initialization...")
    
    try:
        # Import the router module
        logger.debug("Importing router module...")
        from terrafusion_sync.plugins.gis_export import router
        
        # Check if router loaded
        logger.debug(f"Router object: {router}")
        
        # Check metrics_available flag
        if hasattr(router, "metrics_available"):
            logger.info(f"Router metrics_available flag: {router.metrics_available}")
        else:
            logger.warning("Router does not have metrics_available attribute!")
        
        # Check imported metric objects
        metric_names = [
            "GIS_EXPORT_JOBS_SUBMITTED_TOTAL",
            "GIS_EXPORT_JOBS_COMPLETED_TOTAL",
            "GIS_EXPORT_JOBS_FAILED_TOTAL",
            "GIS_EXPORT_PROCESSING_DURATION_SECONDS",
            "GIS_EXPORT_FILE_SIZE_KB",
            "GIS_EXPORT_RECORD_COUNT"
        ]
        
        for name in metric_names:
            if hasattr(router, name):
                logger.info(f"Router has {name}: {getattr(router, name)}")
            else:
                logger.warning(f"Router does not have {name} attribute!")
        
        return True
    except Exception as e:
        logger.error(f"Error in router debug: {e}", exc_info=True)
        return False

def check_plugin_initialization():
    """Check overall plugin initialization."""
    logger.info("Testing GIS Export plugin initialization...")
    
    try:
        # Import the plugin package
        logger.debug("Importing plugin package...")
        import terrafusion_sync.plugins.gis_export as gis_export
        
        # Reload to ensure we get fresh initialization
        logger.debug("Reloading plugin package...")
        importlib.reload(gis_export)
        
        # Check if initialization occurred
        logger.debug(f"Plugin __init__ executed, router: {gis_export.router}")
        
        return True
    except Exception as e:
        logger.error(f"Error in plugin initialization debug: {e}", exc_info=True)
        return False

def main():
    """Run all debug functions."""
    logger.info("===== GIS Export Metrics Debug =====")
    
    # Debug metrics initialization
    metrics_result = debug_metrics_initialization()
    logger.info(f"Metrics initialization debug: {'SUCCESS' if metrics_result else 'FAILED'}")
    
    # Check router initialization
    router_result = check_router_initialization()
    logger.info(f"Router initialization debug: {'SUCCESS' if router_result else 'FAILED'}")
    
    # Check plugin initialization
    plugin_result = check_plugin_initialization()
    logger.info(f"Plugin initialization debug: {'SUCCESS' if plugin_result else 'FAILED'}")
    
    # Overall status
    if metrics_result and router_result and plugin_result:
        logger.info("✅ All checks passed")
    else:
        logger.error("❌ Some checks failed")

if __name__ == "__main__":
    main()