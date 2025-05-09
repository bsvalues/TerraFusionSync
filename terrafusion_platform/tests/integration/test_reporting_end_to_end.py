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
import pytest_asyncio
import asyncio
import time
import uuid
from typing import Dict, Any
from datetime import datetime, timedelta

from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_create_report_job(sync_client: TestClient, create_report_job):
    """Test creating a report job."""
    # Prepare test data
    report_data = {
        "report_type": "assessment_roll",
        "county_id": "test_county",
        "parameters": {
            "year": 2025,
            "quarter": 2,
            "include_exempt": True
        }
    }
    
    # Call the API
    response = sync_client.post("/plugins/v1/reporting/reports", json=report_data)
    
    # Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Check response structure
    assert "report_id" in data, "Response missing report_id"
    assert data["report_type"] == report_data["report_type"]
    assert data["county_id"] == report_data["county_id"]
    assert data["parameters"]["year"] == report_data["parameters"]["year"]
    assert data["parameters"]["quarter"] == report_data["parameters"]["quarter"]
    assert data["status"] == "PENDING"


@pytest.mark.asyncio
async def test_get_report_by_id(sync_client: TestClient, create_report_job):
    """Test getting a report job by ID."""
    # Create a report job using the fixture
    report_job = await create_report_job(
        report_type="assessment_roll",
        county_id="test_county",
        status="COMPLETED",
        parameters_json={
            "year": 2025,
            "quarter": 1,
            "include_exempt": True
        },
        result_location="s3://test-bucket/reports/test-report.xlsx",
        result_metadata_json={
            "rows": 1500,
            "file_size_bytes": 35000,
            "generated_at": datetime.utcnow().isoformat()
        }
    )
    
    # Get the report through the API
    response = sync_client.get(f"/plugins/v1/reporting/reports/{report_job.report_id}")
    
    # Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Check response structure and data
    assert data["report_id"] == report_job.report_id
    assert data["report_type"] == report_job.report_type
    assert data["county_id"] == report_job.county_id
    assert data["status"] == report_job.status
    assert data["parameters"]["year"] == report_job.parameters_json["year"]
    assert data["parameters"]["quarter"] == report_job.parameters_json["quarter"]
    assert data["result_location"] == report_job.result_location
    assert data["result_metadata"]["rows"] == report_job.result_metadata_json["rows"]


@pytest.mark.asyncio
async def test_list_reports(sync_client: TestClient, create_report_job):
    """Test listing report jobs with filtering."""
    # Create multiple report jobs for testing
    county_id = "test_county_list"
    await create_report_job(
        report_type="assessment_roll",
        county_id=county_id,
        status="COMPLETED"
    )
    await create_report_job(
        report_type="exemption_report",
        county_id=county_id,
        status="PENDING"
    )
    await create_report_job(
        report_type="valuation_summary",
        county_id=county_id,
        status="FAILED"
    )
    
    # List all reports for the test county
    response = sync_client.get(f"/plugins/v1/reporting/reports?county_id={county_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3, f"Expected 3 reports, got {len(data)}"
    
    # Filter by report_type
    response = sync_client.get(f"/plugins/v1/reporting/reports?county_id={county_id}&report_type=assessment_roll")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["report_type"] == "assessment_roll"
    
    # Filter by status
    response = sync_client.get(f"/plugins/v1/reporting/reports?county_id={county_id}&status=FAILED")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "FAILED"
    assert data[0]["report_type"] == "valuation_summary"


@pytest.mark.asyncio
async def test_run_report(sync_client: TestClient, create_report_job):
    """Test running a report and checking its status."""
    # Prepare the test data
    run_data = {
        "report_type": "assessment_roll",
        "county_id": "test_county",
        "parameters": {
            "year": 2025,
            "quarter": 2,
            "include_exempt": True
        }
    }
    
    # Call the run API
    response = sync_client.post("/plugins/v1/reporting/run", json=run_data)
    assert response.status_code == 202, f"Expected 202 Accepted, got {response.status_code}: {response.text}"
    data = response.json()
    assert "report_id" in data
    assert "status_url" in data
    
    # Check the status URL works
    report_id = data["report_id"]
    status_response = sync_client.get(f"/plugins/v1/reporting/status/{report_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["report_id"] == report_id
    assert "status" in status_data
    assert "progress" in status_data
    
    # Simulate a completed report by updating it directly in the database
    result_location = f"s3://test-bucket/reports/{report_id}.xlsx"
    result_metadata = {
        "rows": 1250,
        "file_size_bytes": 42500,
        "generation_time_seconds": 2.5,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    # Update the job using the create_report_job fixture
    updated_job = await create_report_job(
        report_id=report_id,
        status="COMPLETED",
        result_location=result_location,
        result_metadata_json=result_metadata
    )
    
    # Now check if the results endpoint works
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_id}")
    assert results_response.status_code == 200
    results_data = results_response.json()
    assert results_data["report_id"] == report_id
    assert results_data["status"] == "COMPLETED"
    assert results_data["result_location"] == result_location
    assert results_data["result_metadata"]["rows"] == result_metadata["rows"]


@pytest.mark.asyncio
async def test_report_failure_handling(sync_client: TestClient, create_report_job):
    """Test handling of failed reports."""
    # Create a failed report job
    error_message = "Failed to generate report: insufficient data for year 2025"
    report_job = await create_report_job(
        report_type="assessment_roll",
        county_id="test_county",
        status="FAILED",
        message=error_message
    )
    
    # Check the status through the API
    response = sync_client.get(f"/plugins/v1/reporting/status/{report_job.report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "FAILED"
    assert data["message"] == error_message
    
    # Check results handling for failed reports
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{report_job.report_id}")
    assert results_response.status_code == 404, "Failed reports should return 404 for results endpoint"


@pytest.mark.asyncio
async def test_nonexistent_report(sync_client: TestClient):
    """Test handling of nonexistent report IDs."""
    nonexistent_id = str(uuid.uuid4())
    
    # Test getting a nonexistent report
    response = sync_client.get(f"/plugins/v1/reporting/reports/{nonexistent_id}")
    assert response.status_code == 404
    
    # Test status for nonexistent report
    status_response = sync_client.get(f"/plugins/v1/reporting/status/{nonexistent_id}")
    assert status_response.status_code == 404
    
    # Test results for nonexistent report
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{nonexistent_id}")
    assert results_response.status_code == 404