"""
Integration tests for the Reporting Plugin API endpoints.

This module tests the end-to-end functionality of the reporting system, including:
- Creating report jobs
- Getting report job status
- Getting report job results
- Listing report jobs
- Running reports with various parameters
"""

import pytest
import asyncio
import datetime
import time
import uuid
from typing import Dict, Any, List
from fastapi.testclient import TestClient

# Import the ReportJob model for typings
from terrafusion_sync.core_models import ReportJob

# Constants for testing
TEST_COUNTY_ID = "test_county"
TEST_REPORT_TYPE = "assessment_roll"


@pytest.mark.asyncio
async def test_create_report_job(sync_client: TestClient, create_report_job):
    """Test creating a report job."""
    # Prepare test data
    report_id = str(uuid.uuid4())
    report_data = {
        "report_type": TEST_REPORT_TYPE,
        "county_id": TEST_COUNTY_ID,
        "parameters": {
            "year": 2025,
            "quarter": 1,
            "include_exempt": True,
            "format": "pdf"
        }
    }
    
    # Call the API to create a report
    response = sync_client.post(
        "/plugins/v1/reporting/reports", 
        json=report_data
    )
    
    # Assertions
    assert response.status_code == 201, f"Expected 201, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "report_id" in data
    assert data["report_type"] == TEST_REPORT_TYPE
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["status"] == "PENDING"
    assert "created_at" in data
    
    # Verify parameters were stored correctly
    assert data["parameters"]["year"] == 2025
    assert data["parameters"]["quarter"] == 1
    assert data["parameters"]["include_exempt"] is True
    assert data["parameters"]["format"] == "pdf"


@pytest.mark.asyncio
async def test_get_report_by_id(sync_client: TestClient, create_report_job):
    """Test getting a report job by ID."""
    # Create a test report job in the database
    test_params = {
        "year": 2025,
        "quarter": 2,
        "special_parameter": "test_value"
    }
    report_job = await create_report_job(
        report_type=TEST_REPORT_TYPE,
        county_id=TEST_COUNTY_ID,
        status="PENDING",
        parameters_json=test_params
    )
    
    # Call the API to get the report
    response = sync_client.get(f"/plugins/v1/reporting/reports/{report_job.report_id}")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == report_job.report_id
    assert data["report_type"] == TEST_REPORT_TYPE
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["status"] == "PENDING"
    
    # Verify parameters match what we stored
    assert data["parameters"]["year"] == 2025
    assert data["parameters"]["quarter"] == 2
    assert data["parameters"]["special_parameter"] == "test_value"


@pytest.mark.asyncio
async def test_list_reports(sync_client: TestClient, create_report_job):
    """Test listing report jobs with filtering."""
    # Create some test report jobs
    await create_report_job(
        report_type=TEST_REPORT_TYPE,
        county_id=TEST_COUNTY_ID,
        status="COMPLETED"
    )
    await create_report_job(
        report_type="valuation_summary",
        county_id=TEST_COUNTY_ID,
        status="PENDING"
    )
    await create_report_job(
        report_type=TEST_REPORT_TYPE,
        county_id="another_county",
        status="PENDING"
    )
    
    # Test listing all reports
    response = sync_client.get("/plugins/v1/reporting/reports")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # At least the ones we just created
    
    # Test filtering by report_type
    response = sync_client.get("/plugins/v1/reporting/reports?report_type=valuation_summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(item["report_type"] == "valuation_summary" for item in data)
    
    # Test filtering by county_id
    response = sync_client.get("/plugins/v1/reporting/reports?county_id=another_county")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(item["county_id"] == "another_county" for item in data)
    
    # Test filtering by status
    response = sync_client.get("/plugins/v1/reporting/reports?status=COMPLETED")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(item["status"] == "COMPLETED" for item in data)
    
    # Test combined filtering
    response = sync_client.get(
        f"/plugins/v1/reporting/reports?report_type={TEST_REPORT_TYPE}&county_id={TEST_COUNTY_ID}&status=COMPLETED"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all(
        item["report_type"] == TEST_REPORT_TYPE 
        and item["county_id"] == TEST_COUNTY_ID 
        and item["status"] == "COMPLETED"
        for item in data
    )


@pytest.mark.asyncio
async def test_run_report(sync_client: TestClient, create_report_job):
    """Test running a report and checking its status."""
    # Prepare run request data
    run_data = {
        "report_type": TEST_REPORT_TYPE,
        "county_id": TEST_COUNTY_ID,
        "parameters": {
            "year": 2025,
            "format": "pdf",
            "include_charts": True
        }
    }
    
    # Run the report
    response = sync_client.post("/plugins/v1/reporting/run", json=run_data)
    assert response.status_code == 202, f"Expected 202, got {response.status_code}. Response: {response.text}"
    data = response.json()
    assert "report_id" in data
    report_id = data["report_id"]
    
    # Check initial status right after submission
    response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["PENDING", "RUNNING"]
    
    # In a real test, we would wait for the report to complete, but
    # for the integration test, we'll simulate completion by directly updating the DB
    # Wait a small amount to simulate processing time
    await asyncio.sleep(0.1)
    
    # Update the report status directly
    report_job = await create_report_job(
        report_id=report_id,  
        report_type=TEST_REPORT_TYPE,
        county_id=TEST_COUNTY_ID,
        status="COMPLETED",
        result_location="s3://terrafusion-reports/2025/test_county/assessment_roll_20250509.pdf",
        result_metadata_json={
            "page_count": 42,
            "file_size_bytes": 1048576,
            "generated_at": datetime.datetime.utcnow().isoformat()
        }
    )
    
    # Check the completed status
    response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert "result_location" in data
    assert data["result_location"] == report_job.result_location
    
    # Check getting the results
    response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["report_id"] == report_id
    assert data["status"] == "COMPLETED"
    assert data["result_location"] == report_job.result_location
    assert "result_metadata" in data
    assert data["result_metadata"]["page_count"] == 42
    assert data["result_metadata"]["file_size_bytes"] == 1048576


@pytest.mark.asyncio
async def test_report_failure_handling(sync_client: TestClient, create_report_job):
    """Test handling of failed reports."""
    # Create a failed report job
    error_message = "Report generation failed: missing required data for tax district 123"
    report_job = await create_report_job(
        report_type=TEST_REPORT_TYPE,
        county_id=TEST_COUNTY_ID,
        status="FAILED",
        message=error_message
    )
    
    # Check the failed status
    response = sync_client.get(f"/plugins/v1/reporting/status/{report_job.report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["message"] == error_message
    
    # Get the error details through the results endpoint
    response = sync_client.get(f"/plugins/v1/reporting/results/{report_job.report_id}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "failed" in data["detail"].lower()
    assert error_message in data["detail"]


@pytest.mark.asyncio
async def test_nonexistent_report(sync_client: TestClient):
    """Test handling of nonexistent report IDs."""
    nonexistent_id = str(uuid.uuid4())
    
    # Check status of nonexistent report
    response = sync_client.get(f"/plugins/v1/reporting/status/{nonexistent_id}")
    assert response.status_code == 404
    
    # Get results of nonexistent report
    response = sync_client.get(f"/plugins/v1/reporting/results/{nonexistent_id}")
    assert response.status_code == 404