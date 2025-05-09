"""
Integration tests for the reporting API CRUD operations.

These tests verify the basic CRUD functionality of the reporting API endpoints.
"""

import asyncio
import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime
from typing import Dict, Any, List

@pytest.mark.asyncio
@pytest.mark.integration
async def test_report_crud_operations(
    sync_client: TestClient,
    db_session
):
    """
    Test the basic CRUD operations for report jobs.
    
    This test verifies:
    1. Creating a report job (POST /reports)
    2. Retrieving a report job (GET /reports/{id})
    3. Updating a report job status (PATCH /reports/{id})
    4. Listing report jobs (GET /reports)
    """
    print("\n===== Testing Report Job CRUD Operations =====")
    
    # Create a report job
    test_county_id = f"TEST_COUNTY_{uuid.uuid4().hex[:8]}"
    test_report_type = "assessment_roll"
    test_parameters = {"year": 2025, "quarter": 2, "include_exempt": True}
    
    create_payload = {
        "report_type": test_report_type,
        "county_id": test_county_id,
        "parameters": test_parameters
    }
    
    print(f"Creating a new report job")
    response = sync_client.post("/plugins/v1/reporting/reports", json=create_payload)
    
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}. Response: {response.text}"
    job_data = response.json()
    print(f"Created job: {job_data['report_id']}")
    
    report_id = job_data["report_id"]
    
    # Retrieve the report job by ID
    print(f"Retrieving the report job by ID")
    get_response = sync_client.get(f"/plugins/v1/reporting/reports/{report_id}")
    
    assert get_response.status_code == 200
    get_job_data = get_response.json()
    assert get_job_data["report_id"] == report_id
    assert get_job_data["status"] == "PENDING"
    print(f"Successfully retrieved job with status: {get_job_data['status']}")
    
    # Update the report job status
    print(f"Updating the report job status to RUNNING")
    update_payload = {
        "status": "RUNNING",
        "message": "Report generation in progress"
    }
    
    update_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=update_payload)
    assert update_response.status_code == 200
    
    updated_job = update_response.json()
    assert updated_job["status"] == "RUNNING"
    assert updated_job["message"] == "Report generation in progress"
    print(f"Successfully updated job status to: {updated_job['status']}")
    
    # List all report jobs and verify our job is included
    print(f"Listing all report jobs")
    list_response = sync_client.get("/plugins/v1/reporting/reports")
    assert list_response.status_code == 200
    
    list_data = list_response.json()
    assert "items" in list_data
    assert "count" in list_data
    
    # Find our job in the list
    found = False
    for job in list_data["items"]:
        if job["report_id"] == report_id:
            found = True
            assert job["status"] == "RUNNING"
            break
    
    assert found, f"Could not find job {report_id} in the list of jobs"
    print(f"Successfully listed all jobs and found our job with status: RUNNING")
    
    # Complete the job with results
    print(f"Completing the report job with results")
    complete_payload = {
        "status": "COMPLETED",
        "message": "Report generation completed successfully",
        "result_location": f"s3://terrafusion-reports/{test_county_id}/{test_report_type}/{report_id}.pdf",
        "result_metadata": {
            "file_size_kb": 1024,
            "pages": 42,
            "generation_time_seconds": 3.5,
            "generated_at": datetime.utcnow().isoformat()
        }
    }
    
    complete_response = sync_client.patch(f"/plugins/v1/reporting/reports/{report_id}", json=complete_payload)
    assert complete_response.status_code == 200
    
    completed_job = complete_response.json()
    assert completed_job["status"] == "COMPLETED"
    assert completed_job["result_location"].endswith(f"{report_id}.pdf")
    print(f"Successfully completed the job with status: {completed_job['status']}")
    
    # Get the results from the results endpoint
    print(f"Getting results from the results endpoint")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    assert results_response.status_code == 200
    
    results_data = results_response.json()
    assert results_data["status"] == "COMPLETED"
    assert results_data["result"] is not None
    assert results_data["result"]["result_location"].endswith(f"{report_id}.pdf")
    assert "file_size_kb" in results_data["result"]["result_metadata"]
    print(f"Successfully retrieved results for the completed job")
    
    print("All CRUD operations completed successfully")