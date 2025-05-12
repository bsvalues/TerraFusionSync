"""
Integration test for the end-to-end market analysis workflow.

This test verifies the full lifecycle of market analysis jobs, from creation to status checking
to result retrieval.
"""

import asyncio
import time
import pytest
from fastapi.testclient import TestClient
import uuid
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
    # ----- Part 1: Successful Market Analysis Test -----
    print("\n===== Testing Successful Market Analysis =====")
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    test_analysis_type = "price_trend_by_zip"
    test_parameters = {
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "zip_codes": ["90210", "90211"],
        "property_types": ["residential"]
    }

    # --- 1. Call /market-analysis/run ---
    run_payload = {
        "analysis_type": test_analysis_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    print(f"Test Market Analysis (Success): Posting to /plugins/v1/market-analysis/run with payload: {run_payload}")
    
    response = sync_client.post("/plugins/v1/market-analysis/run", json=run_payload)
    
    assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}. Response: {response.text}"
    job_data = response.json()
    print(f"Test Market Analysis (Success): /run response: {job_data}")

    assert "job_id" in job_data
    assert "analysis_type" in job_data and job_data["analysis_type"] == test_analysis_type
    assert "county_id" in job_data and job_data["county_id"] == test_county_id
    assert "status" in job_data
    job_id = job_data["job_id"]
    print(f"Test Market Analysis (Success): Job {job_id} initiated with status {job_data['status']}.")

    # --- 2. Poll status until COMPLETED (max ~10 seconds for this test) ---
    current_status = None
    max_polls = 20  # 20 polls * 0.5s sleep = 10 seconds max wait
    poll_interval = 0.5  # seconds

    print(f"Test Market Analysis (Success): Polling /plugins/v1/market-analysis/status/{job_id}...")
    for i in range(max_polls):
        status_response = sync_client.get(f"/plugins/v1/market-analysis/status/{job_id}")
        assert status_response.status_code == 200, f"Status poll failed: {status_response.status_code}. Response: {status_response.text}"
        
        status_data = status_response.json()
        print(f"Test Market Analysis (Success): Poll {i+1}/{max_polls} - Status for job {job_id}: {status_data['status']}")
        current_status = status_data["status"]
        
        if current_status == "COMPLETED":
            break
        elif current_status == "FAILED":
            pytest.fail(f"Market Analysis job {job_id} FAILED. Message: {status_data.get('message', 'No message')}")
        
        await asyncio.sleep(poll_interval)
    
    assert current_status == "COMPLETED", f"Job {job_id} did not complete within the timeout. Last status: {current_status}"
    print(f"Test Market Analysis (Success): Job {job_id} COMPLETED.")

    # --- 3. Fetch results ---
    print(f"Test Market Analysis (Success): Fetching results from /plugins/v1/market-analysis/results/{job_id}...")
    results_response = sync_client.get(f"/plugins/v1/market-analysis/results/{job_id}")
    
    assert results_response.status_code == 200, f"Results fetch failed: {results_response.status_code}. Response: {results_response.text}"
    results_data = results_response.json()
    print(f"Test Market Analysis (Success): /results response: {results_data}")

    assert results_data["job_id"] == job_id
    assert results_data["status"] == "COMPLETED"
    assert "result" in results_data
    assert results_data["result"] is not None, "Result field should not be null for a COMPLETED job"
    
    result_detail = results_data["result"]
    assert "result_data_location" in result_detail
    assert result_detail["result_data_location"] is not None
    assert "result_summary" in result_detail
    
    # Verify the structure of result summary based on analysis type
    if test_analysis_type == "price_trend_by_zip":
        assert "trends" in result_detail["result_summary"]
        assert isinstance(result_detail["result_summary"]["trends"], list)
        if len(result_detail["result_summary"]["trends"]) > 0:
            # Check first trend entry if available
            trend = result_detail["result_summary"]["trends"][0]
            assert "zip_code" in trend
            assert "data_points" in trend
    
    print(f"Test Market Analysis (Success): Job {job_id} successfully completed and results verified.")

    # ----- Part 2: List Jobs Test -----
    print("\n===== Testing Market Analysis Job Listing =====")
    # Small delay to ensure we don't have issues with transaction management
    await asyncio.sleep(1)
    
    # Test listing all jobs
    print("Test Market Analysis (List): Fetching all jobs")
    list_response = sync_client.get("/plugins/v1/market-analysis/list")
    assert list_response.status_code == 200
    list_data = list_response.json()
    print(f"Test Market Analysis (List): Found {len(list_data['jobs'])} jobs")
    assert len(list_data["jobs"]) > 0
    
    # Test listing jobs by county
    print(f"Test Market Analysis (List): Fetching jobs for county {test_county_id}")
    county_list_response = sync_client.get(f"/plugins/v1/market-analysis/list?county_id={test_county_id}")
    assert county_list_response.status_code == 200
    county_list_data = county_list_response.json()
    print(f"Test Market Analysis (List): Found {len(county_list_data['jobs'])} jobs for county {test_county_id}")
    assert len(county_list_data["jobs"]) > 0
    assert all(job["county_id"] == test_county_id for job in county_list_data["jobs"])
    
    # Test listing jobs by analysis type
    print(f"Test Market Analysis (List): Fetching jobs for analysis type {test_analysis_type}")
    type_list_response = sync_client.get(f"/plugins/v1/market-analysis/list?analysis_type={test_analysis_type}")
    assert type_list_response.status_code == 200
    type_list_data = type_list_response.json()
    print(f"Test Market Analysis (List): Found {len(type_list_data['jobs'])} jobs for analysis type {test_analysis_type}")
    assert len(type_list_data["jobs"]) > 0
    assert all(job["analysis_type"] == test_analysis_type for job in type_list_data["jobs"])
    
    # ----- Part 3: Simulated Failure Test -----
    print("\n===== Testing Simulated Market Analysis Failure =====")
    # Small delay to ensure we don't have issues with transaction management
    await asyncio.sleep(1)
    
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    # This specific analysis_type will trigger a FAILED status in the processing
    failing_analysis_type = "FAILING_ANALYSIS_SIM" 
    test_parameters = {"year": 2025, "quarter": 2}

    run_payload = {
        "analysis_type": failing_analysis_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    print(f"Test Market Analysis (Failure): Posting to /plugins/v1/market-analysis/run with payload: {run_payload}")
    response = sync_client.post("/plugins/v1/market-analysis/run", json=run_payload)
    
    assert response.status_code == 202
    job_data = response.json()
    job_id = job_data["job_id"]
    print(f"Test Market Analysis (Failure): Job {job_id} initiated for failing analysis type.")

    # Poll status until FAILED or COMPLETED (should be FAILED)
    current_status = None
    max_polls = 20
    poll_interval = 0.5
    print(f"Test Market Analysis (Failure): Polling /plugins/v1/market-analysis/status/{job_id}...")
    for i in range(max_polls):
        status_response = sync_client.get(f"/plugins/v1/market-analysis/status/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        print(f"Test Market Analysis (Failure): Poll {i+1}/{max_polls} - Status for job {job_id}: {status_data['status']}")
        current_status = status_data["status"]
        if current_status == "FAILED":
            assert "Simulated market analysis failure" in status_data.get("message", "")
            break
        elif current_status == "COMPLETED":
             pytest.fail(f"Job {job_id} for failing analysis type unexpectedly COMPLETED.")
        await asyncio.sleep(poll_interval)
    
    assert current_status == "FAILED", f"Job {job_id} for failing analysis type did not FAIL as expected. Last status: {current_status}"
    print(f"Test Market Analysis (Failure): Job {job_id} correctly FAILED as expected.")

    # Check results endpoint for a FAILED job
    results_response = sync_client.get(f"/plugins/v1/market-analysis/results/{job_id}")
    assert results_response.status_code == 200  # The endpoint itself should work
    results_data = results_response.json()
    assert results_data["status"] == "FAILED"
    assert results_data["result"] is None  # No result data for failed jobs
    print(f"Test Market Analysis (Failure): Results endpoint for job {job_id} correctly reflects FAILED status.")

    # ----- Part 4: Job Not Found Test -----
    print("\n===== Testing Job Not Found Handling =====")
    
    # Test with a non-existent job ID
    non_existent_job_id = str(uuid.uuid4())
    print(f"Test Market Analysis (Not Found): Checking status for non-existent job {non_existent_job_id}")
    
    status_response = sync_client.get(f"/plugins/v1/market-analysis/status/{non_existent_job_id}")
    assert status_response.status_code == 404
    print(f"Test Market Analysis (Not Found): Status check correctly returned 404 for non-existent job")
    
    results_response = sync_client.get(f"/plugins/v1/market-analysis/results/{non_existent_job_id}")
    assert results_response.status_code == 404
    print(f"Test Market Analysis (Not Found): Results check correctly returned 404 for non-existent job")