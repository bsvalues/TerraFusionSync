"""
Integration tests for property valuation endpoints in the TerraFusion SyncService.

These tests verify that the valuation API endpoints work correctly with the
database and return the expected responses.
"""
import pytest
import uuid
import time
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

# Import the models for type hints
try:
    from terrafusion_sync.core_models import PropertyOperational, ValuationJob
except ImportError:
    pass  # The import should work in normal execution, but we handle failure gracefully


@pytest.mark.asyncio
async def test_create_valuation_job(
    sync_client: TestClient,
    create_property_operational: Callable,
    db_session: AsyncSession
):
    """
    Test creating a new valuation job through the API.
    
    This test:
    1. Creates a test property in the database
    2. Makes an API request to start a valuation job for this property
    3. Verifies the job is created properly
    """
    # Step 1: Create a test property with a known ID
    test_prop_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"
    test_county = "test_county"
    
    # Use the fixture to create a property in the database
    test_prop = await create_property_operational(
        property_id=test_prop_id,
        county_id=test_county,
        current_assessed_value_total=350000.0,
        year_built=2015
    )
    
    # Step 2: Request to create a valuation job through the API
    payload = {
        "property_id": test_prop_id,
        "county_id": test_county,
        "valuation_method_hint": "sales_comparison"
    }
    
    response = sync_client.post("/valuation/jobs", json=payload)
    
    # Step 3: Verify the response
    assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}: {response.text}"
    
    # Check the response data
    job_data = response.json()
    assert job_data["property_id"] == test_prop_id
    assert job_data["county_id"] == test_county
    assert job_data["status"] == "PENDING" or job_data["status"] == "SUBMITTED"
    assert "job_id" in job_data


@pytest.mark.asyncio
async def test_get_valuation_job_by_id(
    sync_client: TestClient,
    create_property_operational: Callable,
    db_session: AsyncSession
):
    """
    Test retrieving a specific valuation job by ID.
    
    This test:
    1. Creates a test property in the database
    2. Creates a valuation job for the property
    3. Retrieves the job by ID and verifies its details
    """
    # Step 1: Create a test property
    test_prop_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"
    test_county = "test_county"
    
    await create_property_operational(
        property_id=test_prop_id,
        county_id=test_county
    )
    
    # Step 2: Create a valuation job
    payload = {
        "property_id": test_prop_id,
        "county_id": test_county
    }
    
    create_response = sync_client.post("/valuation/jobs", json=payload)
    assert create_response.status_code == 201
    
    job_data = create_response.json()
    job_id = job_data["job_id"]
    
    # Step 3: Retrieve the job by ID
    response = sync_client.get(f"/valuation/jobs/{job_id}")
    
    # Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Check the response data
    retrieved_job = response.json()
    assert retrieved_job["job_id"] == job_id
    assert retrieved_job["property_id"] == test_prop_id
    assert retrieved_job["county_id"] == test_county


@pytest.mark.asyncio
async def test_get_valuation_jobs_by_property(
    sync_client: TestClient,
    create_property_operational: Callable,
    db_session: AsyncSession
):
    """
    Test retrieving all valuation jobs for a specific property.
    
    This test:
    1. Creates a test property in the database
    2. Creates multiple valuation jobs for the property
    3. Retrieves all jobs for the property and verifies the results
    """
    # Step 1: Create a test property
    test_prop_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"
    test_county = "test_county"
    
    await create_property_operational(
        property_id=test_prop_id,
        county_id=test_county
    )
    
    # Step 2: Create multiple valuation jobs with different methods
    methods = ["sales_comparison", "income_approach", "cost_approach"]
    job_ids = []
    
    for method in methods:
        payload = {
            "property_id": test_prop_id,
            "county_id": test_county,
            "valuation_method_hint": method
        }
        
        response = sync_client.post("/valuation/jobs", json=payload)
        assert response.status_code == 201
        
        job_ids.append(response.json()["job_id"])
        
        # Add a small delay to ensure jobs have different timestamps
        time.sleep(0.1)
    
    # Step 3: Retrieve all jobs for this property
    response = sync_client.get(f"/valuation/jobs?property_id={test_prop_id}")
    
    # Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Check the response data
    jobs_data = response.json()
    assert len(jobs_data) >= len(methods), f"Expected at least {len(methods)} jobs, got {len(jobs_data)}"
    
    # Verify all our job IDs are in the results
    returned_ids = [job["job_id"] for job in jobs_data]
    for job_id in job_ids:
        assert job_id in returned_ids, f"Job {job_id} not found in response"