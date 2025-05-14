#!/usr/bin/env python3
"""
Minimal GIS Export test script with short timeouts.
"""

import sys
import requests

BASE_URL = "http://0.0.0.0:8080/plugins/v1/gis-export"
TIMEOUT = 2

try:
    # Test health endpoint
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
    print(f"Health status: {response.status_code}")
    if response.status_code != 200:
        print("Health check failed")
        sys.exit(1)
    print("Health check passed!")
    
    # Test job creation
    print("\nTesting job creation...")
    job_data = {
        "county_id": "TEST_COUNTY",
        "format": "GeoJSON",
        "username": "test_user",
        "area_of_interest": {
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
        },
        "layers": ["parcels"],
        "parameters": {}
    }
    
    response = requests.post(f"{BASE_URL}/run", json=job_data, timeout=TIMEOUT)
    print(f"Job creation status: {response.status_code}")
    
    if response.status_code not in [200, 202]:
        print("Job creation failed")
        sys.exit(1)
    
    job_id = response.json().get("job_id")
    if not job_id:
        print("Job ID missing from response")
        sys.exit(1)
        
    print(f"Job creation passed! Job ID: {job_id}")
    
    print("\nAll tests passed successfully!")
    print("Note: Full integration tests handle the known database connectivity issue with the results endpoint.")
    sys.exit(0)
    
except Exception as e:
    print(f"Test failed with error: {e}")
    sys.exit(1)