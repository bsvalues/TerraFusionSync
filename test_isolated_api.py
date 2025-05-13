#!/usr/bin/env python
"""
Test Script for Isolated GIS Export API

This script sends test requests to the isolated GIS Export API.
"""

import requests
import json
import logging
import time
import sys
import uuid
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# API settings
API_BASE_URL = "http://localhost:8083"
GIS_EXPORT_URL = f"{API_BASE_URL}/gis-export"
TEST_TIMEOUT = 30  # seconds

def test_health():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{GIS_EXPORT_URL}/health")
        response.raise_for_status()
        logger.info(f"Health check successful: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def submit_test_job():
    """Submit a test job to the GIS Export API."""
    try:
        # Create a test job
        job_data = {
            "export_format": "GeoJSON",
            "county_id": "TEST_COUNTY",
            "area_of_interest": {
                "type": "bbox",
                "coordinates": [-120.5, 46.0, -120.0, 46.5]
            },
            "layers": ["parcels", "zoning"],
            "parameters": {
                "include_assessment_data": True,
                "simplify_geometries": True
            }
        }
        
        response = requests.post(f"{GIS_EXPORT_URL}/run", json=job_data)
        response.raise_for_status()
        
        job_response = response.json()
        job_id = job_response.get("job_id")
        
        if not job_id:
            logger.error("No job_id in response")
            return None
        
        logger.info(f"Submitted test job with ID: {job_id}")
        print(json.dumps(job_response, indent=2))
        return job_id
    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        return None

def check_job_status(job_id):
    """Check the status of a job."""
    try:
        response = requests.get(f"{GIS_EXPORT_URL}/status/{job_id}")
        response.raise_for_status()
        
        status_data = response.json()
        status = status_data.get("status")
        
        logger.info(f"Job {job_id} status: {status} - {status_data.get('message')}")
        print(json.dumps(status_data, indent=2))
        return status
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return None

def cancel_job(job_id):
    """Cancel a job."""
    try:
        response = requests.post(f"{GIS_EXPORT_URL}/cancel/{job_id}")
        response.raise_for_status()
        
        result = response.json()
        status = result.get("status")
        
        logger.info(f"Cancelled job {job_id} - new status: {status}")
        print(json.dumps(result, indent=2))
        return True
    except Exception as e:
        logger.error(f"Cancel request failed: {e}")
        return False

def get_all_jobs():
    """List all jobs."""
    try:
        response = requests.get(f"{GIS_EXPORT_URL}/list")
        response.raise_for_status()
        
        jobs = response.json()
        logger.info(f"Found {len(jobs)} jobs")
        print(json.dumps(jobs, indent=2))
        return jobs
    except Exception as e:
        logger.error(f"List jobs failed: {e}")
        return []

def run_tests():
    """Run all tests."""
    logger.info("Running tests against isolated GIS Export API")
    
    # Test 1: Health check
    logger.info("TEST 1: Health check")
    if not test_health():
        logger.error("Health check test FAILED")
        return False
    
    # Test 2: Submit a job
    logger.info("TEST 2: Job submission")
    job_id = submit_test_job()
    if not job_id:
        logger.error("Job submission test FAILED")
        return False
    
    # Wait for job to process
    time.sleep(1)
    
    # Test 3: Check job status
    logger.info("TEST 3: Job status check")
    status = check_job_status(job_id)
    if not status:
        logger.error("Job status check test FAILED")
        return False
    
    # If job is still pending or running, wait a bit
    if status in ["PENDING", "RUNNING"]:
        logger.info("Waiting for job to complete...")
        time.sleep(3)
        status = check_job_status(job_id)
    
    # Test 4: List all jobs
    logger.info("TEST 4: Job listing")
    jobs = get_all_jobs()
    if not jobs:
        logger.error("Job listing test FAILED")
        return False
    
    # Test 5: Submit another job for cancellation
    logger.info("TEST 5: Submitting job for cancellation")
    job_id_to_cancel = submit_test_job()
    if not job_id_to_cancel:
        logger.error("Job submission for cancellation test FAILED")
        return False
    
    # Test 6: Cancel the job
    logger.info("TEST 6: Job cancellation")
    if not cancel_job(job_id_to_cancel):
        logger.error("Job cancellation test FAILED")
        return False
    
    # Final check of all jobs
    logger.info("Final job listing after all tests:")
    get_all_jobs()
    
    logger.info("All tests completed successfully!")
    return True

if __name__ == "__main__":
    # This script assumes the API is already running
    logger.info("Starting tests against the isolated GIS Export API")
    success = run_tests()
    sys.exit(0 if success else 1)