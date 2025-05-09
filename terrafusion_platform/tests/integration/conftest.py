import asyncio
import os
import pytest
import pytest_asyncio # For async fixtures
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator, Callable, Dict, Any
import uuid
import datetime # For datetime objects in model creation

# Add project root to sys.path to allow importing application modules
# This assumes conftest.py is in tests/integration/ and project root is two levels up.
PROJECT_ROOT_FOR_TESTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Terrafusion_sync might be directly at the project root, not under the platform directory
TERRAFUSION_SYNC_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT_FOR_TESTS, '..', 'terrafusion_sync'))
if not os.path.exists(TERRAFUSION_SYNC_ROOT):
    # As a fallback, try the platform subdirectory
    TERRAFUSION_SYNC_ROOT = os.path.join(PROJECT_ROOT_FOR_TESTS, 'terrafusion_sync')
    if not os.path.exists(TERRAFUSION_SYNC_ROOT):
        # If still not found, try the absolute path
        TERRAFUSION_SYNC_ROOT = '/home/runner/workspace/terrafusion_sync'
import sys
sys.path.insert(0, PROJECT_ROOT_FOR_TESTS)
sys.path.insert(0, TERRAFUSION_SYNC_ROOT) # Ensure terrafusion_sync modules can be found

# Import Base and specific models from terrafusion_sync.core_models
# This is critical for Alembic and for the create_property_operational fixture.
try:
    from terrafusion_sync.core_models import Base, PropertyOperational, ReportJob
    # If you have a central place for Base in terrafusion_sync (e.g. terrafusion_sync.database.Base)
    # ensure that's the one Alembic also uses.
except ImportError as e:
    print(f"CRITICAL ERROR in conftest.py: Could not import SQLAlchemy models from 'terrafusion_sync.core_models'. {e}")
    print(f"Ensure 'terrafusion_sync/core_models.py' exists, defines 'Base', 'PropertyOperational', and 'ReportJob'.")
    print(f"PROJECT_ROOT_FOR_TESTS: {PROJECT_ROOT_FOR_TESTS}")
    print(f"TERRAFUSION_SYNC_ROOT: {TERRAFUSION_SYNC_ROOT}")
    print(f"sys.path: {sys.path}")
    # pytest.exit("Failed to import core models for testing.", returncode=1) # Exit if models can't be loaded
    # For now, we'll let it proceed so the structure is visible, but tests will fail.
    # In a real scenario, this import failure must be fixed.
    pass


# Load .env file from the project root (terrafusion_platform/.env)
# This ensures that environment variables like TEST_DATABASE_URL are available.
DOTENV_PATH = os.path.join(PROJECT_ROOT_FOR_TESTS, '.env')
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
    print(f"Loaded .env file from: {DOTENV_PATH}")
else:
    # Fallback if .env is in the current directory (e.g. when running tests from project root)
    if os.path.exists(".env"):
        load_dotenv()
        print("Loaded .env file from current directory.")
    else:
        print("Warning: .env file not found at project root or current directory.")


# --- Alembic Configuration ---
@pytest.fixture(scope="session")
def alembic_config_path():
    """Returns the path to alembic.ini, assuming it's in terrafusion_sync/"""
    # Try the standard path first
    path = os.path.join(TERRAFUSION_SYNC_ROOT, "alembic.ini")
    
    # If not found, look for it in the project root 
    if not os.path.exists(path):
        alt_path = os.path.join(PROJECT_ROOT_FOR_TESTS, "terrafusion_sync", "alembic.ini")
        if os.path.exists(alt_path):
            return alt_path
        # If still not found, try the direct path from the project root
        direct_path = os.path.join(PROJECT_ROOT_FOR_TESTS, "terrafusion_sync/alembic.ini")
        if os.path.exists(direct_path):
            return direct_path
        # One more attempt from the file system root
        root_path = "/home/runner/workspace/terrafusion_sync/alembic.ini"
        if os.path.exists(root_path):
            return root_path
            
        pytest.fail(f"Alembic config file not found at {path} or alternative paths. "
                    "Ensure alembic init was run in terrafusion_sync/ and env.py is configured.")
    return path

@pytest.fixture(scope="session")
def alembic_cfg_obj(alembic_config_path):
    """Provides the Alembic Config object."""
    from alembic.config import Config
    # Set the script location for Alembic relative to the ini file
    # Alembic needs to know where its 'versions' directory is.
    
    # Temporarily change CWD for Alembic to load its environment correctly
    original_cwd = os.getcwd()
    os.chdir(TERRAFUSION_SYNC_ROOT)
    try:
        cfg = Config(alembic_config_path)
        # Ensure Alembic uses the TEST database URL for migrations during tests
        test_db_url = os.getenv("TEST_DATABASE_URL")
        if not test_db_url:
            pytest.fail("TEST_DATABASE_URL not set for Alembic test config.")
        cfg.set_main_option("sqlalchemy.url", test_db_url) # Override for tests
    finally:
        os.chdir(original_cwd)
    return cfg


