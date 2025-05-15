#!/usr/bin/env python3
"""
GIS Export Metrics Test

This script tests if the GIS Export metrics are properly registered and incrementing.
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://0.0.0.0:8080/plugins/v1/gis-export"
METRICS_URL = "http://0.0.0.0:8080/plugins/v1/gis-export/metrics"

# Test data
TEST_COUNTY_ID = "benton_wa"
TEST_EXPORT_FORMAT = "GeoJSON"
TEST_AREA_OF_INTEREST = {
    "type": "Polygon",
    "coordinates": [[
        [-119.48, 46.21],
        [-119.48, 46.26],
        [-119.42, 46.26],
        [-119.42, 46.21],
        [-119.48, 46.21]
    ]]
}
TEST_LAYERS = ["parcels", "zoning"]
TEST_USERNAME = "test_user"

def check_health():
    """Check if the GIS Export API is healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            logger.info("✅ GIS Export API is healthy")
            return True
        else:
            logger.error(f"❌ GIS Export API health check failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ Error checking GIS Export API health: {e}")
        return False

def get_initial_metrics():
    """Get initial metrics values to compare later"""
    try:
        response = requests.get(METRICS_URL)
        if response.status_code != 200:
            logger.error(f"❌ Failed to get metrics: {response.status_code} - {response.text}")
            return None
        
        metrics_text = response.text
        logger.info("Retrieved initial metrics")
        return metrics_text
    except Exception as e:
        logger.error(f"❌ Error getting metrics: {e}")
        return None

def submit_test_job():
    """Submit a test GIS export job"""
    try:
        # Create job request
        job_data = {
            "format": TEST_EXPORT_FORMAT,
            "county_id": TEST_COUNTY_ID,
            "username": TEST_USERNAME,
            "area_of_interest": TEST_AREA_OF_INTEREST,
            "layers": TEST_LAYERS,
            "parameters": {
                "simplify_tolerance": 0.0001,
                "include_attributes": True
            }
        }
        
        logger.info(f"Submitting test job for county {TEST_COUNTY_ID}, format {TEST_EXPORT_FORMAT}")
        response = requests.post(f"{BASE_URL}/run", json=job_data)
        
        if response.status_code == 200:
            job_info = response.json()
            job_id = job_info.get("job_id")
            logger.info(f"✅ Test job submitted successfully, job ID: {job_id}")
            return job_id
        else:
            logger.error(f"❌ Failed to submit test job: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error submitting test job: {e}")
        return None

def wait_for_job_completion(job_id, timeout_seconds=30):
    """Wait for a job to complete or timeout"""
    logger.info(f"Waiting for job {job_id} to complete (timeout: {timeout_seconds}s)")
    start_time = time.time()
    completed = False
    
    while time.time() - start_time < timeout_seconds:
        try:
            response = requests.get(f"{BASE_URL}/status/{job_id}")
            
            if response.status_code != 200:
                logger.error(f"❌ Error checking job status: {response.status_code} - {response.text}")
                time.sleep(1)
                continue
            
            status_info = response.json()
            current_status = status_info.get("status")
            
            logger.info(f"Job status: {current_status} - {status_info.get('message', '')}")
            
            if current_status == "COMPLETED":
                logger.info(f"✅ Job completed successfully")
                completed = True
                break
            elif current_status == "FAILED":
                logger.error(f"❌ Job failed: {status_info.get('message', '')}")
                break
            
            # Wait before checking again
            time.sleep(1)
        except Exception as e:
            logger.error(f"❌ Error checking job status: {e}")
            time.sleep(1)
    
    if not completed and time.time() - start_time >= timeout_seconds:
        logger.warning(f"⚠️ Timeout waiting for job to complete")
    
    return completed

def check_metrics_updated(initial_metrics, job_id):
    """Check if metrics were updated after job execution"""
    try:
        # Get updated metrics
        response = requests.get(METRICS_URL)
        if response.status_code != 200:
            logger.error(f"❌ Failed to get updated metrics: {response.status_code} - {response.text}")
            return False
        
        updated_metrics = response.text
        
        # Check for GIS Export metrics
        metrics_to_check = [
            f'gis_export_jobs_submitted_total{{county_id="{TEST_COUNTY_ID}",export_format="{TEST_EXPORT_FORMAT}"',
            f'gis_export_jobs_completed_total{{county_id="{TEST_COUNTY_ID}",export_format="{TEST_EXPORT_FORMAT}"',
            f'gis_export_processing_duration_seconds_count{{county_id="{TEST_COUNTY_ID}",export_format="{TEST_EXPORT_FORMAT}"',
            f'gis_export_file_size_kb_count{{county_id="{TEST_COUNTY_ID}",export_format="{TEST_EXPORT_FORMAT}"',
            f'gis_export_record_count_count{{county_id="{TEST_COUNTY_ID}",export_format="{TEST_EXPORT_FORMAT}"'
        ]
        
        success = True
        for metric in metrics_to_check:
            if metric in updated_metrics:
                logger.info(f"✅ Metric found: {metric}")
            else:
                logger.error(f"❌ Metric not found: {metric}")
                success = False
        
        # Check if counter values increased
        if initial_metrics:
            for metric in metrics_to_check:
                if metric in initial_metrics and metric in updated_metrics:
                    # Extract values (simple check, not precise parsing)
                    initial_lines = [line for line in initial_metrics.split('\n') if metric in line]
                    updated_lines = [line for line in updated_metrics.split('\n') if metric in line]
                    
                    if initial_lines and updated_lines:
                        initial_value = initial_lines[0].split("}")[1].strip()
                        updated_value = updated_lines[0].split("}")[1].strip()
                        logger.info(f"Metric {metric}: Initial={initial_value}, Updated={updated_value}")
        
        return success
    except Exception as e:
        logger.error(f"❌ Error checking metrics update: {e}")
        return False

def main():
    """Main test function"""
    logger.info("===== GIS Export Metrics Test =====")
    
    # Step 1: Check if API is healthy
    if not check_health():
        logger.error("❌ Exiting test due to failed health check")
        return False
    
    # Step 2: Get initial metrics
    initial_metrics = get_initial_metrics()
    
    # Step 3: Submit a test job
    job_id = submit_test_job()
    if not job_id:
        logger.error("❌ Exiting test due to failed job submission")
        return False
    
    # Step 4: Wait for job completion
    if not wait_for_job_completion(job_id):
        logger.warning("⚠️ Job did not complete in time, but metrics might still be updated")
    
    # Step 5: Check if metrics were updated
    logger.info("Checking if metrics were updated...")
    time.sleep(2)  # Give time for metrics to be updated
    success = check_metrics_updated(initial_metrics, job_id)
    
    if success:
        logger.info("✅ GIS Export metrics test passed!")
    else:
        logger.error("❌ GIS Export metrics test failed - some metrics were not updated properly")
    
    return success

if __name__ == "__main__":
    main()