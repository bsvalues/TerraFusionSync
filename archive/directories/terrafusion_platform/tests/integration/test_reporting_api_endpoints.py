"""
Integration tests for the reporting API endpoints.

These tests verify the functionality of the individual reporting API endpoints,
focusing on CRUD operations and error handling.
"""

import asyncio
import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Fixtures from conftest.py
# sync_client: TestClient
# db_session: AsyncSession

@pytest.mark.asyncio
@pytest.mark.integration
async def test_reporting_api_endpoints(
    sync_client: TestClient,
    db_session
):
    """
    Test the reporting API endpoints comprehensively.
    
    This combined test covers:
    1. Creating and retrieving report jobs
    2. Listing and filtering report jobs 
    3. Updating report job status
    4. Error handling for invalid inputs
    5. Behavior with non-existent resources
    """
    # ===== Part 1: Create and Get Report Job =====
    await test_create_and_get_report_job(sync_client, db_session)
    
    # Small delay to ensure we don't run into event loop issues
    await asyncio.sleep(1)
    
    # ===== Part 2: List Report Jobs =====
    await test_list_report_jobs(sync_client, db_session)
    
    # Small delay between test sections
    await asyncio.sleep(1)
    
    # ===== Part 3: Update Report Status =====
    await test_update_report_status(sync_client, db_session)
    
    # Small delay between test sections
    await asyncio.sleep(1)
    
    # ===== Part 4: Error Handling =====
    await test_error_handling(sync_client, db_session)
    
    # Small delay between test sections
    await asyncio.sleep(1)
    
    # ===== Part 5: Non-Existing Report Endpoints =====
    await test_non_existing_report_endpoints(sync_client, db_session)


