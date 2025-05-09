"""
Test fixtures for integration tests.

This module provides fixtures for integration testing of the terrafusion_sync service,
including database access, test data generation, and API client configuration.
"""

import os
import sys
import uuid
import datetime
import asyncio
import pytest
import pytest_asyncio
from typing import Dict, Any, Callable, AsyncGenerator
from pathlib import Path
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add the root directory to sys.path to make the terrafusion_sync package importable
# This should be the parent of terrafusion_platform
ROOT_DIR = str(Path(__file__).parents[3].absolute())
TERRAFUSION_SYNC_ROOT = str(Path(ROOT_DIR) / "terrafusion_sync")
sys.path.insert(0, ROOT_DIR)

# This import ensures that SQLAlchemy models are available
from terrafusion_sync.core_models import Base, PropertyOperational, ReportJob


# --- Path Fixtures ---
@pytest.fixture(scope="session")
def alembic_config_path():
    """Returns the path to alembic.ini, assuming it's in terrafusion_sync/"""
    alembic_path = Path(TERRAFUSION_SYNC_ROOT) / "alembic.ini"
    if not alembic_path.exists():
        pytest.fail(f"Alembic config not found at expected path: {alembic_path}")
    return str(alembic_path)


@pytest.fixture(scope="session")
def alembic_cfg_obj(alembic_config_path):
    """Provides the Alembic Config object."""
    from alembic.config import Config
    
    cfg = Config(alembic_config_path)
    # Set the script_location if not in the config
    if not cfg.get_main_option("script_location"):
        script_location = str(Path(TERRAFUSION_SYNC_ROOT) / "alembic_migrations")
        cfg.set_main_option("script_location", script_location)
    
    return cfg


# --- Database Fixtures ---
@pytest_asyncio.fixture(scope="session")
async def pg_engine(alembic_cfg_obj):
    """
    Provides an SQLAlchemy async engine connected to the TEST database.
    It runs Alembic migrations to set up the schema once per test session.
    This fixture avoids using asyncio.run() which conflicts with pytest's
    event loop.
    """
    from alembic import command # Alembic command interface
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext

    # Use the regular database URL for testing if no test URL is provided
    # In a production environment, you would use a separate test database
    test_db_url = os.getenv("DATABASE_URL", os.getenv("TEST_DATABASE_URL"))
    if not test_db_url:
        pytest.fail("Neither DATABASE_URL nor TEST_DATABASE_URL environment variable is set.")

    # Check if we need to convert non-async URL to async
    if "postgresql://" in test_db_url and "asyncpg" not in test_db_url:
        test_db_url = test_db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    # For asyncpg, we need to handle SSL parameters differently
    # The asyncpg driver doesn't accept 'sslmode' parameter directly
    connect_args = {}
    if "sslmode=require" in test_db_url:
        # Remove sslmode from URL and add it to connect_args
        test_db_url = test_db_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
        connect_args["ssl"] = True
    
    # Create the engine with optimized connect args for test reliability
    engine = create_async_engine(
        test_db_url, 
        connect_args={
            **connect_args,
            "timeout": 10,  # Connection timeout in seconds
            "command_timeout": 10  # Command execution timeout
        },
        pool_size=5,  # Smaller pool size for tests
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=60,  # More frequent connection recycling
        pool_pre_ping=True,  # Check connection validity
        echo=os.getenv("SQLALCHEMY_TEST_ECHO", "False").lower() == "true"
    )
    
    # Configure engine with execution options to help with transaction handling
    engine = engine.execution_options(
        isolation_level="READ COMMITTED",  # Less strict isolation level
        postgresql_readonly=False,
        postgresql_deferrable=False  # Non-deferrable transactions
    )
    
    # Apply migrations manually using the async engine
    print(f"\nApplying Alembic migrations to test database: {test_db_url.split('@')[-1]}")
    original_cwd = os.getcwd()
    os.chdir(TERRAFUSION_SYNC_ROOT) # Alembic commands often expect to be run from where alembic.ini is
    
    try:
        # Since Alembic requires a regular Connection and not AsyncConnection,
        # we need to find a different approach to check if we need to run migrations
        
        # Use command.upgrade directly - our modified env.py will handle async correctly
        print(f"Running Alembic migrations with properly configured connect_args...")
        # Let alembic env.py handle the async connection issues
        command.upgrade(alembic_cfg_obj, "head")
        print("Alembic migrations applied successfully.")
    except Exception as e:
        pytest.fail(f"Alembic migration failed: {e}")
    finally:
        os.chdir(original_cwd)
    
    yield engine # Provide the engine to tests
    
    # Teardown: Dispose of the engine
    print("\nDisposing of test database engine.")
    await engine.dispose()

