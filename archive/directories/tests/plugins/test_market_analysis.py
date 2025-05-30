"""
Integration tests for the market analysis plugin.

This module contains tests for the market analysis plugin's API endpoints,
covering job creation, status checks, and result retrieval.
"""

import pytest
import pytest_asyncio
import uuid
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select

from terrafusion_sync.app import app
from terrafusion_sync.database import engine
from terrafusion_sync.core_models import MarketAnalysisJob


# Create a test client for the FastAPI app
client = TestClient(app)

# Test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_ANALYSIS_TYPE = "price_trend_by_zip"
TEST_PARAMETERS = {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "zip_codes": ["90210", "90211"],
    "property_types": ["residential"]
}


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide an async database session for tests."""
    async with AsyncSession(engine) as session:
        yield session
        # Cleanup - rollback any pending transactions
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def cleanup_test_jobs(db_session):
    """
    Clean up test market analysis jobs before and after tests.
    
    This fixture deletes any test jobs created during testing
    to ensure tests are isolated.
    """
    # Setup: Clean any existing test jobs
    stmt = delete(MarketAnalysisJob).where(
        (MarketAnalysisJob.county_id == TEST_COUNTY_ID) &
        (MarketAnalysisJob.analysis_type == TEST_ANALYSIS_TYPE)
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
async def test_run_market_analysis(cleanup_test_jobs):
    """Test running a market analysis job."""
    # Prepare request data
    analysis_data = {
        "county_id": TEST_COUNTY_ID,
        "analysis_type": TEST_ANALYSIS_TYPE,
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to run a market analysis
    response = client.post("/plugins/v1/market-analysis/run", json=analysis_data)
    
    # Check status code and response structure
    assert response.status_code == 202, f"Failed to run market analysis: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert "job_id" in data
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["analysis_type"] == TEST_ANALYSIS_TYPE
    assert data["status"] == "PENDING"
    
    # Save job_id for later tests
    job_id = data["job_id"]
    
    # Wait a moment and check status
    time.sleep(3)
    
    # Check status endpoint
    response = client.get(f"/plugins/v1/market-analysis/status/{job_id}")
    assert response.status_code == 200
    status_data = response.json()
    
    # Verify the job is completed or at least not pending anymore
    assert status_data["status"] in ["RUNNING", "COMPLETED"], f"Unexpected status: {status_data['status']}"
    
    # Wait a bit more if needed for completion
    if status_data["status"] == "RUNNING":
        time.sleep(3)
        response = client.get(f"/plugins/v1/market-analysis/status/{job_id}")
        assert response.status_code == 200
        status_data = response.json()
        assert status_data["status"] == "COMPLETED", f"Job did not complete in expected time, status: {status_data['status']}"
    
    # Check results endpoint
    response = client.get(f"/plugins/v1/market-analysis/results/{job_id}")
    assert response.status_code == 200
    results_data = response.json()
    
    # Verify results structure
    assert "result" in results_data
    assert "result_summary" in results_data["result"]
    assert "key_finding" in results_data["result"]["result_summary"]
    assert "trends" in results_data["result"]
    assert len(results_data["result"]["trends"]) > 0
    
    return job_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_job_failure_scenario(cleanup_test_jobs):
    """Test market analysis job failure handling."""
    # Prepare request data with a type known to fail
    analysis_data = {
        "county_id": TEST_COUNTY_ID,
        "analysis_type": "FAILING_ANALYSIS_SIM",
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to run a failing market analysis
    response = client.post("/plugins/v1/market-analysis/run", json=analysis_data)
    
    # Check status code and response structure
    assert response.status_code == 202, f"Failed to create job: {response.text}"
    data = response.json()
    
    # Save job_id
    job_id = data["job_id"]
    
    # Wait a moment for processing
    time.sleep(3)
    
    # Check status endpoint
    response = client.get(f"/plugins/v1/market-analysis/status/{job_id}")
    assert response.status_code == 200
    status_data = response.json()
    
    # Verify the job failed as expected
    assert status_data["status"] == "FAILED", f"Job should have failed but status is: {status_data['status']}"
    assert "failure" in status_data["message"].lower() or "error" in status_data["message"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_market_analysis_by_id(cleanup_test_jobs):
    """Test retrieving a specific market analysis job by ID."""
    # First create a job
    job_id = await test_run_market_analysis(cleanup_test_jobs)
    
    # Now retrieve it
    response = client.get(f"/plugins/v1/market-analysis/status/{job_id}")
    
    # Check status code and response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response fields
    assert data["job_id"] == job_id
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["analysis_type"] == TEST_ANALYSIS_TYPE


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_market_analysis_jobs(cleanup_test_jobs):
    """Test listing market analysis jobs with filters."""
    # Create a test job
    job_id = await test_run_market_analysis(cleanup_test_jobs)
    
    # Test basic listing
    response = client.get("/plugins/v1/market-analysis/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(job["job_id"] == job_id for job in data)
    
    # Test filtering by county_id
    response = client.get(f"/plugins/v1/market-analysis/list?county_id={TEST_COUNTY_ID}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(job["job_id"] == job_id for job in data)
    
    # Test filtering by analysis_type
    response = client.get(f"/plugins/v1/market-analysis/list?analysis_type={TEST_ANALYSIS_TYPE}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(job["job_id"] == job_id for job in data)
    
    # Test filtering by status
    response = client.get("/plugins/v1/market-analysis/list?status=COMPLETED")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(job["job_id"] == job_id for job in data)
    
    # Test combination of filters
    response = client.get(
        f"/plugins/v1/market-analysis/list?county_id={TEST_COUNTY_ID}&analysis_type={TEST_ANALYSIS_TYPE}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(job["job_id"] == job_id for job in data)