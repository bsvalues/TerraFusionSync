#!/usr/bin/env python3
"""
TerraFusion Sync API Test Script

This script tests the Sync Service API endpoints to verify functionality.
"""

import json
import requests
import sys

BASE_URL = "http://localhost:5000"

def test_list_jobs():
    """Test listing sync jobs"""
    print("Testing GET /api/v1/sync/jobs")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/sync/jobs")
        response.raise_for_status()
        jobs = response.json()
        print(f"Success! Found {len(jobs)} jobs")
        print(json.dumps(jobs, indent=2))
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_create_job():
    """Test creating a new sync job"""
    print("\nTesting POST /api/v1/sync/jobs")
    try:
        data = {
            "county_id": "king-wa",
            "username": "test-user@county.gov",
            "data_types": ["parcels", "zoning"],
            "source_system": "county-gis",
            "target_system": "terrafusion"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/sync/jobs",
            json=data
        )
        response.raise_for_status()
        job = response.json()
        print(f"Success! Created job with ID: {job['job_id']}")
        print(json.dumps(job, indent=2))
        return job['job_id']
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def test_get_job(job_id):
    """Test getting a specific job"""
    print(f"\nTesting GET /api/v1/sync/jobs/{job_id}")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/sync/jobs/{job_id}")
        response.raise_for_status()
        job = response.json()
        print(f"Success! Retrieved job {job_id}")
        print(json.dumps(job, indent=2))
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_get_report(job_id):
    """Test getting a job report"""
    print(f"\nTesting GET /api/v1/sync/jobs/{job_id}/report")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/sync/jobs/{job_id}/report")
        response.raise_for_status()
        report = response.json()
        print(f"Success! Retrieved report for job {job_id}")
        print(json.dumps(report, indent=2))
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("TerraFusion Sync API Test\n" + "-"*25)
    
    # Test listing jobs
    if not test_list_jobs():
        print("List jobs test failed. Aborting further tests.")
        sys.exit(1)
    
    # Test creating a job
    job_id = test_create_job()
    if not job_id:
        print("Create job test failed. Aborting further tests.")
        sys.exit(1)
    
    # Test getting a job
    if not test_get_job(job_id):
        print("Get job test failed. Aborting further tests.")
        sys.exit(1)
    
    # Test getting a report
    test_get_report(job_id)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()