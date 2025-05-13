#!/usr/bin/env python
"""
Test script for GIS Export API

This script tests the GIS Export API by submitting jobs and checking their status.
"""

import requests
import json
import logging
import time
import sys
import uuid
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# API settings
API_BASE_URL = "http://localhost:8083/plugins/v1/gis-export"
TEST_TIMEOUT = 30  # seconds

def test_health():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"http://localhost:8083/")
        response.raise_for_status()
        logger.info(f"Health check successful: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False

def test_metrics():
    """Test the metrics endpoint."""
    try:
        response = requests.get(f"http://localhost:8083/metrics")
        response.raise_for_status()
        logger.info(f"Metrics endpoint successful, content length: {len(response.text)}")
        return True
    except Exception as e:
        logger.error(f"Metrics endpoint failed: {e}")
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
        
        response = requests.post(f"{API_BASE_URL}/run", json=job_data)
        response.raise_for_status()
        
        job_response = response.json()
        job_id = job_response.get("job_id")
        
        if not job_id:
            logger.error("No job_id in response")
            return None
        
        logger.info(f"Submitted test job with ID: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Job submission failed: {e}")
        return None

def check_job_status(job_id):
    """Check the status of a job."""
    try:
        response = requests.get(f"{API_BASE_URL}/status/{job_id}")
        response.raise_for_status()
        
        status_data = response.json()
        status = status_data.get("status")
        
        logger.info(f"Job {job_id} status: {status} - {status_data.get('message')}")
        return status
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return None

def cancel_job(job_id):
    """Cancel a job."""
    try:
        response = requests.post(f"{API_BASE_URL}/cancel/{job_id}")
        response.raise_for_status()
        
        result = response.json()
        status = result.get("status")
        
        logger.info(f"Cancelled job {job_id} - new status: {status}")
        return True
    except Exception as e:
        logger.error(f"Cancel request failed: {e}")
        return False

def get_all_jobs():
    """List all jobs."""
    try:
        response = requests.get(f"{API_BASE_URL}/list")
        response.raise_for_status()
        
        jobs = response.json()
        logger.info(f"Found {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"List jobs failed: {e}")
        return []

def run_test_suite():
    """Run all tests."""
    tests_passed = True
    
    # Test 1: Health check
    logger.info("TEST 1: Health check")
    if not test_health():
        tests_passed = False
        logger.error("Health check test FAILED")
    else:
        logger.info("Health check test PASSED")
    
    # Test 2: Metrics
    logger.info("TEST 2: Metrics endpoint")
    if not test_metrics():
        tests_passed = False
        logger.error("Metrics test FAILED")
    else:
        logger.info("Metrics test PASSED")
    
    # Test 3: Submit a job
    logger.info("TEST 3: Job submission")
    job_id = submit_test_job()
    if not job_id:
        tests_passed = False
        logger.error("Job submission test FAILED")
    else:
        logger.info("Job submission test PASSED")
    
    # Test 4: Check job status
    if job_id:
        logger.info("TEST 4: Job status check")
        status = check_job_status(job_id)
        if status is None:
            tests_passed = False
            logger.error("Job status check test FAILED")
        else:
            logger.info("Job status check test PASSED")
    
    # Test 5: Cancel the job
    if job_id:
        logger.info("TEST 5: Job cancellation")
        if not cancel_job(job_id):
            tests_passed = False
            logger.error("Job cancellation test FAILED")
        else:
            logger.info("Job cancellation test PASSED")
    
    # Test 6: List all jobs
    logger.info("TEST 6: Job listing")
    jobs = get_all_jobs()
    if jobs is None:
        tests_passed = False
        logger.error("Job listing test FAILED")
    else:
        logger.info("Job listing test PASSED")
    
    # Print summary
    if tests_passed:
        logger.info("All tests PASSED! GIS Export API is working correctly.")
    else:
        logger.error("Some tests FAILED! Check the logs for details.")
    
    return tests_passed

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)