# --- Database Fixtures ---
@pytest_asyncio.fixture(scope="session")
async def pg_engine(alembic_cfg_obj):
    """
    Provides an SQLAlchemy async engine connected to the TEST database.
    It runs Alembic migrations to set up the schema once per test session.
    """
    from alembic import command # Alembic command interface

    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        pytest.fail("TEST_DATABASE_URL environment variable is not set.")

    # Check if we need to convert non-async URL to async
    if "postgresql://" in test_db_url and "asyncpg" not in test_db_url:
        test_db_url = test_db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        test_db_url, 
        echo=os.getenv("SQLALCHEMY_TEST_ECHO", "False").lower() == "true"
    )

    # Run Alembic migrations to "head" to set up the schema
    print(f"\nApplying Alembic migrations to test database: {test_db_url.split('@')[-1]}")
    original_cwd = os.getcwd()
    os.chdir(TERRAFUSION_SYNC_ROOT) # Alembic commands often expect to be run from where alembic.ini is
    try:
        command.upgrade(alembic_cfg_obj, "head")
        print("Alembic migrations applied successfully.")
    except Exception as e:
        pytest.fail(f"Alembic upgrade failed: {e}")
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
    It begins a transaction before the test and rolls it back after,
    ensuring test isolation.
    """
    AsyncSessionFactory = sessionmaker(
        bind=pg_engine, class_=AsyncSession, expire_on_commit=False, future=True
    )
    
    async with AsyncSessionFactory() as session:
        # Start a top-level transaction for the test.
        # If your code uses nested transactions (savepoints), this will work.
        async with session.begin() as transaction: 
            print(f"\nTest DB Session: BEGIN (Test: {os.environ.get('PYTEST_CURRENT_TEST', '').split(' ')[0]})")
            yield session
            # Rollback the transaction after the test to undo any changes
            await transaction.rollback()
            print(f"Test DB Session: ROLLBACK (Test: {os.environ.get('PYTEST_CURRENT_TEST', '').split(' ')[0]})")


@pytest_asyncio.fixture(scope="function")
async def create_property_operational(db_session: AsyncSession) -> Callable[..., PropertyOperational]:
    """
    Factory fixture to create PropertyOperational records in the test database.
    Relies on the db_session fixture's transaction rollback for cleanup.
    """
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
        
        db_session.add(new_property)
        await db_session.flush() # Assigns IDs, etc., if DB-generated, before potential rollback
        await db_session.refresh(new_property) # Get all defaults and DB-generated values
        
        print(f"Fixture: Created PropertyOperational: {new_property.property_id}")
        return new_property

    return _create_property


@pytest_asyncio.fixture(scope="function")
async def create_report_job(db_session: AsyncSession) -> Callable[..., ReportJob]:
    """
    Factory fixture to create ReportJob records in the test database.
    Relies on the db_session fixture's transaction rollback for cleanup.
    """
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
        
        db_session.add(new_report_job)
        await db_session.flush()
        await db_session.refresh(new_report_job)
        
        print(f"Fixture: Created ReportJob: {new_report_job.report_id} ({new_report_job.report_type})")
        return new_report_job

    return _create_report_job


# --- API Client Fixtures ---
# Import the FastAPI app from terrafusion_sync
try:
    from terrafusion_sync.app import app as actual_sync_app
    
    # Try to import dependency from connectors.postgres, if it doesn't exist we'll handle it
    try:
        from terrafusion_sync.database import get_session as app_get_db_session # Database session dependency
    except ImportError as e:
        print(f"Warning: Could not import 'get_session' from terrafusion_sync.database. Dependency override may fail: {e}")
        app_get_db_session = None  # We'll check this later
except ImportError as e:
    print(f"Failed to import 'app' from 'terrafusion_sync.app': {e}")
    print("Check PYTHONPATH/imports.")
    actual_sync_app = None  # We'll check this later


@pytest_asyncio.fixture(scope="function") # Function scope for client if app state changes or for dep override
async def sync_client(db_session: AsyncSession) -> AsyncGenerator:
    """
    Provides a FastAPI TestClient for the terrafusion_sync service.
    Crucially, it overrides the `get_session` dependency in the app
    to use the test-specific, transaction-managed `db_session` from this conftest.
    """
    if actual_sync_app is None:
        pytest.skip("FastAPI app could not be imported. Skipping test.")
        return
        
    if app_get_db_session is None:
        pytest.skip("Database session dependency could not be imported. Skipping test.")
        return
    
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.skip("fastapi and httpx must be installed for testing: pip install fastapi httpx")
        return

    # Define a dependency override for get_db_session
    async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session # Use the test-managed session

    # Apply the override to the FastAPI app
    actual_sync_app.dependency_overrides[app_get_db_session] = override_get_db_session
    
    print("\nTest Client: Initialized with DB session override.")
    # Create client
    client = TestClient(actual_sync_app, base_url="http://testserver-sync")
    yield client
    
    # Clear the dependency override after the test
    del actual_sync_app.dependency_overrides[app_get_db_session]
    print("Test Client: DB session override cleared.")