async def test_create_and_get_report_job(
    sync_client: TestClient,
    db_session
):
    """
    Test creating a new report job and then retrieving it.
    
    This test verifies:
    1. POST /plugins/v1/reporting/reports endpoint for creating a report job
    2. GET /plugins/v1/reporting/reports/{report_id} for retrieving a specific report job
    """
    # --- Create a new report job ---
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    test_report_type = "assessment_roll"
    test_parameters = {"year": 2025, "quarter": 2, "include_exempt": True}
    
    create_payload = {
        "report_type": test_report_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    
    print(f"\n===== Testing Create Report Job =====")
    print(f"Creating report job with payload: {create_payload}")
    response = sync_client.post("/plugins/v1/reporting/reports", json=create_payload)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    job_data = response.json()
    print(f"Created report job: {job_data}")
    
    # Validate response fields
    report_id = job_data["report_id"]
    assert job_data["report_type"] == test_report_type
    assert job_data["county_id"] == test_county_id
    assert job_data["status"] == "PENDING"  # Should start as PENDING
    assert job_data["parameters"] == test_parameters
    assert "created_at" in job_data
    assert "updated_at" in job_data
    
    # --- Get the report job by ID ---
    print(f"Fetching report job with ID: {report_id}")
    get_response = sync_client.get(f"/plugins/v1/reporting/reports/{report_id}")
    
    assert get_response.status_code == 200, f"Expected 200 OK, got {get_response.status_code}. Response: {get_response.text}"
    get_job_data = get_response.json()
    print(f"Retrieved report job: {get_job_data}")
    
    # Validate the retrieved job matches what we created
    assert get_job_data["report_id"] == report_id
    assert get_job_data["report_type"] == test_report_type
    assert get_job_data["county_id"] == test_county_id
    assert get_job_data["parameters"] == test_parameters
    
    print(f"Successfully created and retrieved report job with ID: {report_id}")


async def test_list_report_jobs(
    sync_client: TestClient,
    db_session
):
    """
    Test listing report jobs with various filters.
    
    This test verifies:
    1. Creating multiple report jobs with different attributes
    2. GET /plugins/v1/reporting/reports for listing all report jobs
    3. Filtering by county_id, report_type, and status
    4. Pagination with limit and offset
    """
    print(f"\n===== Testing List Report Jobs =====")
    
    # Create multiple report jobs with different attributes
    # We'll create at least one for each filter we want to test
    jobs_to_create = [
        {
            "report_type": "assessment_roll",
            "county_id": f"TEST_COUNTY_A_{uuid.uuid4().hex[:6]}",
            "parameters": {"year": 2025}
        },
        {
            "report_type": "sales_ratio_study",
            "county_id": f"TEST_COUNTY_A_{uuid.uuid4().hex[:6]}",
            "parameters": {"year": 2025}
        },
        {
            "report_type": "assessment_roll",
            "county_id": f"TEST_COUNTY_B_{uuid.uuid4().hex[:6]}",
            "parameters": {"year": 2025}
        },
        {
            "report_type": "sales_ratio_study",
            "county_id": f"TEST_COUNTY_B_{uuid.uuid4().hex[:6]}",
            "parameters": {"year": 2025}
        }
    ]
    
    created_jobs = []
    
    # Create each job and store its ID and attributes
    for job_data in jobs_to_create:
        response = sync_client.post("/plugins/v1/reporting/reports", json=job_data)
        assert response.status_code == 200, f"Failed to create job. Status: {response.status_code}, Response: {response.text}"
        created_job = response.json()
        created_jobs.append(created_job)
        print(f"Created job: {created_job['report_id']} - Type: {created_job['report_type']}, County: {created_job['county_id']}")
    
    # Ensure we have enough jobs for testing
    assert len(created_jobs) >= 4, "Failed to create enough test jobs"
    
    # Wait a moment to ensure all jobs are properly committed
    await asyncio.sleep(1)
    
    # --- Test listing all jobs ---
    print("Testing listing all jobs...")
    list_response = sync_client.get("/plugins/v1/reporting/reports")
    assert list_response.status_code == 200
    list_data = list_response.json()
    
    # There might be other jobs from previous tests, so we just verify we have at least our created jobs
    assert list_data["count"] >= len(created_jobs)
    assert len(list_data["items"]) >= len(created_jobs)
    print(f"Found {list_data['count']} total jobs")
    
    # --- Test filtering by county_id ---
    # Extract county_id from first job
    county_a = created_jobs[0]["county_id"]
    county_jobs = [j for j in created_jobs if j["county_id"] == county_a]
    
    print(f"Testing filtering by county_id: {county_a}")
    county_response = sync_client.get(f"/plugins/v1/reporting/reports?county_id={county_a}")
    assert county_response.status_code == 200
    county_data = county_response.json()
    
    # Verify count matches expected number of jobs for this county
    assert county_data["count"] >= len(county_jobs)
    job_ids = [j["report_id"] for j in county_data["items"]]
    for job in county_jobs:
        assert job["report_id"] in job_ids, f"Job {job['report_id']} missing from county filtered results"
    print(f"Successfully filtered by county_id: {county_a}, found {county_data['count']} jobs")
    
    # --- Test filtering by report_type ---
    report_type = "assessment_roll"
    type_jobs = [j for j in created_jobs if j["report_type"] == report_type]
    
    print(f"Testing filtering by report_type: {report_type}")
    type_response = sync_client.get(f"/plugins/v1/reporting/reports?report_type={report_type}")
    assert type_response.status_code == 200
    type_data = type_response.json()
    
    # Verify we got at least our assessment roll jobs
    assert type_data["count"] >= len(type_jobs)
    job_ids = [j["report_id"] for j in type_data["items"]]
    for job in type_jobs:
        assert job["report_id"] in job_ids, f"Job {job['report_id']} missing from report type filtered results"
    print(f"Successfully filtered by report_type: {report_type}, found {type_data['count']} jobs")
    
    # --- Test filtering by status ---
    status = "PENDING"  # All our created jobs should be PENDING
    print(f"Testing filtering by status: {status}")
    status_response = sync_client.get(f"/plugins/v1/reporting/reports?status={status}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    
    # All jobs should be pending, but there might be others from different tests
    assert status_data["count"] >= len(created_jobs)
    print(f"Successfully filtered by status: {status}, found {status_data['count']} jobs")
    
    # --- Test pagination ---
    # Set a small limit to ensure pagination works
    limit = 2
    print(f"Testing pagination with limit={limit}")
    page1_response = sync_client.get(f"/plugins/v1/reporting/reports?limit={limit}")
    assert page1_response.status_code == 200
    page1_data = page1_response.json()
    
    # Verify we got the right number of items
    assert len(page1_data["items"]) == limit
    
    # Get the next page
    page2_response = sync_client.get(f"/plugins/v1/reporting/reports?limit={limit}&offset={limit}")
    assert page2_response.status_code == 200
    page2_data = page2_response.json()
    
    # Verify we get different items on the second page
    page1_ids = [j["report_id"] for j in page1_data["items"]]
    page2_ids = [j["report_id"] for j in page2_data["items"]]
    assert set(page1_ids).isdisjoint(set(page2_ids)), "Pagination returned duplicate jobs"
    
    print(f"Pagination test successful: page 1 ({len(page1_ids)} jobs) differs from page 2 ({len(page2_ids)} jobs)")


async def test_update_report_status(
    sync_client: TestClient,
    db_session
):
    """
    Test updating a report job status.
    
    This test verifies:
    1. Creating a report job
    2. Updating its status with PATCH /plugins/v1/reporting/reports/{report_id}
    3. Verifying the status is updated correctly
    """
    print(f"\n===== Testing Update Report Status =====")
    
    # Create a report job first
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    test_report_type = "assessment_roll"
    
    create_payload = {
        "report_type": test_report_type,
        "county_id": test_county_id,
        "parameters": {"year": 2025}
    }
    
    create_response = sync_client.post("/plugins/v1/reporting/reports", json=create_payload)
    assert create_response.status_code == 200
    job_data = create_response.json()
    report_id = job_data["report_id"]
    
    print(f"Created report job with ID: {report_id}")
    
    # Update the status to RUNNING
    update_payload = {
        "status": "RUNNING",
        "message": "Processing report data"
    }
    
    print(f"Updating job {report_id} status to RUNNING")
    update_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=update_payload)
    assert update_response.status_code == 200, f"Failed to update job status. Response: {update_response.text}"
    
    updated_job = update_response.json()
    assert updated_job["status"] == "RUNNING"
    assert updated_job["message"] == "Processing report data"
    print(f"Successfully updated job status to RUNNING")
    
    # Update the status to COMPLETED with result data
    result_location = f"s3://terrafusion-reports/{test_county_id}/{test_report_type}/{report_id}.pdf"
    result_metadata = {
        "file_size_kb": 1024,
        "pages": 42,
        "generation_time_seconds": 3.5,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    complete_payload = {
        "status": "COMPLETED",
        "message": "Report generated successfully",
        "result_location": result_location,
        "result_metadata": result_metadata
    }
    
    print(f"Updating job {report_id} status to COMPLETED with result data")
    complete_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=complete_payload)
    assert complete_response.status_code == 200
    
    completed_job = complete_response.json()
    assert completed_job["status"] == "COMPLETED"
    assert completed_job["message"] == "Report generated successfully"
    assert completed_job["result_location"] == result_location
    assert "result_metadata" in completed_job
    assert completed_job["result_metadata"]["file_size_kb"] == 1024
    assert completed_job["result_metadata"]["pages"] == 42
    
    print(f"Successfully updated job to COMPLETED with result data")


async def test_error_handling(
    sync_client: TestClient,
    db_session
):
    """
    Test error handling in the reporting API endpoints.
    
    This test verifies:
    1. Trying to create a report job with invalid data
    2. Trying to get a non-existent report job
    3. Trying to update a non-existent report job
    4. Trying to update a report job with invalid status
    """
    print(f"\n===== Testing Error Handling =====")
    
    # Test 1: Create with invalid data (missing required fields)
    invalid_payload = {
        "report_type": "assessment_roll"
        # Missing county_id
    }
    
    print("Testing create with invalid data (missing county_id)")
    invalid_response = sync_client.post("/plugins/v1/reporting/reports", json=invalid_payload)
    assert 400 <= invalid_response.status_code < 500, f"Expected client error, got {invalid_response.status_code}"
    print(f"Got expected error response: {invalid_response.status_code}")
    
    # Test 2: Get non-existent report job
    fake_id = str(uuid.uuid4())
    print(f"Testing get with non-existent ID: {fake_id}")
    not_found_response = sync_client.get(f"/plugins/v1/reporting/reports/{fake_id}")
    assert not_found_response.status_code == 404
    print(f"Got expected 404 response")
    
    # Test 3: Update non-existent report job
    print(f"Testing update with non-existent ID: {fake_id}")
    update_payload = {"status": "RUNNING"}
    not_found_update = sync_client.patch(f"/plugins/v1/reporting/reports/{fake_id}", json=update_payload)
    assert not_found_update.status_code == 404
    print(f"Got expected 404 response")
    
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
    
    print(f"Created report job with ID: {report_id} for invalid status test")
    
    # Try to update with invalid status
    invalid_status = {
        "status": "INVALID_STATUS"
    }
    
    print(f"Testing update with invalid status: {invalid_status['status']}")
    invalid_status_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=invalid_status)
    assert 400 <= invalid_status_response.status_code < 500
    print(f"Got expected error response: {invalid_status_response.status_code}")
    
    print("All error handling tests completed successfully")


async def test_non_existing_report_endpoints(
    sync_client: TestClient,
    db_session
):
    """
    Test the behavior of status and results endpoints with non-existent report IDs.
    
    This test verifies:
    1. GET /plugins/v1/reporting/status/{report_id} with non-existent ID
    2. GET /plugins/v1/reporting/results/{report_id} with non-existent ID
    """
    print(f"\n===== Testing Non-Existing Report Endpoints =====")
    
    fake_id = str(uuid.uuid4())
    
    # Test status endpoint with non-existent ID
    print(f"Testing status endpoint with non-existent ID: {fake_id}")
    status_response = sync_client.get(f"/plugins/v1/reporting/status/{fake_id}")
    assert status_response.status_code == 404
    print(f"Got expected 404 response from status endpoint")
    
    # Test results endpoint with non-existent ID
    print(f"Testing results endpoint with non-existent ID: {fake_id}")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{fake_id}")
    assert results_response.status_code == 404
    print(f"Got expected 404 response from results endpoint")