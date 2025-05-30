"""
Combined integration tests for the reporting API.

This test file combines all reporting tests into a single test function
to avoid issues with the asyncio event loop being closed between tests.
"""

import asyncio
import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any, List
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_reporting_combined(
    sync_client: TestClient,
    db_session
):
    """
    Combined test for all reporting API functionality.
    
    This test runs all the reporting tests in sequence within a single test function
    to avoid issues with the asyncio event loop being closed between tests.
    """
    logger.info("Starting combined reporting tests")
    
    # ===== PART 1: End-to-End Test (Success Case) =====
    logger.info("\n===== PART 1: End-to-End Test (Success Case) =====")
    
    # Create a unique county ID for this test
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    
    # Test parameters
    test_report_type = "assessment_roll"
    test_parameters = {"year": 2025, "quarter": 2, "include_exempt": True}
    
    # Run payload for success case
    success_payload = {
        "report_type": test_report_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    
    logger.info(f"Test Reporting (Success): Posting to /plugins/v1/reporting/run with payload: {success_payload}")
    run_response = sync_client.post("/plugins/v1/reporting/run", json=success_payload)
    
    assert run_response.status_code == 202, f"Expected 202 Accepted, got {run_response.status_code}"
    
    run_data = run_response.json()
    logger.info(f"Test Reporting (Success): /run response: {run_data}")
    
    report_id = run_data["report_id"]
    initial_status = run_data["status"]
    
    logger.info(f"Test Reporting (Success): Job {report_id} initiated with status {initial_status}.")
    
    # Poll status until completion or timeout
    max_polls = 20
    poll_interval_seconds = 0.5
    
    complete = False
    for i in range(1, max_polls + 1):
        logger.info(f"Test Reporting (Success): Polling /plugins/v1/reporting/status/{report_id}...")
        status_response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
        
        assert status_response.status_code == 200, f"Status API failed with code {status_response.status_code}"
        
        status_data = status_response.json()
        current_status = status_data["status"]
        
        logger.info(f"Test Reporting (Success): Poll {i}/{max_polls} - Status for job {report_id}: {current_status}")
        
        if current_status == "COMPLETED":
            complete = True
            logger.info(f"Test Reporting (Success): Job {report_id} COMPLETED.")
            break
        elif current_status == "FAILED":
            assert False, f"Report job failed: {status_data.get('message', 'No error message provided')}"
        
        # Only wait if we're going to poll again
        if i < max_polls:
            time.sleep(poll_interval_seconds)
    
    assert complete, f"Report job did not complete within {max_polls} polls"
    
    # Get results for the completed job
    logger.info(f"Test Reporting (Success): Getting results for completed job {report_id}")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    
    assert results_response.status_code == 200, f"Results API failed with code {results_response.status_code}"
    
    results_data = results_response.json()
    logger.info(f"Test Reporting (Success): Results: {results_data}")
    
    assert results_data["status"] == "COMPLETED"
    assert results_data["result"] is not None
    assert "result_location" in results_data["result"]
    assert results_data["result"]["result_location"].endswith(f"{report_id}.pdf")
    
    logger.info("Test Reporting (Success): Successfully completed end-to-end test")
    
    # Add a small delay between tests to ensure DB connections are properly closed
    await asyncio.sleep(1)
    
    # ===== PART 2: CRUD Operations Test =====
    logger.info("\n===== PART 2: CRUD Operations Test =====")
    
    # Create a report job
    crud_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    
    create_payload = {
        "report_type": "assessment_roll",
        "county_id": crud_county_id,
        "parameters": {"year": 2025, "quarter": 2, "include_exempt": True}
    }
    
    logger.info(f"Creating a new report job")
    response = sync_client.post("/plugins/v1/reporting/reports", json=create_payload)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    job_data = response.json()
    logger.info(f"Created job: {job_data['report_id']}")
    
    crud_report_id = job_data["report_id"]
    
    # Retrieve the report job by ID
    logger.info(f"Retrieving the report job by ID")
    get_response = sync_client.get(f"/plugins/v1/reporting/reports/{crud_report_id}")
    
    assert get_response.status_code == 200
    get_job_data = get_response.json()
    assert get_job_data["report_id"] == crud_report_id
    assert get_job_data["status"] == "PENDING"
    logger.info(f"Successfully retrieved job with status: {get_job_data['status']}")
    
    # Update the report job status
    logger.info(f"Updating the report job status to RUNNING")
    update_payload = {
        "status": "RUNNING",
        "message": "Report generation in progress"
    }
    
    update_response = sync_client.patch(f"/plugins/v1/reporting/reports/{crud_report_id}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_job = update_response.json()
    assert updated_job["status"] == "RUNNING"
    assert updated_job["message"] == "Report generation in progress"
    logger.info(f"Successfully updated job status to: {updated_job['status']}")
    
    # List all report jobs and verify our job is included
    logger.info(f"Listing all report jobs")
    list_response = sync_client.get("/plugins/v1/reporting/reports")
    assert list_response.status_code == 200
    
    list_data = list_response.json()
    assert "items" in list_data
    assert "count" in list_data
    
    # Find our job in the list
    found = False
    for job in list_data["items"]:
        if job["report_id"] == crud_report_id:
            found = True
            assert job["status"] == "RUNNING"
            break
    
    assert found, f"Could not find job {crud_report_id} in the list of jobs"
    logger.info(f"Successfully listed all jobs and found our job with status: RUNNING")
    
    # Complete the job with results
    logger.info(f"Completing the report job with results")
    complete_payload = {
        "status": "COMPLETED",
        "message": "Report generation completed successfully",
        "result_location": f"s3://terrafusion-reports/{crud_county_id}/assessment_roll/{crud_report_id}.pdf",
        "result_metadata": {
            "file_size_kb": 1024,
            "pages": 42,
            "generation_time_seconds": 3.5,
            "generated_at": datetime.utcnow().isoformat()
        }
    }
    
    complete_response = sync_client.patch(f"/plugins/v1/reporting/reports/{crud_report_id}", json=complete_payload)
    assert complete_response.status_code == 200
    
    completed_job = complete_response.json()
    assert completed_job["status"] == "COMPLETED"
    assert completed_job["result_location"].endswith(f"{crud_report_id}.pdf")
    logger.info(f"Successfully completed the job with status: {completed_job['status']}")
    
    # Get the results from the results endpoint
    logger.info(f"Getting results from the results endpoint")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{crud_report_id}")
    assert results_response.status_code == 200
    
    results_data = results_response.json()
    assert results_data["status"] == "COMPLETED"
    assert results_data["result"] is not None
    assert results_data["result"]["result_location"].endswith(f"{crud_report_id}.pdf")
    assert "file_size_kb" in results_data["result"]["result_metadata"]
    logger.info(f"Successfully retrieved results for the completed job")
    
    logger.info("All CRUD operations completed successfully")
    
    # Add a small delay between tests to ensure DB connections are properly closed
    await asyncio.sleep(1)
    
    # ===== PART 3: Error Handling Test =====
    logger.info("\n===== PART 3: Error Handling Test =====")
    
    # Test 1: Create with invalid data (missing required fields)
    invalid_payload = {
        "report_type": "assessment_roll"
        # Missing county_id
    }
    
    logger.info("Testing create with invalid data (missing county_id)")
    invalid_response = sync_client.post("/plugins/v1/reporting/reports", json=invalid_payload)
    assert 400 <= invalid_response.status_code < 500, f"Expected client error, got {invalid_response.status_code}"
    logger.info(f"Got expected error response: {invalid_response.status_code}")
    
    # Test 2: Get non-existent report job
    fake_id = str(uuid.uuid4())
    logger.info(f"Testing get with non-existent ID: {fake_id}")
    not_found_response = sync_client.get(f"/plugins/v1/reporting/reports/{fake_id}")
    assert not_found_response.status_code == 404
    logger.info(f"Got expected 404 response")
    
    # Test 3: Update non-existent report job
    logger.info(f"Testing update with non-existent ID: {fake_id}")
    update_payload = {"status": "RUNNING"}
    not_found_update = sync_client.patch(f"/plugins/v1/reporting/reports/{fake_id}", json=update_payload)
    assert not_found_update.status_code == 404
    logger.info(f"Got expected 404 response")
    
    # Test 4: Update with invalid status
    # First create a valid job
    valid_payload = {
        "report_type": "assessment_roll",
        "county_id": f"TEST_COUNTY_{uuid.uuid4().hex[:8]}",
        "parameters": {"year": 2025}
    }
    
    create_response = sync_client.post("/plugins/v1/reporting/reports", json=valid_payload)
    assert create_response.status_code == 200
    job_data = create_response.json()
    report_id = job_data["report_id"]
    
    logger.info(f"Created report job with ID: {report_id} for invalid status test")
    
    # Try to update with invalid status
    invalid_status = {
        "status": "INVALID_STATUS"
    }
    
    logger.info(f"Testing update with invalid status: {invalid_status['status']}")
    invalid_status_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=invalid_status)
    assert 400 <= invalid_status_response.status_code < 500
    logger.info(f"Got expected error response: {invalid_status_response.status_code}")
    
    # Test 5: Test status and results endpoints with non-existent ID
    logger.info(f"Testing status endpoint with non-existent ID: {fake_id}")
    status_response = sync_client.get(f"/plugins/v1/reporting/status/{fake_id}")
    assert status_response.status_code == 404
    logger.info(f"Got expected 404 response from status endpoint")
    
    logger.info(f"Testing results endpoint with non-existent ID: {fake_id}")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{fake_id}")
    assert results_response.status_code == 404
    logger.info(f"Got expected 404 response from results endpoint")
    
    logger.info("All error handling tests completed successfully")
    
    # ===== All Tests Complete =====
    logger.info("\n===== All Reporting Tests Completed Successfully =====")