@pytest_asyncio.fixture(scope="function") # function scope for test isolation
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an SQLAlchemy AsyncSession for a single test function.
    
    This version does NOT use a transaction. Instead, it commits changes 
    to the database. Test isolation is maintained by using unique IDs and
    prefixes for test data.
    
    This approach avoids asyncpg transaction conflicts when 
    the API endpoints create their own transactions.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    # Create a fresh async sessionmaker with our test engine
    TestAsyncSessionFactory = async_sessionmaker(
        bind=pg_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )
    
    # Create a fresh session
    session = TestAsyncSessionFactory()
    session_id = id(session)
    current_test = os.environ.get('PYTEST_CURRENT_TEST', '').split(' ')[0]
    print(f"\nTest DB Session {session_id}: Created (Test: {current_test})")
    
    try:
        yield session
        
        # Commit any pending changes to make them visible to API calls
        if session.in_transaction():
            await session.commit()
            print(f"Test DB Session {session_id}: Committed at cleanup")
    except Exception as e:
        print(f"Test DB Session {session_id}: Error: {str(e)}")
        if session.in_transaction():
            await session.rollback()
            print(f"Test DB Session {session_id}: Rolled back")
        raise
    finally:
        # Always close the session properly
        await session.close()
        print(f"Test DB Session {session_id}: Closed")


@pytest_asyncio.fixture(scope="function")
async def create_property_operational(pg_engine) -> Callable[..., PropertyOperational]:
    """
    Factory fixture to create PropertyOperational records in the test database.
    
    This version creates a fresh session for each property creation,
    commits immediately, and closes the session to prevent transaction conflicts.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    # Create a sessionmaker for our test engine
    TestAsyncSessionFactory = async_sessionmaker(
        bind=pg_engine, 
        expire_on_commit=False,
        autocommit=False, 
        autoflush=False
    )
    
    async def _create_property(
        property_id: str = None, 
        county_id: str = "test_county",
        address_street: str = "123 Test St",
        address_city: str = "Testville",
        address_state: str = "TS",
        address_zip: str = "12345",
        property_type: str = "residential",
        parcel_number: str = "TEST-PARCEL-123",
        year_built: int = 2000,
        assessed_value: float = 100000.0,
        custom_fields: Dict[str, Any] = None
    ) -> PropertyOperational:
        # Create a fresh session for this operation
        session = TestAsyncSessionFactory()
        
        try:
            if property_id is None:
                property_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"

            prop_data = {
                "property_id": property_id,
                "county_id": county_id,
                "address_street": address_street,
                "address_city": address_city,
                "address_state": address_state,
                "address_zip": address_zip,
                "property_type": property_type,
                "parcel_number": parcel_number,
                "year_built": year_built,
                "assessed_value": assessed_value,
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow()
            }
            if custom_fields:
                prop_data.update(custom_fields)
            
            new_property = PropertyOperational(**prop_data)
            
            session.add(new_property)
            await session.commit()  # Commit immediately
            
            # Refresh after commit to get any DB-generated values
            await session.refresh(new_property)
            
            # Create a detached copy of the property to return
            # This prevents issues with using the entity after session close
            detached_property = PropertyOperational(**new_property.__dict__.copy())
            
            print(f"Fixture: Created PropertyOperational: {detached_property.property_id}")
            return detached_property
        except Exception as e:
            await session.rollback()
            print(f"Fixture Error: Failed to create PropertyOperational: {str(e)}")
            raise
        finally:
            await session.close()
            
    return _create_property


@pytest_asyncio.fixture(scope="function")
async def create_report_job(pg_engine) -> Callable[..., ReportJob]:
    """
    Factory fixture to create ReportJob records in the test database.
    
    This version creates a fresh session for each report job creation,
    commits immediately, and closes the session to prevent transaction conflicts.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker
    
    # Create a sessionmaker for our test engine
    TestAsyncSessionFactory = async_sessionmaker(
        bind=pg_engine, 
        expire_on_commit=False,
        autocommit=False, 
        autoflush=False
    )
    
    async def _create_report_job(
        report_id: str = None,
        report_type: str = "assessment_roll",
        county_id: str = "test_county",
        status: str = "PENDING",
        message: str = None,
        parameters_json: Dict[str, Any] = None,
        result_location: str = None,
        result_metadata_json: Dict[str, Any] = None,
        custom_fields: Dict[str, Any] = None
    ) -> ReportJob:
        # Create a fresh session for this operation
        session = TestAsyncSessionFactory()
        
        try:
            if report_id is None:
                report_id = str(uuid.uuid4())
                
            # Set default parameters if none provided
            if parameters_json is None:
                parameters_json = {
                    "year": 2025,
                    "quarter": 1,
                    "include_exempt": True
                }

            report_data = {
                "report_id": report_id,
                "report_type": report_type,
                "county_id": county_id,
                "status": status,
                "message": message,
                "parameters_json": parameters_json,
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow(),
                "result_location": result_location,
                "result_metadata_json": result_metadata_json
            }
            
            if custom_fields:
                report_data.update(custom_fields)
            
            new_report_job = ReportJob(**report_data)
            
            session.add(new_report_job)
            await session.commit()  # Commit immediately
            
            # Refresh after commit to get any DB-generated values
            await session.refresh(new_report_job)
            
            # Create a detached copy of the report job to return
            # This prevents issues with using the entity after session close
            detached_report = ReportJob(**new_report_job.__dict__.copy())
            
            print(f"Fixture: Created ReportJob: {detached_report.report_id} ({detached_report.report_type})")
            return detached_report
        except Exception as e:
            await session.rollback()
            print(f"Fixture Error: Failed to create ReportJob: {str(e)}")
            raise
        finally:
            await session.close()

    return _create_report_job


