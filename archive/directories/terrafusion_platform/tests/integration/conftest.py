"""
Conftest for integration tests.

Provides fixtures for database session, FastAPI test client, and more.
"""

import os
import asyncio
import pytest
import uuid
import sys
from typing import Dict, Any, Callable, AsyncGenerator, Optional
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from datetime import datetime, timedelta

# Import the FastAPI app, models and database config from the terrafusion_sync package
from terrafusion_sync.app import app
from terrafusion_sync.database import get_session, DATABASE_URL
from terrafusion_sync.core_models import Base, PropertyOperational, ReportJob, MarketAnalysisJob

# Get database URL from environment or fallback to default
TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or DATABASE_URL

# Create a test async engine with optimized settings for test environments
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    future=True,
    pool_pre_ping=True,
    pool_recycle=300,
    # Quick timeout for tests
    connect_args={
        "command_timeout": 5,
    }
)

# Create a new async session factory
test_async_session_maker = async_sessionmaker(
    bind=test_engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

# We use the default event_loop fixture from pytest-asyncio
# This prevents the "Event loop is closed" error between tests


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    
    This fixture creates tables, runs the test with a dedicated
    session, and rolls back changes afterward.
    """
    # Create a new connection and begin a transaction
    connection = await test_engine.connect()
    
    try:
        trans = await connection.begin()
        
        # Create tables in a transaction
        await connection.run_sync(Base.metadata.create_all)
        
        # Create a new session for each test
        session = test_async_session_maker(bind=connection)
        
        try:
            # Return session for use in tests
            yield session
        finally:
            # Always make sure to close the session
            await session.close()
    except Exception as e:
        print(f"Error in db_session fixture: {str(e)}")
        raise
    finally:
        # Always try to clean up the connection
        try:
            if 'trans' in locals() and trans is not None:
                await trans.rollback()
            await connection.close()
        except Exception as e:
            print(f"Error cleaning up db_session fixture: {str(e)}")


@pytest.fixture(scope="function")
def sync_client() -> TestClient:
    """
    Create a FastAPI test client.
    
    This client can be used to make synchronous requests to the FastAPI app.
    """
    # Override the dependency to use our test session
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="function")
async def create_property_operational(db_session: AsyncSession) -> Callable:
    """
    Fixture to create a PropertyOperational object in the database.
    
    Returns a callable that can be used to create a PropertyOperational
    object with custom attributes.
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
        assessed_value: float = 100000,
        custom_fields: Dict[str, Any] = None
    ):
        """Create a PropertyOperational record."""
        # Generate a property ID if none is provided
        if property_id is None:
            property_id = f"PROP-{uuid.uuid4()}"
            
        # Create property instance
        property_obj = PropertyOperational(
            property_id=property_id,
            county_id=county_id,
            address_street=address_street,
            address_city=address_city,
            address_state=address_state,
            address_zip=address_zip,
            property_type=property_type,
            parcel_number=parcel_number,
            year_built=year_built,
            assessed_value=assessed_value,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Add custom fields if provided
        if custom_fields:
            property_obj.extended_attributes = custom_fields
            
        # Add to database and commit
        db_session.add(property_obj)
        await db_session.commit()
        
        # Refresh to get any database-generated values
        await db_session.refresh(property_obj)
        
        return property_obj
        
    return _create_property


@pytest.fixture(scope="function")
async def create_report_job(db_session: AsyncSession) -> Callable:
    """
    Fixture to create a ReportJob object in the database.
    
    Returns a callable that can be used to create a ReportJob
    object with custom attributes.
    """
    async def _create_report_job(
        report_id: str = None,
        report_type: str = "assessment_roll",
        county_id: str = "test_county",
        status: str = "PENDING",
        message: Optional[str] = None,
        parameters_json: Optional[Dict[str, Any]] = None,
        result_location: Optional[str] = None,
        result_metadata_json: Optional[Dict[str, Any]] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """Create a ReportJob record."""
        # Generate a report ID if none is provided
        if report_id is None:
            report_id = str(uuid.uuid4())
            
        # Create timestamps
        now = datetime.utcnow()
        
        # Create report job instance
        report_job = ReportJob(
            report_id=report_id,
            report_type=report_type,
            county_id=county_id,
            status=status,
            message=message,
            parameters_json=parameters_json or {},
            result_location=result_location,
            result_metadata_json=result_metadata_json,
            created_at=now,
            updated_at=now
        )
        
        # Add to database and commit
        db_session.add(report_job)
        await db_session.commit()
        
        # Refresh to get any database-generated values
        await db_session.refresh(report_job)
        
        return report_job
        
    return _create_report_job


@pytest.fixture(scope="function")
async def create_market_analysis_job(db_session: AsyncSession) -> Callable:
    """
    Fixture to create a MarketAnalysisJob object in the database.
    
    Returns a callable that can be used to create a MarketAnalysisJob
    object with custom attributes.
    """
    async def _create_market_analysis_job(
        job_id: str = None,
        analysis_type: str = "price_trend_by_zip",
        county_id: str = "test_county",
        status: str = "PENDING",
        message: Optional[str] = None,
        parameters_json: Optional[Dict[str, Any]] = None,
        result_summary_json: Optional[Dict[str, Any]] = None,
        result_data_location: Optional[str] = None,
        custom_fields: Optional[Dict[str, Any]] = None
    ):
        """Create a MarketAnalysisJob record."""
        # Generate a job ID if none is provided
        if job_id is None:
            job_id = str(uuid.uuid4())
            
        # Create timestamps
        now = datetime.utcnow()
        
        # Create market analysis job instance
        market_analysis_job = MarketAnalysisJob(
            job_id=job_id,
            analysis_type=analysis_type,
            county_id=county_id,
            status=status,
            message=message,
            parameters_json=parameters_json or {},
            result_summary_json=result_summary_json,
            result_data_location=result_data_location,
            created_at=now,
            updated_at=now
        )
        
        # Add to database and commit
        db_session.add(market_analysis_job)
        await db_session.commit()
        
        # Refresh to get any database-generated values
        await db_session.refresh(market_analysis_job)
        
        return market_analysis_job
        
    return _create_market_analysis_job