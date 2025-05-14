#!/usr/bin/env python3
"""
Simple test for the GIS Export plugin job creation.
"""

import requests
import sys
import json
import time

def test_create_gis_export_job(host="localhost"):
    """Test creating a new GIS export job."""
    base_url = f"http://{host}:8080/plugins/v1/gis-export"
    
    # Create a new job
    job_data = {
        "username": "test_user",
        "format": "shapefile",
        "properties": ["address", "value", "owner"],
        "query_filters": {"county": "Montgomery"},
        "metadata": {"test_run": True, "priority": "normal"}
    }
    
    try:
        print("Submitting job creation request...")
        response = requests.post(f"{base_url}/jobs", json=job_data, timeout=10)
        print(f"Job creation status code: {response.status_code}")
        print(f"Job creation response: {response.text}")
        
        if response.status_code == 200:
            job_response = response.json()
            job_id = job_response["job_id"]
            print(f"✅ Created GIS export job: {job_id}")
            return job_id
        else:
            print(f"❌ Failed to create job: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error creating job: {str(e)}")
        return None

if __name__ == "__main__":
    host = "localhost"
    if len(sys.argv) > 1:
        host = sys.argv[1]
    
    job_id = test_create_gis_export_job(host)
    if job_id:
        print(f"Successfully created job with ID: {job_id}")
    else:
        print("Failed to create job")