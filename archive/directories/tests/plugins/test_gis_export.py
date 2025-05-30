"""
Integration tests for the GIS Export plugin.

This module contains end-to-end tests for the GIS Export plugin's API endpoints,
covering the complete workflow from job submission to result retrieval.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from terrafusion_sync.core_models import GisExportJob

# Test data constants
TEST_COUNTY_ID = "test_county"
TEST_EXPORT_FORMAT = "GeoJSON"
TEST_FAIL_FORMAT = "FAIL_FORMAT_SIM"  # Format that simulates failure
TEST_AREA_OF_INTEREST = {
    "type": "Polygon",
    "coordinates": [
        [
            [-119.3, 46.1],
            [-119.2, 46.1],
            [-119.2, 46.2],
            [-119.3, 46.2],
            [-119.3, 46.1]
        ]
    ]
}
TEST_LAYERS = ["parcels", "roads", "zoning"]
TEST_PARAMETERS = {
    "include_attributes": True,
    "simplify_tolerance": 0.0001,
    "coordinate_system": "EPSG:4326"
}
TEST_USERNAME = "test_user"


@pytest_asyncio.fixture
async def cleanup_test_exports(db_session):
    """Remove test GIS export jobs before and after tests."""
    # Clean up before test
    async with db_session() as session:
        async with session.begin():
            stmt = select(GisExportJob).where(GisExportJob.county_id == TEST_COUNTY_ID)
            result = await session.execute(stmt)
            for job in result.scalars().all():
                await session.delete(job)
    
    # Run the test
    yield
    
    # Clean up after test
    async with db_session() as session:
        async with session.begin():
            stmt = select(GisExportJob).where(GisExportJob.county_id == TEST_COUNTY_ID)
            result = await session.execute(stmt)
            for job in result.scalars().all():
                await session.delete(job)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint(test_client):
    """Test the GIS Export plugin health endpoint."""
    response = test_client.get("/plugins/v1/gis-export/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["plugin"] == "gis_export"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_gis_export_workflow(cleanup_test_exports, test_client, db_session):
    """Test the complete GIS export workflow from creation to completion."""
    # Create a job
    job_data = {
        "county_id": TEST_COUNTY_ID,
        "format": TEST_EXPORT_FORMAT,
        "username": TEST_USERNAME,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit the job
    response = test_client.post("/plugins/v1/gis-export/run", json=job_data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Wait for the job to complete (background task should process it)
    max_attempts = 10
    data = None
    for attempt in range(max_attempts):
        response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "COMPLETED":
            break
        elif data["status"] == "FAILED":
            pytest.fail(f"Job failed unexpectedly: {data.get('message', 'No message')}")
        
        # Wait a moment before checking again
        await asyncio.sleep(1)
    
    # Verify the job data exists and completed
    assert data is not None, "No job data received"
    assert data["status"] == "COMPLETED", f"Job did not complete within {max_attempts} attempts"
    
    # Verify job data in database
    async with db_session() as session:
        stmt = select(GisExportJob).where(GisExportJob.job_id == str(job_id))
        result = await session.execute(stmt)
        db_job = result.scalar_one_or_none()
        
        assert db_job is not None
        assert db_job.status == "COMPLETED"
        assert db_job.county_id == TEST_COUNTY_ID
        assert db_job.export_format == TEST_EXPORT_FORMAT
        assert db_job.completed_at is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_failed_gis_export_job(cleanup_test_exports, test_client, db_session):
    """Test a GIS export job that fails."""
    # Create a job with a format that triggers failure
    job_data = {
        "county_id": TEST_COUNTY_ID,
        "format": TEST_FAIL_FORMAT,  # This format triggers a simulated failure
        "username": TEST_USERNAME,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit the job
    response = test_client.post("/plugins/v1/gis-export/run", json=job_data)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Wait for the job to fail
    max_attempts = 10
    data = None
    for attempt in range(max_attempts):
        response = test_client.get(f"/plugins/v1/gis-export/status/{job_id}")
        assert response.status_code == 200
        data = response.json()
        
        if data["status"] == "FAILED":
            break
        
        # Wait a moment before checking again
        await asyncio.sleep(1)
    
    # Verify the job failed
    assert data is not None, "No job data received"
    assert data["status"] == "FAILED", f"Job did not fail as expected within {max_attempts} attempts"
    assert "message" in data, "Failed job should include error message"
    
    # Verify job data in database
    async with db_session() as session:
        stmt = select(GisExportJob).where(GisExportJob.job_id == str(job_id))
        result = await session.execute(stmt)
        db_job = result.scalar_one_or_none()
        
        assert db_job is not None
        assert db_job.status == "FAILED"
        assert db_job.message is not None  # Should have error message


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_gis_export_jobs(cleanup_test_exports, test_client, db_session):
    """Test listing GIS export jobs with various filters."""
    # Create two test jobs with different formats
    job_data1 = {
        "county_id": TEST_COUNTY_ID,
        "format": "GeoJSON",
        "username": TEST_USERNAME,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    job_data2 = {
        "county_id": TEST_COUNTY_ID,
        "format": "Shapefile",
        "username": TEST_USERNAME,
        "area_of_interest": TEST_AREA_OF_INTEREST,
        "layers": TEST_LAYERS,
        "parameters": TEST_PARAMETERS
    }
    
    # Submit jobs
    response1 = test_client.post("/plugins/v1/gis-export/run", json=job_data1)
    assert response1.status_code == 200
    job_id1 = response1.json()["job_id"]
    
    response2 = test_client.post("/plugins/v1/gis-export/run", json=job_data2)
    assert response2.status_code == 200
    job_id2 = response2.json()["job_id"]
    
    # Wait for jobs to be processed
    await asyncio.sleep(2)
    
    # Test listing all jobs
    response = test_client.get("/plugins/v1/gis-export/list")
    assert response.status_code == 200
    all_jobs = response.json()
    assert len(all_jobs) >= 2
    
    # Verify our test jobs are in the list
    job_ids = [job["job_id"] for job in all_jobs]
    assert str(job_id1) in job_ids
    assert str(job_id2) in job_ids
    
    # Test filtering by format
    response = test_client.get("/plugins/v1/gis-export/list?format=GeoJSON")
    assert response.status_code == 200
    filtered_jobs = response.json()
    
    # Verify filter worked
    filtered_job_ids = [job["job_id"] for job in filtered_jobs]
    assert str(job_id1) in filtered_job_ids
    assert str(job_id2) not in filtered_job_ids