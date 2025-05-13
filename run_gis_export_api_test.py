#!/usr/bin/env python
"""
GIS Export API Test

This script runs the GIS Export API in a single process and tests its functionality.
This is designed to be run from the command line when testing the GIS Export plugin.
"""

import asyncio
import os
import time
import json
import logging
import sys
import uuid
import requests
from datetime import datetime
from multiprocessing import Process

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Set environment variable for custom registry
os.environ["GIS_EXPORT_USE_CUSTOM_REGISTRY"] = "1"

# Constants
API_PORT = 8083
API_HOST = "localhost"
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"
PLUGIN_BASE_URL = f"{API_BASE_URL}/plugins/v1/gis-export"
SERVER_STARTUP_WAIT = 5  # seconds
TEST_TIMEOUT = 60  # seconds


def run_api_server():
    """Run the GIS Export API server in a subprocess."""
    try:
        import uvicorn
        from simplified_gis_export_api import app
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=API_PORT,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)


def test_health():
    """Test the health check endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        logger.info(f"Health check successful: {response.json()}")
        return True
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


def test_metrics():
    """Test the metrics endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/metrics")
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
        
        response = requests.post(f"{PLUGIN_BASE_URL}/run", json=job_data)
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
        response = requests.get(f"{PLUGIN_BASE_URL}/status/{job_id}")
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
        response = requests.post(f"{PLUGIN_BASE_URL}/cancel/{job_id}")
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
        response = requests.get(f"{PLUGIN_BASE_URL}/list")
        response.raise_for_status()
        
        jobs = response.json()
        logger.info(f"Found {len(jobs)} jobs")
        return jobs
    except Exception as e:
        logger.error(f"List jobs failed: {e}")
        return []


def run_tests():
    """Run all tests."""
    tests_passed = True
    
    # Test 1: Health check
    logger.info("TEST 1: Health check")
    if not test_health():
        tests_passed = False
        logger.error("Health check test FAILED")
    else:
        logger.info("Health check test PASSED")
    
    # Test 2: Metrics endpoint
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


def wait_for_server():
    """Wait for the server to be ready."""
    start_time = time.time()
    logger.info(f"Waiting for server to start (max {SERVER_STARTUP_WAIT} seconds)...")
    
    while time.time() - start_time < SERVER_STARTUP_WAIT:
        try:
            response = requests.get(f"{API_BASE_URL}/")
            if response.status_code == 200:
                logger.info("Server is ready!")
                return True
        except:
            pass
        
        time.sleep(0.5)
    
    logger.error("Server failed to start in time")
    return False


def main():
    """Main entry point."""
    try:
        # Start the API server in a separate process
        logger.info("Starting GIS Export API server...")
        server_process = Process(target=run_api_server)
        server_process.start()
        
        # Wait for the server to be ready
        if not wait_for_server():
            logger.error("Exiting because server failed to start")
            server_process.terminate()
            return 1
        
        # Run the tests
        logger.info("Starting tests...")
        tests_passed = run_tests()
        
        # Clean up
        logger.info("Tests complete, shutting down server...")
        server_process.terminate()
        server_process.join(timeout=5)
        
        return 0 if tests_passed else 1
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        return 1
    finally:
        # Ensure the server process is terminated
        if 'server_process' in locals() and server_process.is_alive():
            server_process.terminate()


if __name__ == "__main__":
    sys.exit(main())