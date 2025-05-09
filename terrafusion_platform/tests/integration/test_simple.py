"""
Simple integration test to verify our test setup works properly.

This test checks if we can connect to the database and SyncService.
"""

import pytest
from fastapi.testclient import TestClient


def test_sync_client_works(sync_client):
    """Test that the sync client can connect to the SyncService."""
    response = sync_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.asyncio
async def test_db_session_works(db_session):
    """Test that the db_session fixture can connect to the database."""
    # Just test that the session is created and basic methods work
    result = await db_session.execute("SELECT 1")
    row = result.scalar_one()
    assert row == 1