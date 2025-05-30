#!/usr/bin/env python
"""
Test Metrics Isolation

This script verifies that our metrics isolation approach works by creating 
duplicate metrics registries and ensuring they don't conflict.
"""

import logging
import os
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

# Setup logging
logging.basicConfig(level=logging.INFO, 
                   format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_metrics_isolation():
    """Test that metrics can be isolated in separate registries."""
    logger.info("Testing metrics isolation...")
    
    # Create two separate registries
    registry1 = CollectorRegistry()
    registry2 = CollectorRegistry()
    
    # Create a counter with the same name in both registries
    counter1 = Counter(
        "test_counter", 
        "Test counter for isolation testing",
        registry=registry1
    )
    
    counter2 = Counter(
        "test_counter", 
        "Test counter for isolation testing",
        registry=registry2
    )
    
    # Increment counters
    counter1.inc(1)
    counter2.inc(2)
    
    # Generate output from both registries
    output1 = generate_latest(registry1).decode("utf-8")
    output2 = generate_latest(registry2).decode("utf-8")
    
    logger.info(f"Registry 1 output:\n{output1}")
    logger.info(f"Registry 2 output:\n{output2}")
    
    # Verify the counters are different
    assert "test_counter 1.0" in output1, "Counter 1 should have value 1.0"
    assert "test_counter 2.0" in output2, "Counter 2 should have value 2.0"
    
    logger.info("✅ Metrics isolation test passed!")
    return True

def test_gis_export_metrics():
    """Test our GIS Export metrics isolation approach."""
    logger.info("Testing GIS Export metrics isolation...")
    
    # Set environment variable for custom registry
    os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"
    
    # Import our metrics class
    from terrafusion_sync.plugins.gis_export.metrics import GisExportMetrics
    
    # Initialize with custom registry
    GisExportMetrics.initialize(use_default_registry=False)
    
    # Use metrics
    GisExportMetrics.jobs_submitted.labels(
        county_id="TEST_COUNTY",
        export_format="GeoJSON",
        status_on_submit="PENDING"
    ).inc()
    
    # Get metrics output
    if GisExportMetrics.registry:
        output = generate_latest(GisExportMetrics.registry).decode("utf-8")
        logger.info(f"GIS Export metrics output:\n{output}")
        
        # Verify counter exists
        assert "gis_export_jobs_submitted_total" in output, "GIS Export jobs counter should exist"
        
        logger.info("✅ GIS Export metrics isolation test passed!")
        return True
    else:
        logger.error("❌ GIS Export metrics registry not initialized!")
        return False

if __name__ == "__main__":
    # Run basic isolation test
    test_metrics_isolation()
    
    # Test GIS Export metrics
    test_gis_export_metrics()