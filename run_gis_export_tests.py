#!/usr/bin/env python
"""
TerraFusion - GIS Export API Test Script

This script runs basic integration tests against the GIS Export API.
It sends requests to create, monitor, and retrieve export jobs.

Usage:
    python run_gis_export_tests.py

Requirements:
    - The GIS Export API must be running (via simplified_gis_export_api.py or full SyncService)
"""

import requests
import json
import time
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# API test configuration
DEFAULT_API_BASE_URL = "http://localhost:8083/plugins/v1/gis-export"
DEFAULT_TIMEOUT = 10  # seconds
MAX_JOB_WAIT_TIME = 60  # seconds

class GisExportApiTest:
    """Test suite for GIS Export API endpoints."""
    
    def __init__(self, base_url: str = DEFAULT_API_BASE_URL):
        """Initialize with API base URL."""
        self.base_url = base_url
        self.job_id = None
        self.test_county_id = "TEST_COUNTY_123"
        
    def run_all_tests(self) -> bool:
        """Run all GIS Export API tests in sequence."""
        try:
            logger.info("Starting GIS Export API test suite")
            
            # Test health endpoint
            self.test_health_check()
            
            # Test job submission
            job_id = self.test_submit_export_job()
            if not job_id:
                logger.error("Failed to get job_id from submission test")
                return False
            
            # Test job status retrieval
            self.test_get_job_status(job_id)
            
            # Wait for job to complete
            if not self.wait_for_job_completion(job_id):
                logger.error("Job did not complete within expected time")
                return False
            
            # Test results retrieval
            self.test_get_job_results(job_id)
            
            # Test job listing
            self.test_list_jobs()
            
            logger.info("All GIS Export API tests completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Test suite failed with exception: {e}", exc_info=True)
            return False
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=DEFAULT_TIMEOUT)
            response.raise_for_status()
            logger.info(f"Health check successful: {response.json()}")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def test_submit_export_job(self) -> Optional[str]:
        """Test job submission and return job_id if successful."""
        request_data = {
            "export_format": "GeoJSON",
            "county_id": self.test_county_id,
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
        
        try:
            response = requests.post(
                f"{self.base_url}/run",
                json=request_data,
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            job_id = result.get("job_id")
            
            assert job_id is not None, "Response missing job_id"
            assert result.get("status") == "PENDING", "Unexpected job status"
            
            logger.info(f"Job submission successful. Job ID: {job_id}")
            return job_id
        except Exception as e:
            logger.error(f"Job submission failed: {e}")
            return None
    
    def test_get_job_status(self, job_id: str) -> bool:
        """Test job status retrieval."""
        try:
            response = requests.get(
                f"{self.base_url}/status/{job_id}",
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            assert result.get("job_id") == job_id, "Job ID mismatch in response"
            
            status = result.get("status")
            logger.info(f"Retrieved job status: {status} for job ID: {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to get job status: {e}")
            return False
    
    def wait_for_job_completion(self, job_id: str) -> bool:
        """Poll until job completes or timeout occurs."""
        start_time = time.time()
        logger.info(f"Waiting for job {job_id} to complete...")
        
        while (time.time() - start_time) < MAX_JOB_WAIT_TIME:
            try:
                response = requests.get(
                    f"{self.base_url}/status/{job_id}",
                    timeout=DEFAULT_TIMEOUT
                )
                response.raise_for_status()
                result = response.json()
                
                status = result.get("status")
                logger.info(f"Current job status: {status}")
                
                if status == "COMPLETED":
                    logger.info(f"Job completed successfully in {time.time() - start_time:.2f} seconds")
                    return True
                elif status == "FAILED":
                    logger.error(f"Job failed: {result.get('message')}")
                    return False
                
                # Wait before polling again
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error checking job status: {e}")
                time.sleep(5)  # Longer wait after error
        
        logger.error(f"Job did not complete within {MAX_JOB_WAIT_TIME} seconds")
        return False
    
    def test_get_job_results(self, job_id: str) -> bool:
        """Test job results retrieval."""
        try:
            response = requests.get(
                f"{self.base_url}/results/{job_id}",
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            assert result.get("job_id") == job_id, "Job ID mismatch in response"
            assert result.get("status") == "COMPLETED", "Job not completed"
            assert result.get("result") is not None, "Missing result data"
            
            file_location = result.get("result", {}).get("result_file_location")
            file_size = result.get("result", {}).get("result_file_size_kb")
            
            logger.info(f"Retrieved results for job {job_id}:")
            logger.info(f"  - File location: {file_location}")
            logger.info(f"  - File size: {file_size} KB")
            
            return True
        except Exception as e:
            logger.error(f"Failed to get job results: {e}")
            return False
    
    def test_list_jobs(self) -> bool:
        """Test job listing endpoint."""
        try:
            response = requests.get(
                f"{self.base_url}/list?county_id={self.test_county_id}",
                timeout=DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            jobs = response.json()
            
            assert isinstance(jobs, list), "Expected list response"
            
            logger.info(f"Listed {len(jobs)} jobs for county {self.test_county_id}")
            if jobs:
                logger.info(f"First job in list: {jobs[0]['job_id']} with status {jobs[0]['status']}")
            
            return True
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return False

if __name__ == "__main__":
    # Allow specifying different API URL from command line
    api_base_url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_API_BASE_URL
    
    # Run tests
    test_runner = GisExportApiTest(api_base_url)
    success = test_runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)