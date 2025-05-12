#!/usr/bin/env python3
"""
Test script for Market Analysis Plugin

This script demonstrates how to use the Market Analysis plugin
by sending requests to the plugin's endpoints.
"""

import asyncio
import json
import uuid
import httpx
import datetime
from typing import Dict, Any, Optional

# API base URL
API_BASE_URL = "http://localhost:8080"
MARKET_ANALYSIS_ENDPOINT = f"{API_BASE_URL}/plugins/v1/market-analysis"

# Test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_ANALYSIS_TYPES = [
    "price_trend_by_zip",
    "comparable_market_area",
    "sales_velocity",
    "market_valuation",
    "price_per_sqft"
]
TEST_PARAMETERS = {
    "price_trend_by_zip": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "zip_codes": ["90210", "90211"],
        "property_types": ["residential"]
    },
    "comparable_market_area": {
        "reference_zip": "90210",
        "max_distance_miles": 25,
        "property_types": ["residential", "commercial"]
    },
    "sales_velocity": {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "area_codes": ["90210", "90211", "90212"]
    },
    "market_valuation": {
        "area_code": "90210",
        "property_type": "residential",
        "min_sqft": 1000,
        "max_sqft": 3000
    },
    "price_per_sqft": {
        "area_codes": ["90210", "90211"],
        "property_types": ["residential", "commercial"],
        "start_date": "2024-01-01",
        "end_date": "2024-12-31"
    }
}

# Test request functions
async def submit_market_analysis_job(
    analysis_type: str, 
    county_id: str,
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Submit a market analysis job."""
    print(f"\n----- Submitting {analysis_type} Market Analysis Job -----")
    
    url = f"{MARKET_ANALYSIS_ENDPOINT}/run"
    payload = {
        "analysis_type": analysis_type,
        "county_id": county_id,
        "parameters": parameters
    }
    
    print(f"Request: POST {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload)
        
    print(f"Response status: {response.status_code}")
    if response.status_code == 202:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return {}

async def get_job_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a market analysis job."""
    print(f"\n----- Checking Status for Job {job_id} -----")
    
    url = f"{MARKET_ANALYSIS_ENDPOINT}/status/{job_id}"
    print(f"Request: GET {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return {}

async def get_job_results(job_id: str) -> Dict[str, Any]:
    """Get the results of a market analysis job."""
    print(f"\n----- Getting Results for Job {job_id} -----")
    
    url = f"{MARKET_ANALYSIS_ENDPOINT}/results/{job_id}"
    print(f"Request: GET {url}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return {}

async def list_jobs(
    county_id: Optional[str] = None,
    analysis_type: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """List market analysis jobs with optional filtering."""
    print("\n----- Listing Market Analysis Jobs -----")
    
    params = {}
    if county_id:
        params["county_id"] = county_id
    if analysis_type:
        params["analysis_type"] = analysis_type
    if status:
        params["status"] = status
        
    url = f"{MARKET_ANALYSIS_ENDPOINT}/list"
    print(f"Request: GET {url}")
    print(f"Params: {params}")
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response body: {json.dumps(response.json(), indent=2)}")
        return response.json()
    else:
        print(f"Error: {response.text}")
        return {}

async def run_test_sequence():
    """Run a test sequence for the market analysis plugin."""
    # Submit a job for each analysis type
    job_ids = []
    for analysis_type in TEST_ANALYSIS_TYPES:
        if analysis_type in TEST_PARAMETERS:
            job_response = await submit_market_analysis_job(
                analysis_type=analysis_type,
                county_id=TEST_COUNTY_ID,
                parameters=TEST_PARAMETERS[analysis_type]
            )
            if job_response and "job_id" in job_response:
                job_ids.append((job_response["job_id"], analysis_type))
                
                # Check the job status immediately
                await get_job_status(job_response["job_id"])
                
                # Wait a moment (in a real test, this would wait for job completion)
                await asyncio.sleep(1)
    
    # List all jobs
    await list_jobs()
    
    # List jobs for specific county
    await list_jobs(county_id=TEST_COUNTY_ID)
    
    # List jobs for specific analysis type
    if job_ids:
        await list_jobs(analysis_type=job_ids[0][1])
    
    # Try to get results for the first job (might not be completed yet in a real test)
    if job_ids:
        await get_job_results(job_ids[0][0])

# Main execution
if __name__ == "__main__":
    print("\n=== Market Analysis Plugin Test ===")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Testing with County ID: {TEST_COUNTY_ID}")
    print(f"Testing analysis types: {', '.join(TEST_ANALYSIS_TYPES)}")
    
    asyncio.run(run_test_sequence())
    
    print("\n=== Test Complete ===")