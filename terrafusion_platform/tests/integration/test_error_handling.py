"""
Integration tests for error handling in the reporting API.

These tests verify that the API endpoints handle error cases correctly.
"""

import asyncio
import pytest
import uuid
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from typing import Dict, Any, List

@pytest.mark.asyncio
@pytest.mark.integration
async def test_reporting_error_handling(
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
    
    # Test 5: Test status and results endpoints with non-existent ID
    print(f"Testing status endpoint with non-existent ID: {fake_id}")
    status_response = sync_client.get(f"/plugins/v1/reporting/status/{fake_id}")
    assert status_response.status_code == 404
    print(f"Got expected 404 response from status endpoint")
    
    print(f"Testing results endpoint with non-existent ID: {fake_id}")
    results_response = sync_client.get(f"/plugins/v1/reporting/results/{fake_id}")
    assert results_response.status_code == 404
    print(f"Got expected 404 response from results endpoint")
    
    print("All error handling tests completed successfully")