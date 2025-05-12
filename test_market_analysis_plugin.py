"""
Test Market Analysis Plugin Integration

This script tests the Market Analysis plugin for TerraFusion SyncService.
It verifies basic functionality like job creation, status querying, and result retrieval.
"""

import os
import sys
import json
import time
import asyncio
import logging
import argparse
import httpx
from typing import Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')
logger = logging.getLogger("market_analysis_test")

# Constants
DEFAULT_BASE_URL = "http://localhost:8080"
DEFAULT_COUNTY_ID = "test_county_001"
TIMEOUT = 30  # Seconds to wait for job completion


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Market Analysis Plugin Integration")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Base URL for SyncService API")
    parser.add_argument("--county-id", default=DEFAULT_COUNTY_ID, help="County ID to use for test jobs")
    parser.add_argument("--timeout", type=int, default=TIMEOUT, help="Timeout in seconds for waiting for job completion")
    parser.add_argument("--test-health-only", action="store_true", help="Only test the health endpoint")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    return parser.parse_args()


async def check_health(client: httpx.AsyncClient, base_url: str) -> bool:
    """Check if the health endpoint is responding."""
    try:
        url = f"{base_url}/plugins/market-analysis/health"
        logger.info(f"Checking health at {url}")
        
        response = await client.get(url, timeout=5.0)
        
        if response.status_code == 200:
            logger.info(f"Health check successful: {response.json()}")
            return True
        else:
            logger.error(f"Health check failed with status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return False


async def run_analysis_job(
    client: httpx.AsyncClient, 
    base_url: str, 
    county_id: str, 
    analysis_type: str, 
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Run a market analysis job and return the job ID."""
    try:
        url = f"{base_url}/plugins/market-analysis/run"
        payload = {
            "county_id": county_id,
            "analysis_type": analysis_type,
            "parameters": parameters
        }
        
        logger.info(f"Starting {analysis_type} job with parameters: {parameters}")
        response = await client.post(url, json=payload, timeout=10.0)
        
        if response.status_code == 202:
            result = response.json()
            logger.info(f"Job created successfully with ID: {result.get('job_id')}")
            return result
        else:
            logger.error(f"Failed to create job: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error creating job: {str(e)}")
        return {}


async def check_job_status(client: httpx.AsyncClient, base_url: str, job_id: str) -> Dict[str, Any]:
    """Check the status of a market analysis job."""
    try:
        url = f"{base_url}/plugins/market-analysis/status/{job_id}"
        response = await client.get(url, timeout=5.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get job status: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
        return {}


async def get_job_results(client: httpx.AsyncClient, base_url: str, job_id: str) -> Dict[str, Any]:
    """Get the results of a completed market analysis job."""
    try:
        url = f"{base_url}/plugins/market-analysis/results/{job_id}"
        response = await client.get(url, timeout=5.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to get job results: {response.status_code} - {response.text}")
            return {}
    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}")
        return {}


async def list_jobs(client: httpx.AsyncClient, base_url: str, county_id: str = None) -> Dict[str, Any]:
    """List market analysis jobs."""
    try:
        url = f"{base_url}/plugins/market-analysis/list"
        params = {}
        if county_id:
            params["county_id"] = county_id
            
        response = await client.get(url, params=params, timeout=5.0)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Failed to list jobs: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return []


async def wait_for_job_completion(
    client: httpx.AsyncClient, 
    base_url: str, 
    job_id: str, 
    timeout: int = TIMEOUT
) -> Dict[str, Any]:
    """
    Wait for a job to complete, polling every second up to the timeout.
    
    Returns the final job status, or an empty dict if timeout is reached.
    """
    logger.info(f"Waiting for job {job_id} to complete (timeout: {timeout}s)")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = await check_job_status(client, base_url, job_id)
        
        if not status:
            # Error getting status
            await asyncio.sleep(1)
            continue
            
        current_status = status.get("status")
        logger.info(f"Current status: {current_status} - {status.get('message', '')}")
        
        if current_status in ["COMPLETED", "FAILED", "CANCELLED"]:
            logger.info(f"Job reached terminal state: {current_status}")
            return status
            
        # Wait before next check
        await asyncio.sleep(1)
    
    logger.error(f"Timeout waiting for job {job_id} to complete")
    return {}


async def test_price_trend_analysis(client: httpx.AsyncClient, base_url: str, county_id: str, timeout: int) -> bool:
    """Test the price trend analysis functionality."""
    
    # Create job parameters
    parameters = {
        "zip_code": "90210",
        "date_from": (datetime.now().replace(year=datetime.now().year - 1)).isoformat(),
        "date_to": datetime.now().isoformat(),
        "property_type": "residential"
    }
    
    # Run the job
    job = await run_analysis_job(client, base_url, county_id, "price_trend_by_zip", parameters)
    
    if not job:
        return False
        
    job_id = job.get("job_id")
    if not job_id:
        logger.error("No job ID returned")
        return False
        
    # Wait for job completion
    final_status = await wait_for_job_completion(client, base_url, job_id, timeout)
    
    if not final_status:
        return False
        
    # Check if job completed successfully
    if final_status.get("status") != "COMPLETED":
        logger.error(f"Job did not complete successfully: {final_status}")
        return False
    
    # Get results
    results = await get_job_results(client, base_url, job_id)
    
    if not results:
        logger.error("Failed to get job results")
        return False
        
    # Validate results structure
    result_data = results.get("result", {})
    trends = result_data.get("trends", [])
    
    if not trends:
        logger.error("No trend data in results")
        return False
        
    logger.info(f"Price trend analysis successful with {len(trends)} data points")
    return True


async def test_comparable_market_area(client: httpx.AsyncClient, base_url: str, county_id: str, timeout: int) -> bool:
    """Test the comparable market area functionality."""
    
    # Create job parameters
    parameters = {
        "zip_code": "90210",
        "radius_miles": 25,
        "min_similar_listings": 5
    }
    
    # Run the job
    job = await run_analysis_job(client, base_url, county_id, "comparable_market_area", parameters)
    
    if not job:
        return False
        
    job_id = job.get("job_id")
    if not job_id:
        logger.error("No job ID returned")
        return False
        
    # Wait for job completion
    final_status = await wait_for_job_completion(client, base_url, job_id, timeout)
    
    if not final_status:
        return False
        
    # Check if job completed successfully
    if final_status.get("status") != "COMPLETED":
        logger.error(f"Job did not complete successfully: {final_status}")
        return False
    
    # Get results
    results = await get_job_results(client, base_url, job_id)
    
    if not results:
        logger.error("Failed to get job results")
        return False
        
    # Validate results structure
    result_data = results.get("result", {})
    summary = result_data.get("result_summary", {})
    
    if not summary:
        logger.error("No summary data in results")
        return False
        
    comparable_areas = summary.get("comparable_areas", [])
    
    if not comparable_areas:
        logger.error("No comparable areas in results")
        return False
        
    logger.info(f"Comparable market area analysis successful with {len(comparable_areas)} areas")
    return True


async def run_tests(args):
    """Run all tests."""
    
    logger.info(f"Starting tests against {args.base_url}")
    
    # Create HTTP client
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        health_ok = await check_health(client, args.base_url)
        
        if not health_ok:
            logger.error("Health check failed, aborting further tests")
            return 1
            
        # Exit if only testing health
        if args.test_health_only:
            logger.info("Health check successful, exiting as requested")
            return 0
            
        # Test price trend analysis
        price_trend_ok = await test_price_trend_analysis(client, args.base_url, args.county_id, args.timeout)
        
        if not price_trend_ok:
            logger.error("Price trend analysis test failed")
            return 1
            
        # Test comparable market area
        comp_market_ok = await test_comparable_market_area(client, args.base_url, args.county_id, args.timeout)
        
        if not comp_market_ok:
            logger.error("Comparable market area test failed")
            return 1
            
        # List jobs
        jobs = await list_jobs(client, args.base_url, args.county_id)
        
        if jobs:
            logger.info(f"Listed {len(jobs)} jobs for county {args.county_id}")
        
        logger.info("All tests completed successfully!")
        return 0


def main():
    """Main entry point."""
    args = parse_args()
    
    # Configure log level
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger("market_analysis_test").setLevel(log_level)
    
    # Run the tests
    try:
        exit_code = asyncio.run(run_tests(args))
        return exit_code
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())