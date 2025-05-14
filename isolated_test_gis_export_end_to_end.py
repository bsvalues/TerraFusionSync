#!/usr/bin/env python3
"""
Isolated runner for GIS Export end-to-end tests.

This script isolates the GIS Export tests from other tests to avoid
metrics registration conflicts. It runs the integration tests for the 
GIS Export plugin without importing other plugin metrics.
"""

import os
import sys
import subprocess
import argparse
import asyncio
import json
import uuid
import time
import datetime
import pytest
import requests
from typing import Dict, Any, List, Optional

# Configure test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_EXPORT_FORMAT = "GeoJSON"
TEST_FAIL_FORMAT = "FAIL_FORMAT_SIM"  # Special format that simulates failure
TEST_AREA_OF_INTEREST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-122.48, 37.78],
            [-122.48, 37.80],
            [-122.46, 37.80],
            [-122.46, 37.78],
            [-122.48, 37.78]
        ]
    ]
}
TEST_LAYERS = ["parcels", "buildings", "zoning"]
TEST_PARAMETERS = {
    "include_attributes": True,
    "simplify_tolerance": 0.0001,
    "coordinate_system": "EPSG:4326"
}

# Base URL for the SyncService API
BASE_URL = "http://localhost:8080/plugins/v1/gis-export"

def test_create_gis_export_job():
    """Test creating a new GIS export job."""
    # Prepare request data
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": TEST_EXPORT_FORMAT,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to create a GIS export job
    response = requests.post(f"{BASE_URL}/run", json=export_data)
    
    # Check status code and response structure
    assert response.status_code == 202, f"Failed to create GIS export job: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert "job_id" in data
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["export_format"] == TEST_EXPORT_FORMAT
    assert data["status"] == "PENDING"
    assert "area_of_interest" in data["parameters"]
    assert "layers" in data["parameters"]
    
    print(f"✅ Created GIS export job: {data['job_id']}")
    return data["job_id"]

