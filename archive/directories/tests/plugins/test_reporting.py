"""
Integration tests for the reporting plugin.

This module contains tests for the reporting plugin's API endpoints,
covering CRUD operations and result retrieval.
"""

import pytest
import pytest_asyncio
import uuid
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

# No need to manually register the mark as it's defined in pytest.ini

from terrafusion_sync.app import app
from terrafusion_sync.database import engine
from terrafusion_sync.core_models import ReportJob


# Create a test client for the FastAPI app
client = TestClient(app)

# Test data
TEST_COUNTY_ID = "TEST_COUNTY"
TEST_REPORT_TYPE = "test_integration_report"
TEST_PARAMETERS = {
    "test_param": "test_value",
    "year": 2025,
    "month": 5,
    "include_charts": True
}


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide an async database session for tests."""
    async with AsyncSession(engine) as session:
        yield session
        # Cleanup - rollback any pending transactions
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def cleanup_test_reports(db_session):
    """
    Clean up test reports before and after tests.
    
    This fixture deletes any test reports created during testing
    to ensure tests are isolated.
    """
    # Setup: Clean any existing test reports
    from sqlalchemy import delete
    
    stmt = delete(ReportJob).where(
        (ReportJob.county_id == TEST_COUNTY_ID) &
        (ReportJob.report_type == TEST_REPORT_TYPE)
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
async def test_create_report(cleanup_test_reports):
    """Test creating a new report job."""
    # Prepare request data
    report_data = {
        "county_id": TEST_COUNTY_ID,
        "report_type": TEST_REPORT_TYPE,
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to create a report
    response = client.post("/plugins/v1/reporting/reports", json=report_data)
    
    # Check status code and response structure
    assert response.status_code == 200, f"Failed to create report: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert "report_id" in data
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["report_type"] == TEST_REPORT_TYPE
    assert data["status"] == "PENDING"
    assert data["parameters"] == TEST_PARAMETERS
    
    # Save report_id for later tests
    report_id = data["report_id"]
    return report_id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_report_by_id(cleanup_test_reports):
    """Test retrieving a specific report by ID."""
    # First create a report
    report_id = await test_create_report(cleanup_test_reports)
    
    # Now retrieve it
    response = client.get(f"/plugins/v1/reporting/reports/{report_id}")
    
    # Check status code and response
    assert response.status_code == 200
    data = response.json()
    
    # Verify response fields
    assert data["report_id"] == report_id
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["report_type"] == TEST_REPORT_TYPE


@pytest.mark.asyncio
@pytest.mark.integration
async def test_list_reports_with_filters(cleanup_test_reports):
    """Test listing reports with various filters."""
    # First create a test report
    report_id = await test_create_report(cleanup_test_reports)
    
    # Test filtering by county_id
    response = client.get(f"/plugins/v1/reporting/reports?county_id={TEST_COUNTY_ID}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert any(item["report_id"] == report_id for item in data["items"])
    
    # Test filtering by report_type
    response = client.get(f"/plugins/v1/reporting/reports?report_type={TEST_REPORT_TYPE}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert any(item["report_id"] == report_id for item in data["items"])
    
    # Test filtering by status
    response = client.get("/plugins/v1/reporting/reports?status=PENDING")
    assert response.status_code == 200
    
    # Test filtering by created_after with a date in the past
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
    response = client.get(f"/plugins/v1/reporting/reports?created_after={yesterday}")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    
    # Test combination of filters
    response = client.get(
        f"/plugins/v1/reporting/reports?county_id={TEST_COUNTY_ID}&report_type={TEST_REPORT_TYPE}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert any(item["report_id"] == report_id for item in data["items"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_report_job(cleanup_test_reports):
    """Test running a report job and checking results."""
    # Prepare request data
    report_data = {
        "county_id": TEST_COUNTY_ID,
        "report_type": TEST_REPORT_TYPE,
        "parameters": TEST_PARAMETERS
    }
    
    # Make request to run a report
    response = client.post("/plugins/v1/reporting/run", json=report_data)
    
    # Check status code and response structure
    assert response.status_code == 202, f"Failed to run report: {response.text}"
    data = response.json()
    
    # Verify response fields
    assert "report_id" in data
    assert data["county_id"] == TEST_COUNTY_ID
    assert data["report_type"] == TEST_REPORT_TYPE
    
    # The report should be COMPLETED or at least not PENDING anymore
    assert data["status"] in ["RUNNING", "COMPLETED"], f"Unexpected status: {data['status']}"
    
    # If completed, check result info
    if data["status"] == "COMPLETED":
        assert data["result_location"] is not None
        assert data["result_metadata"] is not None
    
    # Save report_id
    report_id = data["report_id"]
    
    # Wait a moment and check status (in real test, might use polling with timeout)
    import time
    time.sleep(1)
    
    # Check status endpoint
    response = client.get(f"/plugins/v1/reporting/status/{report_id}")
    assert response.status_code == 200
    status_data = response.json()
    assert status_data["status"] in ["RUNNING", "COMPLETED"]
    
    # If COMPLETED, check results endpoint
    if status_data["status"] == "COMPLETED":
        response = client.get(f"/plugins/v1/reporting/results/{report_id}")
        assert response.status_code == 200
        results_data = response.json()
        assert "result_location" in results_data
        assert "result_metadata" in results_data
        assert "file_size_kb" in results_data["result_metadata"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_expire_stale_reports(db_session, cleanup_test_reports):
    """Test the stale reports expiration functionality."""
    # Create a test report directly in the database
    report_id = str(uuid.uuid4())
    stale_time = datetime.utcnow() - timedelta(minutes=45)  # 45 minutes ago
    
    # Create job with RUNNING status and backdated start time
    job = ReportJob(
        report_id=report_id,
        report_type=TEST_REPORT_TYPE,
        county_id=TEST_COUNTY_ID,
        status="RUNNING",
        parameters_json=TEST_PARAMETERS,
        created_at=stale_time,
        updated_at=stale_time,
        started_at=stale_time
    )
    
    db_session.add(job)
    await db_session.commit()
    
    # Import the expire_stale_reports function
    from terrafusion_sync.plugins.reporting.service import expire_stale_reports
    
    # Run the expire_stale_reports function
    count, expired_ids = await expire_stale_reports(db_session, timeout_minutes=30)
    
    # Verify that our report was expired
    assert count >= 1
    assert report_id in expired_ids
    
    # Verify the job's status and metadata
    from sqlalchemy import select
    query = select(ReportJob).where(ReportJob.report_id == report_id)
    result = await db_session.execute(query)
    updated_job = result.scalars().first()
    
    assert updated_job is not None
    assert updated_job.status == "FAILED"
    assert "timeout" in updated_job.message.lower()
    assert updated_job.result_metadata_json is not None
    assert updated_job.result_metadata_json.get("reason") == "timeout"