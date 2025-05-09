"""
TerraFusion Platform - Reporting Integration Tests

This module provides end-to-end integration tests for the reporting plugin functionality.
"""

import asyncio
import time
import pytest
import uuid
from fastapi.testclient import TestClient

@pytest.mark.asyncio
@pytest.mark.integration
async def test_reporting_workflow_success(
    sync_client: TestClient,
    db_session: asyncio.Future
):
    """
    Tests the full reporting workflow:
    1. Call the /plugins/v1/reporting/run endpoint on the terrafusion_sync service.
    2. Poll the /plugins/v1/reporting/status/{report_id} endpoint until status is COMPLETED.
    3. Fetch results from /plugins/v1/reporting/results/{report_id} and verify them.
    """
    test_county_id = f"REPORT_TEST_COUNTY_{uuid.uuid4().hex[:4]}"
    test_report_type = "simulated_sales_ratio_study"
    test_parameters = {"year": 2024, "property_class": "ALL"}

    # --- 1. Call /plugins/v1/reporting/run ---
    run_payload = {
        "report_type": test_report_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    print(f"Test Reporting (Success): Posting to /plugins/v1/reporting/run with payload: {run_payload}")
    
    response = sync_client.post("/plugins/v1/reporting/run", json=run_payload)
    
    assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}. Response: {response.text}"
    job_data = response.json()
    print(f"Test Reporting (Success): /run response: {job_data}")

    assert "report_id" in job_data
    assert "report_type" in job_data and job_data["report_type"] == test_report_type
    assert "county_id" in job_data and job_data["county_id"] == test_county_id
    assert "status" in job_data and job_data["status"] == "PENDING"
    report_id = job_data["report_id"]
    print(f"Test Reporting (Success): Job {report_id} initiated with status PENDING.")

    # --- 2. Poll status until COMPLETED (max ~10 seconds for this test) ---
    current_status = None
    max_polls = 20  # 20 polls * 0.5s sleep = 10 seconds max wait
    poll_interval = 0.5 # seconds

    print(f"Test Reporting (Success): Polling /plugins/v1/reporting/status/{report_id}...")
    for i in range(max_polls):
        status_response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
        assert status_response.status_code == 200, f"Status poll failed: {status_response.status_code}. Response: {status_response.text}"
        
        status_data = status_response.json()
        print(f"Test Reporting (Success): Poll {i+1}/{max_polls} - Status for job {report_id}: {status_data['status']}")
        current_status = status_data["status"]
        
        if current_status == "COMPLETED":
            break
        elif current_status == "FAILED":
            pytest.fail(f"Reporting job {report_id} FAILED. Message: {status_data.get('message', 'No message')}")
        
        await asyncio.sleep(poll_interval)
    
    assert current_status == "COMPLETED", f"Job {report_id} did not complete within the timeout. Last status: {current_status}"
    print(f"Test Reporting (Success): Job {report_id} COMPLETED.")

    # --- 3. Fetch results ---
    print(f"Test Reporting (Success): Fetching results from /plugins/v1/reporting/results/{report_id}...")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    
    assert results_response.status_code == 200, f"Results fetch failed: {results_response.status_code}. Response: {results_response.text}"
    results_data = results_response.json()
    print(f"Test Reporting (Success): /results response: {results_data}")

    assert results_data["report_id"] == report_id
    assert results_data["status"] == "COMPLETED"
    assert "result" in results_data
    assert results_data["result"] is not None, "Result field should not be null for a COMPLETED job"
    
    result_detail = results_data["result"]
    assert "result_location" in result_detail
    # Based on the implementation in simulate_report_generation
    expected_location_part = f"s3://terrafusion-reports/{test_county_id}/{test_report_type}/{report_id}.pdf"
    assert result_detail["result_location"] == expected_location_part
    assert "result_metadata" in result_detail
    assert result_detail["result_metadata"] == {"file_size_kb": 1024, "pages": 10}

    print(f"Test Reporting (Success): Job {report_id} successfully completed and results verified.")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_reporting_workflow_simulated_failure(
    sync_client: TestClient,
    db_session: asyncio.Future 
):
    """
    Tests the reporting workflow when the report type is designed to simulate a failure.
    """
    test_county_id = f"REPORT_FAIL_COUNTY_{uuid.uuid4().hex[:4]}"
    # This specific report_type will trigger a FAILED status in the mock _simulate_report_generation
    failing_report_type = "FAILING_REPORT_SIM" 
    test_parameters = {"year": 2023}

    run_payload = {
        "report_type": failing_report_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    print(f"Test Reporting (Failure): Posting to /plugins/v1/reporting/run with payload: {run_payload}")
    response = sync_client.post("/plugins/v1/reporting/run", json=run_payload)
    
    assert response.status_code == 202
    job_data = response.json()
    report_id = job_data["report_id"]
    assert job_data["status"] == "PENDING"
    print(f"Test Reporting (Failure): Job {report_id} initiated for failing report type.")

    # Poll status until FAILED or COMPLETED (should be FAILED)
    current_status = None
    max_polls = 20
    poll_interval = 0.5
    print(f"Test Reporting (Failure): Polling /plugins/v1/reporting/status/{report_id}...")
    for i in range(max_polls):
        status_response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        print(f"Test Reporting (Failure): Poll {i+1}/{max_polls} - Status for job {report_id}: {status_data['status']}")
        current_status = status_data["status"]
        if current_status == "FAILED":
            assert "Simulated report generation failure" in status_data.get("message", "")
            break
        elif current_status == "COMPLETED":
             pytest.fail(f"Job {report_id} for failing report type unexpectedly COMPLETED.")
        await asyncio.sleep(poll_interval)
    
    assert current_status == "FAILED", f"Job {report_id} for failing report type did not FAIL as expected. Last status: {current_status}"
    print(f"Test Reporting (Failure): Job {report_id} correctly FAILED as expected.")

    # Check results endpoint for a FAILED job
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    assert results_response.status_code == 200 # The endpoint itself should work
    results_data = results_response.json()
    assert results_data["status"] == "FAILED"
    assert results_data["result"] is None # No result data for failed jobs
    print(f"Test Reporting (Failure): Results endpoint for job {report_id} correctly reflects FAILED status.")