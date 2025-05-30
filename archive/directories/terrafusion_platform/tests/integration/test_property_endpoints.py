"""
Integration tests for property-related endpoints in the TerraFusion SyncService.

These tests verify that the property API endpoints work correctly with the
database and return the expected responses.
"""
import pytest
import uuid
from typing import Callable, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

# Import the PropertyOperational model for type hints
try:
    from terrafusion_sync.core_models import PropertyOperational
except ImportError:
    pass  # The import should work in normal execution, but we handle failure gracefully


@pytest.mark.asyncio
async def test_get_property_by_id(
    sync_client: TestClient,
    create_property_operational: Callable,
    db_session: AsyncSession
):
    """
    Test retrieving a property by ID through the API.
    
    This test:
    1. Creates a test property in the database
    2. Makes an API request to fetch the property by ID
    3. Verifies the response contains the correct property data
    """
    # Step 1: Create a test property with a known ID
    test_prop_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"
    test_county = "test_county"
    test_address = "456 Test Avenue, Testville, TS 54321"
    test_value = 250000.0
    
    # Use the fixture to create a property in the database
    test_prop = await create_property_operational(
        property_id=test_prop_id,
        county_id=test_county,
        situs_address_full=test_address,
        current_assessed_value_total=test_value
    )
    
    # Step 2: Request the property through the API
    response = sync_client.get(f"/properties/{test_prop_id}")
    
    # Step 3: Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Check the response data
    property_data = response.json()
    assert property_data["property_id"] == test_prop_id
    assert property_data["county_id"] == test_county
    assert property_data["situs_address_full"] == test_address
    assert property_data["current_assessed_value_total"] == test_value


@pytest.mark.asyncio
async def test_get_properties_list(
    sync_client: TestClient,
    create_property_operational: Callable,
    db_session: AsyncSession
):
    """
    Test retrieving a list of properties through the API.
    
    This test:
    1. Creates multiple test properties in the database
    2. Makes an API request to fetch all properties
    3. Verifies the response contains the expected properties
    """
    # Step 1: Create multiple test properties
    test_county = "test_county_list"
    test_props = []
    
    # Create 3 test properties
    for i in range(3):
        prop = await create_property_operational(
            county_id=test_county,
            current_assessed_value_total=100000.0 + (i * 50000)
        )
        test_props.append(prop)
    
    # Step 2: Request properties through the API with county filter
    response = sync_client.get(f"/properties?county_id={test_county}")
    
    # Step 3: Verify the response
    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}: {response.text}"
    
    # Check the response data
    properties_data = response.json()
    
    # Verify we got at least the number of properties we created
    assert len(properties_data) >= len(test_props), "Not all created properties were returned"
    
    # Verify all our test property IDs are in the results
    returned_ids = [prop["property_id"] for prop in properties_data]
    for test_prop in test_props:
        assert test_prop.property_id in returned_ids, f"Property {test_prop.property_id} not found in response"


@pytest.mark.asyncio
async def test_property_not_found(sync_client: TestClient):
    """
    Test the behavior when requesting a non-existent property.
    
    This test:
    1. Makes an API request for a property with a non-existent ID
    2. Verifies the API returns a 404 Not Found response
    """
    # Generate a random property ID that shouldn't exist
    non_existent_id = f"NONEXISTENT_{uuid.uuid4().hex}"
    
    # Request the property through the API
    response = sync_client.get(f"/properties/{non_existent_id}")
    
    # Verify the response is a 404 Not Found
    assert response.status_code == 404, f"Expected 404 Not Found, got {response.status_code}: {response.text}"
    
    # Check the error details in the response
    error_data = response.json()
    assert "detail" in error_data, "Error response missing 'detail' field"
    assert "not found" in error_data["detail"].lower(), "Error message doesn't indicate property not found"