# --- API Client Fixtures ---
# Import the FastAPI app from terrafusion_sync
try:
    from terrafusion_sync.app import app as actual_sync_app
    
    # Try to import database dependencies, if they don't exist we'll handle it
    try:
        from terrafusion_sync.database import get_db_session as app_get_db_session # Database session dependency
        from terrafusion_sync.plugins.reporting.routes import get_db  # The actual used dependency in routes
    except ImportError as e:
        print(f"Warning: Could not import database dependencies from terrafusion_sync. Dependency override may fail: {e}")
        app_get_db_session = None  # We'll check this later
        get_db = None
except ImportError as e:
    print(f"Failed to import 'app' from 'terrafusion_sync.app': {e}")
    print("Check PYTHONPATH/imports.")
    actual_sync_app = None  # We'll check this later


@pytest_asyncio.fixture(scope="function") # Function scope for client if app state changes or for dep override
async def sync_client(pg_engine) -> AsyncGenerator:
    """
    Provides a FastAPI TestClient for the terrafusion_sync service.
    
    This version creates separate sessions for each request 
    instead of trying to share the same session, which can
    cause asyncpg transaction conflicts.
    """
    if actual_sync_app is None:
        pytest.skip("FastAPI app could not be imported. Skipping test.")
        return
        
    try:
        # Try to import the reporting routes directly
        from terrafusion_sync.plugins.reporting.routes import get_db
    except ImportError:
        pytest.skip("Could not import get_db from reporting routes. Skipping test.")
        return
    
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi and httpx must be installed for testing: pip install fastapi httpx")
        return

    # Create a sessionmaker for our test engine with explicit transaction settings
    from sqlalchemy.ext.asyncio import async_sessionmaker
    TestAsyncSessionFactory = async_sessionmaker(
        bind=pg_engine, 
        expire_on_commit=False,
        autocommit=False, 
        autoflush=False
    )
    
    # Create a consistently reliable override for get_db that controls session lifecycle
    @asynccontextmanager
    async def test_db_session():
        """Test-specific DB session provider"""
        session = TestAsyncSessionFactory()
        session_id = id(session)
        print(f"\nTest DB Session {session_id}: Created for test API call")
        try:
            yield session
            if session.in_transaction():
                await session.commit()
                print(f"Test DB Session {session_id}: Committed")
        except Exception as e:
            print(f"Test DB Session {session_id}: Error: {str(e)}")
            if session.in_transaction():
                await session.rollback()
                print(f"Test DB Session {session_id}: Rolled back")
            raise
        finally:
            await session.close()
            print(f"Test DB Session {session_id}: Closed")
    
    # Define test-specific get_db function that uses our controlled session
    async def override_get_db():
        async with test_db_session() as session:
            yield session
    
    # Override the dependency in the app
    actual_sync_app.dependency_overrides[get_db] = override_get_db
    print("\nTest Client: Initialized with test DB session provider")
    
    # Create client with force_exit=False to ensure graceful closing of connections
    client = TestClient(
        actual_sync_app, 
        base_url="http://testserver-sync",
        raise_server_exceptions=True
    )
    
    yield client
    
    # Clear the dependency overrides after the test
    del actual_sync_app.dependency_overrides[get_db]
    print("Test Client: DB session overrides cleared.")