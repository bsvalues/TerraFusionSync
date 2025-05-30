"""
Integration test for the end-to-end market analysis workflow.

This test verifies the full lifecycle of market analysis jobs, from creation to status checking
to result retrieval. It covers both successful analysis and failure scenarios.
"""
import asyncio
import time
import uuid
import pytest
import random
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# Fixtures like `sync_client`, `db_session` are expected to be available
# from tests/integration/conftest.py.

@pytest.mark.asyncio
@pytest.mark.integration  # Mark as an integration test
async def test_market_analysis_workflows(
    sync_client: TestClient,  # Injected by conftest.py
    db_session: AsyncSession  # Injected by conftest.py
):
    """
    Tests the full market analysis workflow for both success and failure scenarios:
    1. Successful market analysis workflow
       - Call the /market-analysis/run endpoint
       - Poll until status is COMPLETED
       - Verify results data
    2. Failed market analysis workflow
       - Use an analysis type that simulates failure
       - Verify proper error handling
    """
    print("\n===== Testing Successful Market Analysis =====")
    
    # --- 1. SUCCESSFUL MARKET ANALYSIS WORKFLOW ---
    
    # Create a unique test county ID to avoid conflicts
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    
    # Prepare the request payload
    success_payload = {
        "analysis_type": "price_trend_by_zip",
        "county_id": test_county_id,
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "zip_codes": ["90210", "90211"],
            "property_types": ["residential"]
        }
    }
    
    print(f"Test Market Analysis (Success): Posting to /plugins/v1/market-analysis/run with payload: {success_payload}")
    
    # Make the request to start a market analysis job
    response = sync_client.post("/plugins/v1/market-analysis/run", json=success_payload)
    assert response.status_code == 202, f"Expected status code 202, but got {response.status_code}"
    
    response_data = response.json()
    print(f"Test Market Analysis (Success): /run response: {response_data}")
    
    # Get the job ID from the response
    job_id = response_data["job_id"]
    status = response_data["status"]
    print(f"Test Market Analysis (Success): Job {job_id} initiated with status {status}.")
    
    # Poll for job completion
    max_attempts = 20
    attempt = 0
    completed = False
    
    while attempt < max_attempts:
        attempt += 1
        status_endpoint = f"/plugins/v1/market-analysis/status/{job_id}"
        print(f"Test Market Analysis (Success): Polling {status_endpoint}...")
        
        status_response = sync_client.get(status_endpoint)
        assert status_response.status_code == 200, f"Status endpoint returned {status_response.status_code}"
        
        status_data = status_response.json()
        current_status = status_data["status"]
        print(f"Test Market Analysis (Success): Poll {attempt}/{max_attempts} - Status for job {job_id}: {current_status}")
        
        if current_status == "COMPLETED":
            completed = True
            print(f"Test Market Analysis (Success): Job {job_id} COMPLETED.")
            break
        elif current_status == "FAILED":
            assert False, f"Job failed unexpectedly: {status_data['message']}"
        
        # Wait before polling again
        await asyncio.sleep(1)
    
    assert completed, f"Job {job_id} did not complete within the expected timeframe"
    
    # Get results
    results_endpoint = f"/plugins/v1/market-analysis/results/{job_id}"
    print(f"Test Market Analysis (Success): Fetching results from {results_endpoint}...")
    
    results_response = sync_client.get(results_endpoint)
    assert results_response.status_code == 200, f"Results endpoint returned {results_response.status_code}"
    
    results_data = results_response.json()
    
    # Verify the result structure
    assert "result" in results_data, "Results should contain 'result' field"
    assert "result_summary" in results_data["result"], "Results should contain 'result_summary'"
    assert "trends" in results_data["result"], "Results should contain 'trends'"
    
    # Verify trends data structure
    trends = results_data["result"]["trends"]
    assert isinstance(trends, list), "Trends should be a list"
    assert len(trends) > 0, "Trends list should not be empty"
    
    # Verify first trend item has the expected fields
    first_trend = trends[0]
    assert "period" in first_trend, "Trend item should have 'period' field"
    assert "average_price" in first_trend, "Trend item should have 'average_price' field"
    assert "median_price" in first_trend, "Trend item should have 'median_price' field"
    
    # Verify result summary has expected fields
    result_summary = results_data["result"]["result_summary"]
    assert "key_finding" in result_summary, "Result summary should contain 'key_finding'"
    assert "data_points_analyzed" in result_summary, "Result summary should contain 'data_points_analyzed'"
    
    print("\n===== Testing Failed Market Analysis =====")
    
    # --- 2. FAILED MARKET ANALYSIS WORKFLOW ---
    
    # Prepare the request payload with a known failing analysis type
    failure_payload = {
        "analysis_type": "FAILING_ANALYSIS_SIM",  # This should trigger the simulated failure
        "county_id": test_county_id,
        "parameters": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "property_types": ["residential"]
        }
    }
    
    print(f"Test Market Analysis (Failure): Posting to /plugins/v1/market-analysis/run with payload: {failure_payload}")
    
    # Make the request to start a failing market analysis job
    failure_response = sync_client.post("/plugins/v1/market-analysis/run", json=failure_payload)
    assert failure_response.status_code == 202, f"Expected status code 202, but got {failure_response.status_code}"
    
    failure_response_data = failure_response.json()
    print(f"Test Market Analysis (Failure): /run response: {failure_response_data}")
    
    # Get the job ID from the response
    failure_job_id = failure_response_data["job_id"]
    failure_status = failure_response_data["status"]
    print(f"Test Market Analysis (Failure): Job {failure_job_id} initiated with status {failure_status}.")
    
    # Poll for job failure
    failure_max_attempts = 20
    failure_attempt = 0
    job_failed = False
    
    while failure_attempt < failure_max_attempts:
        failure_attempt += 1
        failure_status_endpoint = f"/plugins/v1/market-analysis/status/{failure_job_id}"
        print(f"Test Market Analysis (Failure): Polling {failure_status_endpoint}...")
        
        failure_status_response = sync_client.get(failure_status_endpoint)
        assert failure_status_response.status_code == 200, f"Status endpoint returned {failure_status_response.status_code}"
        
        failure_status_data = failure_status_response.json()
        current_failure_status = failure_status_data["status"]
        print(f"Test Market Analysis (Failure): Poll {failure_attempt}/{failure_max_attempts} - Status for job {failure_job_id}: {current_failure_status}")
        
        if current_failure_status == "FAILED":
            job_failed = True
            print(f"Test Market Analysis (Failure): Job {failure_job_id} FAILED as expected.")
            print(f"Test Market Analysis (Failure): Error message: {failure_status_data['message']}")
            
            # Verify error message contains expected text
            assert "Simulated market analysis failure" in failure_status_data['message'], "Expected error message not found"
            break
        elif current_failure_status == "COMPLETED":
            assert False, f"Expected job to fail but it completed successfully"
        
        # Wait before polling again
        await asyncio.sleep(1)
    
    assert job_failed, f"Job {failure_job_id} did not fail within the expected timeframe"
    
    print("\n===== All Market Analysis Tests Completed Successfully =====")