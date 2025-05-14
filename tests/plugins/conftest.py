"""
Shared test fixtures for plugin tests.

This module provides common fixtures that can be reused across plugin test modules.
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

from terrafusion_sync.app import app
from terrafusion_sync.database import engine


@pytest.fixture(scope="module")
def test_client():
    """Provide a test client for the FastAPI app."""
    return TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provide an async database session for tests."""
    async with AsyncSession(engine) as session:
        yield session
        # Cleanup - rollback any pending transactions
        await session.rollback()


@pytest.fixture(scope="function")
def sync_client():
    """Provide a synchronous test client for the FastAPI app."""
    return TestClient(app)