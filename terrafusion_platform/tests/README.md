# TerraFusion Platform Testing Framework

This directory contains the testing infrastructure for the TerraFusion Platform.

## Directory Structure

- `integration/` - Integration tests for the platform
  - `conftest.py` - Pytest fixtures for integration tests
  - `test_property_endpoints.py` - Tests for property API endpoints
  - `test_valuation_endpoints.py` - Tests for valuation API endpoints

## Running Tests

You can run the tests using the `run_integration_tests.py` script in the project root:

```bash
# Run all integration tests
./run_integration_tests.py

# Run tests with verbose output
./run_integration_tests.py --verbose

# Run specific tests matching a keyword
./run_integration_tests.py --keyword "property"

# Run a specific test file
./run_integration_tests.py --path terrafusion_platform/tests/integration/test_property_endpoints.py
```

## Test Database Configuration

The integration tests require a test database. Configuration is managed through the `.env` file:

```
# Main database URL (used by application)
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname

# Test database URL (used by tests)
TEST_DATABASE_URL=postgresql+asyncpg://user:password@host/dbname_test

# Set to 'True' to see SQL echo in tests
SQLALCHEMY_TEST_ECHO=False
```

The `run_integration_tests.py` script will create or update the `.env` file with the necessary test database configuration if it doesn't exist.

## Test Fixtures

The `conftest.py` file provides several useful pytest fixtures:

- `pg_engine` - SQLAlchemy engine connected to the test database
- `db_session` - SQLAlchemy session for database operations within tests
- `create_property_operational` - Factory function to create property records
- `sync_client` - FastAPI TestClient for making API requests
- `alembic_cfg_obj` - Alembic configuration for database migrations

## Transaction Isolation

Tests use transaction isolation to prevent data from different tests from interfering with each other. Each test runs in its own transaction, which is rolled back after the test completes. This ensures a clean state for each test without having to recreate the database schema.

## Writing New Tests

To write new integration tests:

1. Create a new file in the `integration/` directory with a `test_` prefix
2. Import the necessary fixtures from `conftest.py`
3. Use the `@pytest.mark.asyncio` decorator for asynchronous tests
4. Follow the existing test patterns for database operations and API requests

Example:

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

@pytest.mark.asyncio
async def test_example(sync_client: TestClient, db_session: AsyncSession):
    # Your test code here
    response = sync_client.get("/some-endpoint")
    assert response.status_code == 200
```

## Alembic Integration

The test infrastructure automatically runs Alembic migrations before tests to ensure the test database has the correct schema. The Alembic configuration is overridden to use the test database instead of the main database.

To create new migrations, use the Alembic CLI:

```bash
# Generate a new migration (in terrafusion_sync directory)
cd terrafusion_sync
alembic revision -m "description_of_changes" --autogenerate
```

To manually apply migrations:

```bash
# Apply migrations (in terrafusion_sync directory)
cd terrafusion_sync
python run_migrations.py
```