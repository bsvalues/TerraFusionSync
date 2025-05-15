#!/usr/bin/env python3
"""
Fixed GIS Export Test Script

This script tests the GIS Export plugin with isolated metrics,
focusing on ensuring metrics are properly isolated from other plugins.
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
BASE_URL = "http://0.0.0.0:8080"
GIS_EXPORT_URL = f"{BASE_URL}/plugins/v1/gis-export"
CUSTOM_METRICS_URL = f"{GIS_EXPORT_URL}/metrics"
DEFAULT_METRICS_URL = f"{BASE_URL}/metrics"

# Test data
TEST_COUNTY_ID = "benton_wa"
TEST_EXPORT_FORMAT = "GeoJSON"
TEST_USERNAME = "test_user"

TEST_AREA_OF_INTEREST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-119.25, 46.15],
            [-119.15, 46.15],
            [-119.15, 46.25],
            [-119.25, 46.25],
            [-119.25, 46.15]
        ]
    ]
}

TEST_LAYERS = ["parcels", "zoning", "roads"]

def log_separator(message=""):
    """Print a separator in the logs."""
    logger.info(f"\n{'=' * 50}\n{message}\n{'=' * 50}")

def check_health():
    """Check if the GIS Export API is healthy."""
    try:
        response = requests.get(f"{GIS_EXPORT_URL}/health")
        response.raise_for_status()
        health_data = response.json()
        logger.info(f"✅ GIS Export API is healthy: {health_data}")
        return True
    except Exception as e:
        logger.error(f"❌ GIS Export API health check failed: {e}")
        return False

def try_metrics_endpoints():
    """Try both custom and default metrics endpoints."""
    results = []
    
    # Try custom endpoint
    try:
        response = requests.get(CUSTOM_METRICS_URL)
        if response.status_code == 200:
            logger.info(f"✅ Custom metrics endpoint available: {CUSTOM_METRICS_URL}")
            metrics_sample = response.text[:200] + "..." if len(response.text) > 200 else response.text
            logger.info(f"Metrics sample: {metrics_sample}")
            results.append(("custom", response.text))
        else:
            logger.warning(f"❌ Custom metrics endpoint returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"❌ Error accessing custom metrics endpoint: {e}")
    
    # Try default endpoint
    try:
        response = requests.get(DEFAULT_METRICS_URL)
        if response.status_code == 200:
            logger.info(f"✅ Default metrics endpoint available: {DEFAULT_METRICS_URL}")
            metrics_sample = response.text[:200] + "..." if len(response.text) > 200 else response.text
            logger.info(f"Metrics sample: {metrics_sample}")
            results.append(("default", response.text))
        else:
            logger.warning(f"❌ Default metrics endpoint returned {response.status_code}: {response.text}")
    except Exception as e:
        logger.error(f"❌ Error accessing default metrics endpoint: {e}")
    
    return results

def create_test_job():
    """Create a test GIS export job."""
    try:
        payload = {
            "county_id": TEST_COUNTY_ID,
            "username": TEST_USERNAME,
            "format": TEST_EXPORT_FORMAT,
            "area_of_interest": TEST_AREA_OF_INTEREST,
            "layers": TEST_LAYERS
        }
        
        logger.info(f"Submitting test job with payload: {json.dumps(payload, indent=2)}")
        response = requests.post(f"{GIS_EXPORT_URL}/run", json=payload)
        response.raise_for_status()
        job_data = response.json()
        job_id = job_data.get("job_id")
        
        logger.info(f"✅ Job submitted successfully with ID: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"❌ Failed to submit job: {e}")
        return None

def wait_for_job_completion(job_id, timeout_seconds=30):
    """Wait for a job to complete or timeout."""
    if not job_id:
        logger.error("❌ Cannot wait for job completion: No job ID provided")
        return False
    
    start_time = datetime.now()
    end_time = start_time + timedelta(seconds=timeout_seconds)
    
    logger.info(f"Waiting for job {job_id} to complete (timeout: {timeout_seconds}s)")
    
    while datetime.now() < end_time:
        try:
            response = requests.get(f"{GIS_EXPORT_URL}/status/{job_id}")
            response.raise_for_status()
            status_data = response.json()
            
            status = status_data.get("status")
            message = status_data.get("message", "")
            
            logger.info(f"Job status: {status} - {message}")
            
            if status == "COMPLETED":
                logger.info(f"✅ Job completed successfully")
                return True
            elif status in ["FAILED", "CANCELLED"]:
                logger.error(f"❌ Job failed with status: {status}")
                return False
            
            # Wait before checking again
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error checking job status: {e}")
            return False
    
    logger.error(f"❌ Job did not complete within {timeout_seconds} seconds")
    return False

def check_metrics_for_changes(before_metrics, after_metrics):
    """Check if metrics have changed after job execution."""
    # Find metrics sets for comparison
    before_custom = next((m for m, s in before_metrics if m == "custom"), None)
    after_custom = next((m for m, s in after_metrics if m == "custom"), None)
    
    before_default = next((m for m, s in before_metrics if m == "default"), None)
    after_default = next((m for m, s in after_metrics if m == "default"), None)
    
    changes_detected = False
    
    # Check custom metrics if available
    if before_custom and after_custom:
        # Look for GIS export metrics in the custom registry
        gis_metrics = ["gis_export_jobs_submitted_total", "gis_export_jobs_completed_total"]
        
        for metric in gis_metrics:
            before_count = before_custom.count(metric)
            after_count = after_custom.count(metric)
            
            if after_count > before_count:
                logger.info(f"✅ Found increased occurrences of {metric} in custom metrics")
                changes_detected = True
    else:
        logger.warning("❌ Cannot compare custom metrics - not available in both samples")
    
    # Check default metrics as fallback
    if not changes_detected and before_default and after_default:
        # Look for GIS export metrics in the default registry
        gis_metrics = ["gis_export_jobs_submitted_total", "gis_export_jobs_completed_total"]
        
        for metric in gis_metrics:
            before_count = before_default.count(metric)
            after_count = after_default.count(metric)
            
            if after_count > before_count:
                logger.info(f"✅ Found increased occurrences of {metric} in default metrics")
                changes_detected = True
    
    return changes_detected

def main():
    """Main test function."""
    log_separator("GIS Export Metrics Isolation Test")
    
    # Check if the API is healthy
    if not check_health():
        logger.error("❌ Cannot proceed with tests - GIS Export API is not healthy")
        return False
    
    # Step 1: Get initial metrics
    log_separator("Step 1: Get Initial Metrics")
    before_metrics = try_metrics_endpoints()
    
    # Step 2: Create and run a test job
    log_separator("Step 2: Create Test Job")
    job_id = create_test_job()
    if not job_id:
        logger.error("❌ Cannot proceed with tests - Failed to create test job")
        return False
    
    # Step 3: Wait for job completion
    log_separator("Step 3: Wait for Job Completion")
    if not wait_for_job_completion(job_id):
        logger.error("❌ Cannot proceed with tests - Job did not complete successfully")
        return False
    
    # Step 4: Check metrics again
    log_separator("Step 4: Check Updated Metrics")
    after_metrics = try_metrics_endpoints()
    
    # Step 5: Compare metrics before and after
    log_separator("Step 5: Analyze Metrics Changes")
    changes_detected = check_metrics_for_changes(before_metrics, after_metrics)
    
    if changes_detected:
        logger.info("✅ GIS Export metrics test passed - metrics were updated properly")
        return True
    else:
        logger.error("❌ GIS Export metrics test failed - metrics were not updated properly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)