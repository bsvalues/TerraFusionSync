#!/usr/bin/env python3
"""
Test script for reporting metrics in the TerraFusion SyncService.

This script verifies that Prometheus metrics for the reporting plugin 
are correctly registered and exposed through the /metrics endpoint.
"""

import os
import sys
import json
import requests
import logging
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("reporting_metrics_test")

# SyncService URL - default to standard development URL
SYNCSERVICE_URL = os.environ.get("SYNCSERVICE_URL", "http://0.0.0.0:8080")

# Expected metrics for the reporting plugin
EXPECTED_METRICS = [
    "report_jobs_submitted_total",
    "report_processing_duration_seconds",
    "report_jobs_failed_total",
    "report_jobs_pending",
    "report_jobs_in_progress"
]

def check_metrics_endpoint():
    """Check if the metrics endpoint is accessible."""
    metrics_url = urljoin(SYNCSERVICE_URL, "/metrics")
    
    try:
        logger.info(f"Checking metrics endpoint: {metrics_url}")
        response = requests.get(metrics_url)
        response.raise_for_status()
        
        logger.info(f"Metrics endpoint accessible: {response.status_code}")
        return response.text
    except requests.RequestException as e:
        logger.error(f"Failed to access metrics endpoint: {e}")
        return None

def verify_reporting_metrics(metrics_text):
    """Verify that the reporting metrics are present in the metrics text."""
    if not metrics_text:
        logger.error("No metrics text to verify")
        return False
    
    found_metrics = []
    missing_metrics = []
    
    for metric in EXPECTED_METRICS:
        if metric in metrics_text:
            found_metrics.append(metric)
            logger.info(f"✓ Found metric: {metric}")
        else:
            missing_metrics.append(metric)
            logger.error(f"✗ Missing metric: {metric}")
    
    if missing_metrics:
        logger.error(f"Missing {len(missing_metrics)} expected metrics")
        return False
    
    logger.info(f"Found all {len(EXPECTED_METRICS)} expected metrics")
    return True

def check_health_endpoint():
    """Check the health endpoint to verify the service is running."""
    health_url = urljoin(SYNCSERVICE_URL, "/health")
    
    try:
        logger.info(f"Checking health endpoint: {health_url}")
        response = requests.get(health_url)
        response.raise_for_status()
        
        health_data = response.json()
        logger.info(f"Health status: {json.dumps(health_data, indent=2)}")
        
        return health_data.get("status") == "healthy"
    except requests.RequestException as e:
        logger.error(f"Failed to access health endpoint: {e}")
        return False

def main():
    """Run the reporting metrics test."""
    logger.info("Starting reporting metrics test")
    
    # First, check the health endpoint
    if not check_health_endpoint():
        logger.error("SyncService is not healthy. Cannot proceed with tests.")
        return 1
    
    # Get metrics from the endpoint
    metrics_text = check_metrics_endpoint()
    
    # Verify reporting metrics
    if verify_reporting_metrics(metrics_text):
        logger.info("✅ Reporting metrics test passed")
        return 0
    else:
        logger.error("❌ Reporting metrics test failed")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.exception("Error running reporting metrics test")
        sys.exit(1)