#!/usr/bin/env python3
"""
Check the current status of the SyncService GIS Export plugin.
"""

import requests
import sys
import json

def main():
    base_url = "http://0.0.0.0:8080"
    
    # Check main health endpoint
    try:
        resp = requests.get(f"{base_url}/health")
        print(f"Main health: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error on main health check: {e}")
    
    # Check GIS Export health endpoint
    try:
        resp = requests.get(f"{base_url}/plugins/v1/gis-export/health")
        print(f"GIS Export health: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"Error on GIS Export health check: {e}")
    
    # Try to create a GIS Export job
    try:
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
            "layers": ["parcels", "buildings"],
            "parameters": {
                "include_attributes": True
            }
        }
        
        resp = requests.post(f"{base_url}/plugins/v1/gis-export/run", json=job_data)
        print(f"Create job: {resp.status_code} - {resp.text}")
        
        if resp.status_code == 202:
            job_id = resp.json()["job_id"]
            print(f"Created job ID: {job_id}")
            
            # Check job status
            status_resp = requests.get(f"{base_url}/plugins/v1/gis-export/status/{job_id}")
            print(f"Job status: {status_resp.status_code} - {status_resp.text}")
    except Exception as e:
        print(f"Error on job creation: {e}")
    
    # List existing jobs
    try:
        resp = requests.get(f"{base_url}/plugins/v1/gis-export/list")
        print(f"Job list: {resp.status_code}")
        if resp.status_code == 200:
            jobs = resp.json()
            print(f"Found {len(jobs)} jobs")
            for job in jobs[:5]:  # Show first 5 jobs
                print(f"Job {job['job_id']}: {job['status']}")
    except Exception as e:
        print(f"Error on job listing: {e}")

if __name__ == "__main__":
    main()