def test_get_gis_export_status(job_id):
    """Test retrieving the status of a GIS export job."""
    # Check status endpoint
    response = requests.get(f"{BASE_URL}/status/{job_id}")
    
    # Check status code and response
    assert response.status_code == 200, f"Failed to get status: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert data["job_id"] == job_id
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["export_format"] == TEST_EXPORT_FORMAT
    assert data["status"] in ["PENDING", "RUNNING", "COMPLETED"]
    
    # Wait a moment and check again to see if status changes
    time.sleep(2)  # Give time for background processing
    
    response = requests.get(f"{BASE_URL}/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Status should have progressed
    assert data["status"] in ["RUNNING", "COMPLETED"]
    print(f"✅ Verified GIS export job status: {data['status']}")
    return data["status"]

def test_complete_gis_export_workflow():
    """Test the complete workflow: submit -> check status -> get results."""
    # Create job
    job_id = test_create_gis_export_job()
    
    # Check status initially
    response = requests.get(f"{BASE_URL}/status/{job_id}")
    assert response.status_code == 200
    initial_status = response.json()["status"]
    assert initial_status in ["PENDING", "RUNNING"]
    
    # Wait for job to complete (with timeout)
    completed = False
    max_retries = 10
    retry_count = 0
    
    while not completed and retry_count < max_retries:
        time.sleep(1)  # Wait 1 second between checks
        response = requests.get(f"{BASE_URL}/status/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        
        if status_data["status"] == "COMPLETED":
            completed = True
        elif status_data["status"] == "FAILED":
            assert False, f"Job failed unexpectedly: {status_data['message']}"
            
        retry_count += 1
    
    assert completed, f"Job did not complete within {max_retries} seconds"
    
    # Get results
    response = requests.get(f"{BASE_URL}/results/{job_id}")
    assert response.status_code == 200
    results_data = response.json()
    
    # Verify result data
    assert results_data["job_id"] == job_id
    assert results_data["status"] == "COMPLETED"
    assert results_data["result"] is not None
    assert "result_file_location" in results_data["result"]
    assert "result_file_size_kb" in results_data["result"]
    assert "result_record_count" in results_data["result"]
    
    print(f"✅ Completed end-to-end workflow test. Results: {results_data['result']['result_file_location']}")
    return job_id

def test_failed_gis_export_job():
    """Test a GIS export job that is expected to fail."""
    # Prepare request data with special failure format
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": TEST_FAIL_FORMAT,  # Special format that triggers failure
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit job
    response = requests.post(f"{BASE_URL}/run", json=export_data)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    # Wait for job to fail (with timeout)
    failed = False
    max_retries = 10
    retry_count = 0
    
    while not failed and retry_count < max_retries:
        time.sleep(1)  # Wait 1 second between checks
        response = requests.get(f"{BASE_URL}/status/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        
        if status_data["status"] == "FAILED":
            failed = True
            
        retry_count += 1
    
    assert failed, f"Job did not fail within {max_retries} seconds"
    
    # Get results should return status with failure but no result data
    response = requests.get(f"{BASE_URL}/results/{job_id}")
    assert response.status_code == 200
    results_data = response.json()
    
    # Verify failure data
    assert results_data["job_id"] == job_id
    assert results_data["status"] == "FAILED"
    assert "Simulated failure" in results_data["message"]
    assert results_data["result"] is None
    
    print(f"✅ Verified failure handling with error: {results_data['message']}")

def test_cancel_gis_export_job():
    """Test cancelling a GIS export job."""
    # Create a job
    job_id = test_create_gis_export_job()
    
    # Cancel the job
    response = requests.post(f"{BASE_URL}/cancel/{job_id}")
    
    # Check status code and response
    assert response.status_code == 200, f"Failed to cancel job: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert data["job_id"] == job_id
    assert data["status"] == "FAILED"
    assert "cancelled" in data["message"].lower()
    
    print(f"✅ Successfully cancelled job: {job_id}")

def test_list_gis_export_jobs():
    """Test listing GIS export jobs with various filters."""
    # Create a few test jobs
    job_id1 = test_create_gis_export_job()
    
    # Create a job with different format for filtering tests
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": "KML",  # Different format
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    response = requests.post(f"{BASE_URL}/run", json=export_data)
    assert response.status_code == 202
    job_id2 = response.json()["job_id"]
    
    # Wait a moment for jobs to be processed
    time.sleep(2)
    
    # Test listing all jobs
    response = requests.get(f"{BASE_URL}/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Should have at least our 2 test jobs
    
    # Test filtering by county_id
    response = requests.get(f"{BASE_URL}/list?county_id={TEST_COUNTY_ID}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    
    # Test filtering by export_format
    response = requests.get(f"{BASE_URL}/list?export_format={TEST_EXPORT_FORMAT}")
    assert response.status_code == 200
    data = response.json()
    assert any(item["job_id"] == job_id1 for item in data)
    assert not any(item["job_id"] == job_id2 for item in data)  # job_id2 is KML
    
    print(f"✅ Successfully tested list filtering with {len(data)} matching jobs")

def test_gis_export_plugin_health():
    """Test the GIS Export plugin health check endpoint."""
    response = requests.get(f"{BASE_URL}/health")
    
    # Check status code and response
    assert response.status_code == 200
    data = response.json()
    
    # Verify health data
    assert data["status"] == "healthy"
    assert data["plugin"] == "gis_export"
    assert "version" in data
    assert "timestamp" in data
    
    print(f"✅ Health check passed. Plugin version: {data['version']}")

def run_all_tests():
    """Run all tests in sequence."""
    print("Starting GIS Export end-to-end tests...")
    
    try:
        # Test health first to ensure service is up
        test_gis_export_plugin_health()
        
        # Run basic workflow test
        test_complete_gis_export_workflow()
        
        # Test failure case
        test_failed_gis_export_job()
        
        # Test cancellation
        test_cancel_gis_export_job()
        
        # Test listing and filtering
        test_list_gis_export_jobs()
        
        print("\n✅ All GIS Export tests completed successfully!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    # Check if the SyncService is running
    try:
        response = requests.get("http://localhost:8080/health")
        if response.status_code != 200:
            print("⚠️ SyncService doesn't appear to be healthy. Tests may fail.")
    except requests.exceptions.ConnectionError:
        print("⚠️ Cannot connect to SyncService at http://localhost:8080. Is it running?")
        sys.exit(1)
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Run GIS Export end-to-end tests")
    parser.add_argument("--host", default="localhost", help="Host where the SyncService is running")
    parser.add_argument("--port", default=8080, type=int, help="Port where the SyncService is running")
    args = parser.parse_args()
    
    # Update base URL if needed
    BASE_URL = f"http://{args.host}:{args.port}/plugins/v1/gis_export"
    
    # Run the tests
    sys.exit(run_all_tests())