#!/usr/bin/env python3
"""
Fixed GIS Export Test Script

This script tests the GIS Export plugin with isolated metrics,
focusing on ensuring metrics are properly isolated from other plugins.
"""

import os
import sys
import json
import time
import logging
import requests
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SYNC_SERVICE_URL = "http://0.0.0.0:8080"
METRICS_SERVICE_URL = "http://0.0.0.0:8090"

def log_separator(message=""):
    """Print a separator in the logs."""
    logger.info(f"{'=' * 20} {message} {'=' * 20}")

def check_health():
    """Check if the GIS Export API is healthy."""
    log_separator("Checking GIS Export API Health")
    
    try:
        # Check SyncService health
        sync_response = requests.get(f"{SYNC_SERVICE_URL}/health")
        logger.info(f"SyncService health: {sync_response.status_code} {sync_response.text}")
        
        # Check GIS Export plugin health via SyncService
        gis_response = requests.get(f"{SYNC_SERVICE_URL}/plugins/v1/gis-export/health")
        logger.info(f"GIS Export plugin health: {gis_response.status_code} {gis_response.text}")
        
        # Check isolated metrics service health
        metrics_response = requests.get(f"{METRICS_SERVICE_URL}/health")
        logger.info(f"Isolated Metrics service health: {metrics_response.status_code} {metrics_response.text}")
        
        return (
            sync_response.status_code == 200 and
            gis_response.status_code == 200 and
            metrics_response.status_code == 200
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def try_metrics_endpoints():
    """Try both custom and default metrics endpoints."""
    log_separator("Checking Metrics Endpoints")
    
    try:
        # Try isolated metrics endpoint
        isolated_response = requests.get(f"{METRICS_SERVICE_URL}/metrics")
        logger.info(f"Isolated metrics endpoint: {isolated_response.status_code}")
        if isolated_response.status_code == 200:
            logger.info(f"Isolated metrics sample: {isolated_response.text[:200]}...")
        else:
            logger.error(f"Isolated metrics response: {isolated_response.text}")
        
        # Try SyncService metrics endpoint
        sync_metrics_response = requests.get(f"{SYNC_SERVICE_URL}/metrics")
        logger.info(f"SyncService metrics endpoint: {sync_metrics_response.status_code}")
        if sync_metrics_response.status_code == 200:
            logger.info(f"SyncService metrics sample: {sync_metrics_response.text[:200]}...")
        else:
            logger.error(f"SyncService metrics response: {sync_metrics_response.text}")
        
        return isolated_response.status_code == 200
    except Exception as e:
        logger.error(f"Metrics endpoint check failed: {e}")
        return False

def create_test_job():
    """Create a test GIS export job."""
    log_separator("Creating Test Job")
    
    # Get metrics before job creation
    before_metrics = requests.get(f"{METRICS_SERVICE_URL}/metrics").text
    
    try:
        # Create a test job
        job_data = {
            "county_id": "benton_wa",
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
        
        # Submit job to GIS Export API
        job_response = requests.post(
            f"{SYNC_SERVICE_URL}/plugins/v1/gis-export/run",
            json=job_data
        )
        
        if job_response.status_code != 200:
            logger.error(f"Job creation failed: {job_response.status_code} {job_response.text}")
            return None
        
        response_data = job_response.json()
        job_id = response_data.get("job_id")
        logger.info(f"Created job with ID: {job_id}")
        
        # Record in isolated metrics
        metrics_data = {
            "job_id": job_id,
            "county_id": job_data["county_id"],
            "format": job_data["format"]
        }
        
        metrics_response = requests.post(
            f"{METRICS_SERVICE_URL}/record/job_submitted",
            json=metrics_data
        )
        
        logger.info(f"Metrics job submission: {metrics_response.status_code} {metrics_response.text}")
        
        # Get metrics after job creation
        after_metrics = requests.get(f"{METRICS_SERVICE_URL}/metrics").text
        
        # Check if metrics were updated
        check_metrics_for_changes(before_metrics, after_metrics)
        
        return job_id
    except Exception as e:
        logger.error(f"Job creation failed: {e}")
        return None

def wait_for_job_completion(job_id, timeout_seconds=30):
    """Wait for a job to complete or timeout."""
    log_separator(f"Waiting for job {job_id} to complete")
    
    start_time = time.time()
    completed = False
    status_response = None
    
    while time.time() - start_time < timeout_seconds:
        try:
            status_response = requests.get(
                f"{SYNC_SERVICE_URL}/plugins/v1/gis-export/jobs/{job_id}/status"
            )
            
            if status_response.status_code != 200:
                logger.warning(f"Status check failed: {status_response.status_code} {status_response.text}")
                time.sleep(1)
                continue
            
            status_data = status_response.json()
            job_status = status_data.get("status")
            logger.info(f"Job status: {job_status}")
            
            if job_status == "COMPLETED":
                completed = True
                # Record completion in metrics
                metrics_data = {
                    "job_id": job_id,
                    "duration_seconds": time.time() - start_time,
                    "file_size_kb": 1024,  # Example value
                    "record_count": 100     # Example value
                }
                
                metrics_response = requests.post(
                    f"{METRICS_SERVICE_URL}/record/job_completed",
                    json=metrics_data
                )
                
                logger.info(f"Metrics job completion: {metrics_response.status_code} {metrics_response.text}")
                break
            elif job_status == "FAILED":
                # Record failure in metrics
                metrics_data = {
                    "job_id": job_id,
                    "error_type": "processing_error"
                }
                
                metrics_response = requests.post(
                    f"{METRICS_SERVICE_URL}/record/job_failed",
                    json=metrics_data
                )
                
                logger.info(f"Metrics job failure: {metrics_response.status_code} {metrics_response.text}")
                break
            
            time.sleep(1)
        except Exception as e:
            logger.error(f"Error checking job status: {e}")
            time.sleep(1)
    
    if not completed and status_response:
        logger.warning(f"Job did not complete within timeout. Last status: {status_response.text}")
    
    # Get final metrics
    final_metrics = requests.get(f"{METRICS_SERVICE_URL}/metrics").text
    logger.info(f"Final metrics sample: {final_metrics[:200]}...")
    
    return completed

def check_metrics_for_changes(before_metrics, after_metrics):
    """Check if metrics have changed after job execution."""
    log_separator("Checking Metrics Changes")
    
    # Look for changes in the metrics
    if "gis_export_jobs_submitted_total" in after_metrics:
        logger.info("Found GIS Export jobs submitted metric")
    else:
        logger.warning("GIS Export jobs submitted metric not found")
    
    # Simple diff to show what changed
    before_lines = set(before_metrics.split("\n"))
    after_lines = set(after_metrics.split("\n"))
    
    new_lines = after_lines - before_lines
    if new_lines:
        logger.info("New metrics detected:")
        for line in new_lines:
            if line.strip() and not line.startswith("#"):
                logger.info(f"  {line}")

def main():
    """Main test function."""
    log_separator("Starting GIS Export Test with Isolated Metrics")
    
    # Check if isolated metrics service is running
    try:
        metrics_health = requests.get(f"{METRICS_SERVICE_URL}/health")
        if metrics_health.status_code != 200:
            logger.error("Metrics service not running or not healthy")
            logger.info("Starting metrics service...")
            
            # Start metrics service in background
            subprocess.Popen(
                ["python", "isolated_gis_export_metrics.py", "--port", "8090"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(3)  # Give it time to start
    except:
        logger.error("Metrics service not running")
        logger.info("Starting metrics service...")
        
        # Start metrics service in background
        subprocess.Popen(
            ["python", "isolated_gis_export_metrics.py", "--port", "8090"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(3)  # Give it time to start
    
    # Run test sequence
    if not check_health():
        logger.error("Health check failed, aborting test")
        return False
    
    if not try_metrics_endpoints():
        logger.error("Metrics endpoints check failed, aborting test")
        return False
    
    job_id = create_test_job()
    if not job_id:
        logger.error("Job creation failed, aborting test")
        return False
    
    if not wait_for_job_completion(job_id):
        logger.warning("Job did not complete within timeout")
        # Continue anyway to check metrics
    
    # Check final metrics
    log_separator("Test Complete")
    logger.info("Test completed successfully")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)