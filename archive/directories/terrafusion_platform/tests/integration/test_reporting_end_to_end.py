"""
Integration test for the end-to-end reporting workflow.

This test verifies the full lifecycle of report generation, from creation to status checking
to result retrieval.
"""

import asyncio
import time
import pytest
from fastapi.testclient import TestClient
import uuid

# Fixtures like `sync_client`, `db_session` are expected to be available
# from tests/integration/conftest.py.

@pytest.mark.asyncio
@pytest.mark.integration  # Mark as an integration test
async def test_reporting_workflows(
    sync_client: TestClient,  # Injected by conftest.py
    db_session  # Injected by conftest.py (actually an AsyncSession)
):
    """
    Tests the full reporting workflow for both success and failure scenarios:
    1. Successful report generation workflow
       - Call the /reporting/run endpoint
       - Poll until status is COMPLETED
       - Verify results data
    2. Failed report generation workflow
       - Use a report type that simulates failure
       - Verify proper error handling
    """
    # ----- Part 1: Successful Report Generation Test -----
    print("\n===== Testing Successful Report Generation =====")
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    test_report_type = "assessment_roll"
    test_parameters = {"year": 2025, "quarter": 2, "include_exempt": True}

    # --- 1. Call /reporting/run ---
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
    assert "status" in job_data
    report_id = job_data["report_id"]
    print(f"Test Reporting (Success): Job {report_id} initiated with status {job_data['status']}.")

    # --- 2. Poll status until COMPLETED (max ~10 seconds for this test) ---
    current_status = None
    max_polls = 20  # 20 polls * 0.5s sleep = 10 seconds max wait
    poll_interval = 0.5  # seconds

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
    # Based on the logic in routes.py: f"s3://terrafusion-reports/{county_id}/{report_type}/{report_id}.pdf"
    expected_location_part = f"s3://terrafusion-reports/{test_county_id}/{test_report_type}/{report_id}.pdf"
    assert result_detail["result_location"] == expected_location_part
    assert "result_metadata" in result_detail
    
    # Verify basic structure of result metadata
    assert "file_size_kb" in result_detail["result_metadata"]
    assert "pages" in result_detail["result_metadata"]
    assert "generation_time_seconds" in result_detail["result_metadata"]
    assert "generated_at" in result_detail["result_metadata"]

    print(f"Test Reporting (Success): Job {report_id} successfully completed and results verified.")

    # ----- Part 2: Simulated Failure Test -----
    print("\n===== Testing Simulated Report Failure =====")
    # Small delay to ensure we don't have issues with transaction management
    await asyncio.sleep(1)
    
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    # This specific report_type will trigger a FAILED status in the simulate_report_generation
    failing_report_type = "FAILING_REPORT_SIM" 
    test_parameters = {"year": 2025, "quarter": 2}

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
    assert results_response.status_code == 200  # The endpoint itself should work
    results_data = results_response.json()
    assert results_data["status"] == "FAILED"
    assert results_data["result"] is None  # No result data for failed jobs
    print(f"Test Reporting (Failure): Results endpoint for job {report_id} correctly reflects FAILED status.")