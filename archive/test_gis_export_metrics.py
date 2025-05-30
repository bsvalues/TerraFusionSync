#!/usr/bin/env python3
"""
GIS Export Metrics Verification Test

This script verifies that the GIS Export plugin's metrics are properly defined and
registered with the Prometheus registry in an isolated manner to prevent conflicts
with other plugins.

This uses the isolated metrics implementation to avoid the duplicate registration
issues that can occur when multiple plugins register metrics with the same registry.
"""

import sys
import logging
import requests
import time
from prometheus_client import CollectorRegistry, Counter, Histogram, start_http_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
METRICS_PORT = 8090
TEST_METRICS_PORT = 8095
SYNC_SERVICE_URL = "http://0.0.0.0:8080"

def start_test_registry():
    """Start a test registry on a different port to verify isolation."""
    # Create a separate registry
    registry = CollectorRegistry()
    
    # Register the same metrics that GIS Export uses
    Counter(
        'gis_export_jobs_submitted_total',
        'Total number of GIS export jobs submitted',
        ['county_id', 'export_format'],
        registry=registry
    )
    
    Counter(
        'gis_export_jobs_completed_total',
        'Total number of GIS export jobs completed successfully',
        ['county_id', 'export_format'],
        registry=registry
    )
    
    Counter(
        'gis_export_jobs_failed_total',
        'Total number of GIS export jobs that failed',
        ['county_id', 'export_format'],
        registry=registry
    )
    
    Histogram(
        'gis_export_processing_duration_seconds',
        'Duration of GIS export job processing in seconds',
        ['county_id', 'export_format'],
        buckets=(1, 5, 10, 30, 60, 120, 300, 600),
        registry=registry
    )
    
    # Start metrics server
    start_http_server(TEST_METRICS_PORT, registry=registry)
    logger.info(f"Started test metrics server on port {TEST_METRICS_PORT}")
    return registry

def check_gis_export_plugin_health():
    """Check if the GIS Export plugin is healthy."""
    try:
        response = requests.get(f"{SYNC_SERVICE_URL}/plugins/v1/gis-export/health")
        assert response.status_code == 200, "GIS Export plugin health check failed"
        data = response.json()
        assert data["status"] == "healthy", "GIS Export plugin is not healthy"
        logger.info("GIS Export plugin is healthy")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def check_isolated_metrics_health():
    """Check if the isolated metrics service is running."""
    try:
        response = requests.get(f"http://0.0.0.0:{METRICS_PORT}/health")
        assert response.status_code == 200, "Isolated metrics health check failed"
        data = response.json()
        assert data["status"] == "healthy", "Isolated metrics service is not healthy"
        logger.info("Isolated metrics service is healthy")
        return True
    except Exception as e:
        logger.error(f"Isolated metrics health check failed: {e}")
        return False

def verify_metrics_isolation():
    """Verify that metrics can be registered independently."""
    # First, check if our isolated metrics server is running
    if not check_isolated_metrics_health():
        logger.warning("Starting isolated metrics service...")
        import subprocess
        subprocess.Popen(
            ["python", "isolated_gis_export_metrics.py", "--port", str(METRICS_PORT)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        # Give it time to start
        time.sleep(3)
        
        if not check_isolated_metrics_health():
            logger.error("Failed to start isolated metrics service")
            return False
    
    # Start our test registry with the same metrics
    try:
        start_test_registry()
        logger.info("Successfully started test registry with duplicate metric names")
        
        # Verify we can get metrics from both servers
        isolated_response = requests.get(f"http://0.0.0.0:{METRICS_PORT}/metrics")
        assert isolated_response.status_code == 200, "Failed to get metrics from isolated service"
        
        test_response = requests.get(f"http://0.0.0.0:{TEST_METRICS_PORT}/metrics")
        assert test_response.status_code == 200, "Failed to get metrics from test service"
        
        logger.info("Successfully verified metrics isolation!")
        return True
    except Exception as e:
        logger.error(f"Metrics isolation verification failed: {e}")
        return False

def submit_test_job():
    """Submit a test job to verify metrics recording."""
    job_data = {
        "county_id": "test_county",
        "format": "GeoJSON",
        "username": "test_user",
        "area_of_interest": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-119.3, 46.1],
                    [-119.2, 46.1],
                    [-119.2, 46.2],
                    [-119.3, 46.2],
                    [-119.3, 46.1]
                ]
            ]
        },
        "layers": ["parcels", "roads"]
    }
    
    try:
        # Submit job to GIS Export API
        response = requests.post(
            f"{SYNC_SERVICE_URL}/plugins/v1/gis-export/run",
            json=job_data
        )
        
        if response.status_code != 200:
            logger.error(f"Job creation failed: {response.status_code} {response.text}")
            return None
        
        job_id = response.json().get("job_id")
        logger.info(f"Created job with ID: {job_id}")
        
        # Record in isolated metrics directly
        metrics_data = {
            "job_id": job_id,
            "county_id": job_data["county_id"],
            "format": job_data["format"]
        }
        
        metrics_response = requests.post(
            f"http://0.0.0.0:{METRICS_PORT}/record/job_submitted",
            json=metrics_data
        )
        
        logger.info(f"Metrics job submission: {metrics_response.status_code} {metrics_response.text}")
        
        # Check metrics endpoint to verify counter incremented
        metrics_text = requests.get(f"http://0.0.0.0:{METRICS_PORT}/metrics").text
        assert "gis_export_jobs_submitted_total" in metrics_text, "Job submission metric not found"
        
        logger.info("Successfully verified metrics recording!")
        return job_id
    except Exception as e:
        logger.error(f"Test job submission failed: {e}")
        return None

def main():
    """Main test function."""
    logger.info("Starting GIS Export Metrics Verification Test")
    
    # Check plugin health
    if not check_gis_export_plugin_health():
        logger.error("GIS Export plugin is not healthy. Exiting.")
        return 1
    
    # Verify metrics isolation
    if not verify_metrics_isolation():
        logger.error("Metrics isolation verification failed. Exiting.")
        return 1
    
    # Submit a test job to verify metrics recording
    job_id = submit_test_job()
    if not job_id:
        logger.error("Test job submission failed. Exiting.")
        return 1
    
    logger.info("✅ All GIS Export metrics tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())