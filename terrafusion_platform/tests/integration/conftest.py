import asyncio
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator, Callable, Dict, Any
import uuid
import datetime  # Added for datetime usage

# Add project root to sys.path to allow importing application modules
PROJECT_ROOT_FOR_TESTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
import sys
sys.path.insert(0, PROJECT_ROOT_FOR_TESTS)

# Attempt to import Base and PropertyOperational model
try:
    from terrafusion_sync.core_models import Base, PropertyOperational
except ImportError:
    # Fallback for different execution contexts
    print("Warning: Could not directly import from terrafusion_sync.core_models. "
          "Ensure PYTHONPATH is set correctly or adjust import paths for tests.")
    
    # Define minimal stubs if import fails
    from sqlalchemy.orm import declarative_base
    from sqlalchemy import Column, String, Integer, Float, DateTime
    Base = declarative_base()
    class PropertyOperational(Base):
        __tablename__ = "properties_operational_test_stub"
        id = Column(Integer, primary_key=True)
        property_id = Column(String, unique=True, index=True, nullable=False)
        county_id = Column(String, index=True, nullable=False)
        situs_address_full = Column(String, nullable=True)
        current_assessed_value_total = Column(Float, nullable=True)
        year_built = Column(Integer, nullable=True)
        created_at = Column(DateTime, default=datetime.datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# Load environment variables
DOTENV_PATH = os.path.join(PROJECT_ROOT_FOR_TESTS, '.env')
if os.path.exists(DOTENV_PATH):
    load_dotenv(dotenv_path=DOTENV_PATH)
else:
    load_dotenv()

# --- Database Fixtures ---

@pytest_asyncio.fixture(scope="session")
async def event_loop():
    """Creates an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def pg_engine():
    """
    Provides an SQLAlchemy async engine connected to the TEST database.
    It creates all tables defined in Base.metadata before tests run
    and disposes of the engine after tests complete.
    """
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        pytest.fail("TEST_DATABASE_URL environment variable is not set. "
                    "Please define it in your .env file for testing.")

    # Check if we need to convert non-async URL to async
    if "postgresql://" in test_db_url and "asyncpg" not in test_db_url:
        test_db_url = test_db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(
        test_db_url, 
        echo=os.getenv("SQLALCHEMY_TEST_ECHO", "False").lower() == "true"
    )
    
    async with engine.begin() as conn:
        # Drop all tables to ensure clean state
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Teardown: Dispose of the engine
    await engine.dispose()

@pytest_asyncio.fixture(scope="function")
async def db_session(pg_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provides an SQLAlchemy AsyncSession for a single test function.
    It begins a transaction before the test and rolls it back after,
    ensuring test isolation.
    """
    AsyncSessionFactory = sessionmaker(
        bind=pg_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionFactory() as session:
        # Start transaction
        async with session.begin():
            yield session
            # Transaction is automatically rolled back when exiting the context

@pytest_asyncio.fixture(scope="function")
def create_property_operational(db_session: AsyncSession) -> Callable[..., PropertyOperational]:
    """
    Factory fixture to create PropertyOperational records in the test database.
    Ensures records are cleaned up after the test via transaction rollback.
    """
    created_property_ids = []

    async def _create_property(
        property_id: str = None,
        county_id: str = "test_county",
        situs_address_full: str = "123 Test St, Testville, TS 12345",
        current_assessed_value_total: float = 100000.0,
        year_built: int = 2000,
        custom_fields: Dict[str, Any] = None
    ) -> PropertyOperational:
        nonlocal created_property_ids
        if property_id is None:
            property_id = f"TEST_PROP_{uuid.uuid4().hex[:8]}"

        prop_data = {
            "property_id": property_id,
            "county_id": county_id,
            "situs_address_full": situs_address_full,
            "current_assessed_value_total": current_assessed_value_total,
            "year_built": year_built,
            "created_at": datetime.datetime.utcnow(),
            "updated_at": datetime.datetime.utcnow()
        }
        if custom_fields:
            prop_data.update(custom_fields)
        
        new_property = PropertyOperational(**prop_data)
        
        db_session.add(new_property)
        await db_session.flush()
        await db_session.refresh(new_property)
        
        created_property_ids.append(new_property.property_id)
        return new_property

    return _create_property

# --- API Client Fixtures ---

@pytest_asyncio.fixture(scope="session")
def sync_app_for_test():
    """
    Provides the FastAPI application instance from terrafusion_sync.
    This allows TestClient to interact with it.
    """
    try:
        from terrafusion_sync.app import app as actual_sync_app
        return actual_sync_app
    except ImportError:
        pytest.fail("Failed to import 'app' from 'terrafusion_sync.app'. Check PYTHONPATH and imports.")

@pytest_asyncio.fixture(scope="function")
async def sync_client(sync_app_for_test):
    """
    Provides a FastAPI TestClient for the terrafusion_sync service.
    """
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        pytest.fail("fastapi and httpx must be installed for testing: pip install fastapi httpx")
        
    # Create a client for the test
    client = TestClient(sync_app_for_test, base_url="http://testserver")
    yield client