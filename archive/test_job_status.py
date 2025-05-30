#!/usr/bin/env python3
"""
Test for checking GIS Export job status.
"""

import requests
import sys
import json
import time

def test_gis_export_job_status(job_id, host="localhost"):
    """Test retrieving the status of a GIS export job."""
    base_url = f"http://{host}:8080/plugins/v1/gis-export"
    
    # Note that the parameter name is job_id_param, not job_id
    response = requests.get(f"{base_url}/status/{job_id}")
    print(f"Status check status code: {response.status_code}")
    print(f"Status check response: {response.text}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get job status: {response.status_code}")
        return False
    
    status_data = response.json()
    print(f"✅ Job status: {status_data['status']}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_job_status.py <job_id> [host]")
        sys.exit(1)
        
    job_id = sys.argv[1]
    host = "localhost"
    if len(sys.argv) > 2:
        host = sys.argv[2]
    
    test_gis_export_job_status(job_id, host)