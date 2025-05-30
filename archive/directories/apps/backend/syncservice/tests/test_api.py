"""
Tests for the SyncService API.

This module contains tests to verify the functionality of the SyncService API endpoints.
"""

import asyncio
import datetime
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient

from syncservice.api.health import router as health_router
from syncservice.api.sync import router as sync_router


@pytest.fixture
def app():
    """Fixture to create a FastAPI test app."""
    app = FastAPI()
    app.include_router(sync_router, prefix="/sync")
    app.include_router(health_router, prefix="/health")
    return app


@pytest.fixture
def client(app):
    """Fixture to create a test client."""
    return TestClient(app)


def test_health_live(client):
    """Test the liveness probe endpoint."""
    response = client.get("/health/live")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "up"
    assert "uptime_seconds" in data
    assert "started_at" in data


def test_health_ready(client):
    """Test the readiness probe endpoint."""
    # Mock the dependency checks
    with patch('syncservice.api.health.check_source_connection', AsyncMock(return_value=True)), \
         patch('syncservice.api.health.check_target_connection', AsyncMock(return_value=True)), \
         patch('syncservice.api.health.check_nats_connection', AsyncMock(return_value=True)):
        
        response = client.get("/health/ready")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["source_database"] == "ok"
        assert data["dependencies"]["target_database"] == "ok"
        assert data["dependencies"]["message_bus"] == "ok"


def test_health_ready_not_ready(client):
    """Test the readiness probe endpoint when dependencies are not available."""
    # Mock the dependency checks
    with patch('syncservice.api.health.check_source_connection', AsyncMock(return_value=False)), \
         patch('syncservice.api.health.check_target_connection', AsyncMock(return_value=True)), \
         patch('syncservice.api.health.check_nats_connection', AsyncMock(return_value=True)):
        
        response = client.get("/health/ready")
        
        # Verify the response
        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["dependencies"]["source_database"] == "error"
        assert data["detail"]["dependencies"]["target_database"] == "ok"
        assert data["detail"]["dependencies"]["message_bus"] == "ok"


def test_health_status(client):
    """Test the detailed health status endpoint."""
    # Mock the dependency checks
    with patch('syncservice.api.health.check_source_connection', AsyncMock(return_value=True)), \
         patch('syncservice.api.health.check_target_connection', AsyncMock(return_value=True)), \
         patch('syncservice.api.health.check_nats_connection', AsyncMock(return_value=True)):
        
        response = client.get("/health/status")
        
        # Verify the response
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "available"
        assert "uptime_seconds" in data
        assert "started_at" in data
        assert data["dependencies"]["source_database"]["status"] == "ok"
        assert data["dependencies"]["target_database"]["status"] == "ok"
        assert data["dependencies"]["message_bus"]["status"] == "ok"


def test_full_sync(client):
    """Test the full sync endpoint."""
    # Mock the dependencies check
    with patch('syncservice.api.sync.check_dependencies', AsyncMock(return_value=True)), \
         patch('syncservice.api.sync.publish_event', AsyncMock(return_value=True)), \
         patch('syncservice.api.sync._run_full_sync', AsyncMock()):
        
        # Call the endpoint
        response = client.post("/sync/full")
        
        # Verify the response
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["details"]["status"] == "queued"


def test_incremental_sync(client):
    """Test the incremental sync endpoint."""
    # Mock the dependencies check
    with patch('syncservice.api.sync.check_dependencies', AsyncMock(return_value=True)), \
         patch('syncservice.api.sync.publish_event', AsyncMock(return_value=True)), \
         patch('syncservice.api.sync._run_incremental_sync', AsyncMock()):
        
        # Create request data
        request_data = {
            "since": (datetime.datetime.utcnow() - datetime.timedelta(hours=2)).isoformat(),
            "limit": 500,
            "options": {
                "include_deleted": True
            }
        }
        
        # Call the endpoint
        response = client.post("/sync/incremental", json=request_data)
        
        # Verify the response
        assert response.status_code == 202
        data = response.json()
        assert data["success"] is True
        assert data["details"]["status"] == "queued"
        assert "since" in data["details"]


def test_sync_status(client):
    """Test the sync status endpoint."""
    # Generate a random operation ID
    operation_id = str(uuid.uuid4())
    
    # Call the endpoint
    response = client.get(f"/sync/status/{operation_id}")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["operation_id"] == operation_id
    assert "status" in data


@pytest.mark.asyncio
async def test_run_full_sync():
    """Test the _run_full_sync background task."""
    # Create mocks
    orchestrator = AsyncMock()
    orchestrator.run_sync_pipeline = AsyncMock(return_value={
        "success": True,
        "count": 100,
        "details": {"valid_count": 90, "invalid_count": 10}
    })
    
    detector = MagicMock()
    transformer = MagicMock()
    validator = MagicMock()
    
    # Mock the publish event function
    with patch('syncservice.api.sync.publish_event', AsyncMock(return_value=True)):
        # Call the function
        from syncservice.api.sync import _run_full_sync
        await _run_full_sync(
            orchestrator=orchestrator,
            detector=detector,
            transformer=transformer,
            validator=validator,
            operation_id="test-operation"
        )
        
        # Verify the orchestrator was called
        orchestrator.run_sync_pipeline.assert_called_once()
        assert orchestrator.run_sync_pipeline.call_args[1]["is_full_sync"] is True


@pytest.mark.asyncio
async def test_run_incremental_sync():
    """Test the _run_incremental_sync background task."""
    # Create mocks
    orchestrator = AsyncMock()
    orchestrator.run_sync_pipeline = AsyncMock(return_value={
        "success": True,
        "count": 50,
        "details": {"valid_count": 45, "invalid_count": 5}
    })
    
    detector = MagicMock()
    transformer = MagicMock()
    validator = MagicMock()
    
    # Test timestamp
    since = datetime.datetime.utcnow() - datetime.timedelta(hours=2)
    
    # Mock the publish event function
    with patch('syncservice.api.sync.publish_event', AsyncMock(return_value=True)):
        # Call the function
        from syncservice.api.sync import _run_incremental_sync
        await _run_incremental_sync(
            orchestrator=orchestrator,
            detector=detector,
            transformer=transformer,
            validator=validator,
            operation_id="test-operation",
            since=since,
            limit=500
        )
        
        # Verify the orchestrator was called
        orchestrator.run_sync_pipeline.assert_called_once()
        assert orchestrator.run_sync_pipeline.call_args[1]["is_full_sync"] is False
        assert orchestrator.run_sync_pipeline.call_args[1]["since"] == since
