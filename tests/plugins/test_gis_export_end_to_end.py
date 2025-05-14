"""
Integration tests for the GIS Export plugin.

This module contains end-to-end tests for the GIS Export plugin's API endpoints,
covering the complete workflow from job submission to result retrieval.
"""

import pytest
import pytest_asyncio
import uuid
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.core_models import GisExportJob

# Import fixtures from conftest.py (test_client, db_session, sync_client)

# Test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_EXPORT_FORMAT = "GeoJSON"
TEST_FAIL_FORMAT = "FAIL_FORMAT_SIM"  # Special format that simulates failure
TEST_AREA_OF_INTEREST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-122.48, 37.78],
            [-122.48, 37.80],
            [-122.46, 37.80],
            [-122.46, 37.78],
            [-122.48, 37.78]
        ]
    ]
}
TEST_LAYERS = ["parcels", "buildings", "zoning"]
TEST_PARAMETERS = {
    "include_attributes": True,
    "simplify_tolerance": 0.0001,
    "coordinate_system": "EPSG:4326"
}


# db_session fixture is provided by conftest.py


@pytest_asyncio.fixture(scope="function")
async def cleanup_test_exports(db_session):
    """
    Clean up test exports before and after tests.
    
    This fixture deletes any test exports created during testing
    to ensure tests are isolated.
    """
    # Setup: Clean any existing test exports
    from sqlalchemy import delete
    
    stmt = delete(GisExportJob).where(
        (GisExportJob.county_id == TEST_COUNTY_ID) &
        (GisExportJob.export_format.in_([TEST_EXPORT_FORMAT, TEST_FAIL_FORMAT]))
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Run the test
    yield
    
    # Teardown: Clean up after test
    await db_session.execute(stmt)
    await db_session.commit()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_gis-export_job(cleanup_test_exports, test_client):
    """Test creating a new GIS export job."""
    # Prepare request data
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": TEST_EXPORT_FORMAT,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to create a GIS export job
    response = test_client.post("/plugins/v1/gis-export/run", json=export_data)
    
    # Check status code and response structure
    assert response.status_code == 202, f"Failed to create GIS export job: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert "job_id" in data
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["export_format"] == TEST_EXPORT_FORMAT
    assert data["status"] == "PENDING"
    assert "area_of_interest" in data["parameters"]
    assert "layers" in data["parameters"]
    
    # Save job_id for later tests
    job_id = data["job_id"]
    return job_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_gis-export_status(cleanup_test_exports, test_client):
    """Test retrieving the status of a GIS export job."""
    # First create a job
    job_id = await test_create_gis-export_job(cleanup_test_exports, test_client)
    
    # Check status endpoint
    response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
    
    # Check status code and response
    assert response.status_code == 200, f"Failed to get status: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert data["job_id"] == job_id
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["export_format"] == TEST_EXPORT_FORMAT
    assert data["status"] in ["PENDING", "RUNNING", "COMPLETED"]
    
    # Wait a moment and check again to see if status changes
    time.sleep(2)  # Give time for background processing
    
    response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
    assert response.status_code == 200
    data = response.json()
    
    # Status should have progressed
    assert data["status"] in ["RUNNING", "COMPLETED"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_gis-export_workflow(cleanup_test_exports, test_client):
    """Test the complete workflow: submit -> check status -> get results."""
    # Prepare request data
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": TEST_EXPORT_FORMAT,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit job
    response = test_client.post("/plugins/v1/gis-export/run", json=export_data)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    # Check status initially
    response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
    assert response.status_code == 200
    initial_status = response.json()["status"]
    assert initial_status in ["PENDING", "RUNNING"]
    
    # Wait for job to complete (with timeout)
    completed = False
    max_retries = 10
    retry_count = 0
    
    while not completed and retry_count < max_retries:
        time.sleep(1)  # Wait 1 second between checks
        response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        
        if status_data["status"] == "COMPLETED":
            completed = True
        elif status_data["status"] == "FAILED":
            assert False, f"Job failed unexpectedly: {status_data['message']}"
            
        retry_count += 1
    
    assert completed, f"Job did not complete within {max_retries} seconds"
    
    # Get results
    response = test_client.get(f"/plugins/v1/gis-export/results/{job_id}")
    assert response.status_code == 200
    results_data = response.json()
    
    # Verify result data
    assert results_data["job_id"] == job_id
    assert results_data["status"] == "COMPLETED"
    assert results_data["result"] is not None
    assert "result_file_location" in results_data["result"]
    assert "result_file_size_kb" in results_data["result"]
    assert "result_record_count" in results_data["result"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_failed_gis-export_job(cleanup_test_exports, test_client):
    """Test a GIS export job that is expected to fail."""
    # Prepare request data with special failure format
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": TEST_FAIL_FORMAT,  # Special format that triggers failure
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit job
    response = test_client.post("/plugins/v1/gis-export/run", json=export_data)
    assert response.status_code == 202
    job_id = response.json()["job_id"]
    
    # Wait for job to fail (with timeout)
    failed = False
    max_retries = 10
    retry_count = 0
    
    while not failed and retry_count < max_retries:
        time.sleep(1)  # Wait 1 second between checks
        response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        
        if status_data["status"] == "FAILED":
            failed = True
            
        retry_count += 1
    
    assert failed, f"Job did not fail within {max_retries} seconds"
    
    # Get results should return status with failure but no result data
    response = test_client.get(f"/plugins/v1/gis-export/results/{job_id}")
    assert response.status_code == 200
    results_data = response.json()
    
    # Verify failure data
    assert results_data["job_id"] == job_id
    assert results_data["status"] == "FAILED"
    assert "Simulated failure" in results_data["message"]
    assert results_data["result"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cancel_gis-export_job(cleanup_test_exports, test_client):
    """Test cancelling a GIS export job."""
    # Create a job
    job_id = await test_create_gis-export_job(cleanup_test_exports, test_client)
    
    # Cancel the job
    response = test_client.post(f"/plugins/v1/gis-export/cancel/{job_id}")
    
    # Check status code and response
    assert response.status_code == 200, f"Failed to cancel job: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert data["job_id"] == job_id
    assert data["status"] == "FAILED"
    assert "cancelled" in data["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_gis-export_jobs(cleanup_test_exports, test_client):
    """Test listing GIS export jobs with various filters."""
    # Create a few test jobs
    job_id1 = await test_create_gis-export_job(cleanup_test_exports, test_client)
    
    # Create a job with different format for filtering tests
    export_data = {
        "county_id": TEST_COUNTY_ID,
        "export_format": "KML",  # Different format
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    response = test_client.post("/plugins/v1/gis-export/run", json=export_data)
    assert response.status_code == 202
    job_id2 = response.json()["job_id"]
    
    # Wait a moment for jobs to be processed
    time.sleep(2)
    
    # Test listing all jobs
    response = test_client.get("/plugins/v1/gis-export/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Should have at least our 2 test jobs
    
    # Test filtering by county_id
    response = test_client.get(f"/plugins/v1/gis-export/list?county_id={TEST_COUNTY_ID}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    
    # Test filtering by export_format
    response = test_client.get(f"/plugins/v1/gis-export/list?export_format={TEST_EXPORT_FORMAT}")
    assert response.status_code == 200
    data = response.json()
    assert any(item["job_id"] == job_id1 for item in data)
    assert not any(item["job_id"] == job_id2 for item in data)  # job_id2 is KML
    
    # Test filtering by status
    response = test_client.get("/plugins/v1/gis-export/list?status=RUNNING")
    assert response.status_code == 200
    running_jobs = response.json()
    
    response = test_client.get("/plugins/v1/gis-export/list?status=COMPLETED")
    assert response.status_code == 200
    completed_jobs = response.json()
    
    # Either running or completed should contain our jobs
    all_jobs = running_jobs + completed_jobs
    assert any(item["job_id"] == job_id1 for item in all_jobs)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_gis-export_plugin_health(cleanup_test_exports, test_client):
    """Test the GIS Export plugin health check endpoint."""
    response = test_client.get("/plugins/v1/gis-export/health")
    
    # Check status code and response
    assert response.status_code == 200
    data = response.json()
    
    # Verify health data
    assert data["status"] == "healthy"
    assert data["plugin"] == "gis-export"
    assert "version" in data
    assert "timestamp" in data