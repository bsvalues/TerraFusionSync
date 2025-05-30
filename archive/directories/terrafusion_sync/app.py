"""
TerraFusion SyncService - FastAPI Application

This module provides the FastAPI application for the TerraFusion SyncService platform.
It initializes the database and sets up routes for property assessment synchronization.
"""

import logging
import os
import json
import sys
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from terrafusion_sync.plugins.market_analysis import plugin_router as market_analysis_router
# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

# Add the project root to the Python path to allow importing from terrafusion_platform
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

# Import database and models
from terrafusion_sync.database import get_db_session, initialize_db, get_db_status
from terrafusion_sync.core_models import (
    PropertyOperational,
    ReportJob
)

# Import plugins router
try:
    from terrafusion_sync.plugins import plugins_router
    logger.info("Loaded plugins router")
except ImportError as e:
    logger.warning(f"Unable to import plugins: {e}. Plugin functionality won't be available.")
    plugins_router = None

# Import county config manager - this will be used to retrieve county-specific settings
try:
    from terrafusion_platform.sdk.county_config import CountyConfigManager
    county_manager = CountyConfigManager()
    logger.info(f"CountyConfigManager loaded with {len(county_manager.list_available_counties())} available counties")
except ImportError as e:
    logger.warning(f"Unable to import CountyConfigManager: {e}. County-specific configurations won't be available.")
    county_manager = None

# Create FastAPI application
app = FastAPI(
    title="TerraFusion SyncService",
    description="Enterprise data synchronization platform for County Property Assessment",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include plugins router if available
if plugins_router:
    app.include_router(plugins_router)
    logger.info("Registered plugins router with FastAPI application")

# Include market analysis plugin router
app.include_router(market_analysis_router, tags=["Market Analysis"])
logger.info("Registered market analysis plugin router with FastAPI application")

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    logger.info("Starting TerraFusion SyncService...")
    try:
        await initialize_db()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Check the health of the SyncService.
    
    Returns:
        dict: Health status information
    """
    db_status = await get_db_status()
    return {
        "status": "healthy" if db_status["status"] == "connected" else "unhealthy",
        "version": "0.1.0",
        "database": db_status,
        "environment": os.getenv("ENV", "development")
    }


# Metrics endpoint for monitoring
# Initialize system metrics gauges (defined at module level to avoid duplication)
from prometheus_client import Gauge

# System metrics as module-level variables
SYSTEM_CPU_USAGE = Gauge('terrafusion_system_cpu_percent', 'Current CPU usage percentage')
SYSTEM_MEMORY_USAGE = Gauge('terrafusion_system_memory_percent', 'Current memory usage percentage')
SYSTEM_DISK_USAGE = Gauge('terrafusion_system_disk_percent', 'Current disk usage percentage')

@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get system metrics for monitoring.
    
    This endpoint provides resource utilization and application performance metrics
    in Prometheus format. It includes both system metrics and application-specific
    metrics such as valuation job statistics.
    
    Returns:
        Response: Prometheus formatted metrics
    """
    import psutil
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    # Update system metrics using the module-level gauges
    SYSTEM_CPU_USAGE.set(psutil.cpu_percent())
    SYSTEM_MEMORY_USAGE.set(psutil.virtual_memory().percent)
    SYSTEM_DISK_USAGE.set(psutil.disk_usage('/').percent)
    
    # Update database metrics
    try:
        db_metrics = await collect_db_metrics()
        from terrafusion_sync.metrics import update_metrics_from_database
        update_metrics_from_database(db_metrics)
    except Exception as e:
        logger.error(f"Error updating metrics from database: {e}")
    
    # Generate metrics response
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

async def collect_db_metrics():
    """
    Collect metrics from the database.
    
    Returns:
        Dict with database metrics
    """
    from sqlalchemy import text
    from terrafusion_sync.database import get_session
    
    db_metrics = {}
    
    session = await get_session()
    try:
        # Check if valuation_jobs table exists before querying it
        try:
            result = await session.execute(
                text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'valuation_jobs'
                )
                """)
            )
            valuation_jobs_exists = result.scalar() or False
            
            if valuation_jobs_exists:
                # Count pending valuation jobs
                result = await session.execute(
                    text("SELECT COUNT(*) FROM valuation_jobs WHERE status = 'PENDING'")
                )
                db_metrics['valuation_jobs_pending'] = result.scalar() or 0
                
                # Count in-progress valuation jobs
                result = await session.execute(
                    text("SELECT COUNT(*) FROM valuation_jobs WHERE status = 'IN_PROGRESS'")
                )
                db_metrics['valuation_jobs_in_progress'] = result.scalar() or 0
            else:
                # Set default values if table doesn't exist
                db_metrics['valuation_jobs_pending'] = 0
                db_metrics['valuation_jobs_in_progress'] = 0
                logger.info("ValuationJobs table doesn't exist yet, using default metrics")
        except Exception as e:
            logger.error(f"Error checking/counting valuation jobs: {e}")
            db_metrics['valuation_jobs_pending'] = 0
            db_metrics['valuation_jobs_in_progress'] = 0
        
        # Get active DB connections (this is PostgreSQL specific)
        try:
            result = await session.execute(
                text("""
                SELECT count(*) 
                FROM pg_stat_activity 
                WHERE datname = current_database()
                """)
            )
            db_metrics['db_connections_active'] = result.scalar() or 0
        except Exception as e:
            logger.error(f"Error getting active DB connections: {e}")
            db_metrics['db_connections_active'] = 0
        
        return db_metrics
    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")
        return {}
    finally:
        await session.close()
    import time
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Application metrics
    start_time = time.time()
    db_status = await get_db_status()
    response_time = time.time() - start_time
    
    # Count database records
    property_count = 0
    sync_source_count = 0
    import_job_count = 0
    
    try:
        async with get_db_session() as session:
            # Count PropertyOperational records
            from sqlalchemy import func, select
            from terrafusion_sync.core_models import PropertyOperational
            
            # Get counts if tables exist (safely)
            try:
                result = await session.execute(select(func.count()).select_from(PropertyOperational))
                property_count = result.scalar() or 0
            except Exception as e:
                logger.warning(f"Could not count PropertyOperational records: {e}")
            
            # SyncSourceSystem and ImportJob have been removed - set default values
            sync_source_count = 0
            import_job_count = 0
            logger.info("SyncSourceSystem and ImportJob models have been removed, using default counts")
    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")
    
    # Format the current timestamp in ISO format for better compatibility
    from datetime import datetime
    current_timestamp = datetime.utcnow().isoformat()
    
    # Return metrics with ISO format timestamp to ensure compatibility
    return {
        "timestamp": current_timestamp,
        "system": {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "memory_available_mb": memory.available // (1024 * 1024),
            "disk_free_gb": disk.free // (1024 * 1024 * 1024)
        },
        "database": {
            "status": db_status["status"],
            "response_time_ms": round(response_time * 1000, 2),
            "property_count": property_count,
            "sync_source_count": sync_source_count,
            "import_job_count": import_job_count
        },
        "application": {
            "version": "0.1.0",
            "uptime_seconds": int(time.time() - psutil.boot_time()),
            "environment": os.getenv("ENV", "development")
        }
    }


# Property endpoints
@app.get("/properties", tags=["Properties"], response_model=List[Dict[str, Any]])
async def get_properties(
    county_id: Optional[str] = None,
    property_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get properties with optional filtering.
    
    Args:
        county_id: Filter by county ID
        property_type: Filter by property type
        limit: Maximum number of properties to return
        offset: Offset for pagination
        
    Returns:
        List of property dictionaries
    """
    from terrafusion_sync.database import get_session
    
    query = select(PropertyOperational)
    
    # Apply filters if provided
    if county_id:
        query = query.where(PropertyOperational.county_id == county_id)
    if property_type:
        query = query.where(PropertyOperational.property_type == property_type)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    session = await get_session()
    try:
        result = await session.execute(query)
        properties = result.scalars().all()
        return [prop.to_dict() for prop in properties]
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching properties: {str(e)}"
        )
    finally:
        await session.close()


@app.get("/properties/{property_id}", tags=["Properties"], response_model=Dict[str, Any])
async def get_property(
    property_id: str
):
    """
    Get a property by ID.
    
    Args:
        property_id: The property ID
        
    Returns:
        Property as a dictionary
        
    Raises:
        HTTPException: If property not found
    """
    from terrafusion_sync.database import get_session
    
    query = select(PropertyOperational).where(PropertyOperational.property_id == property_id)
    
    session = await get_session()
    try:
        result = await session.execute(query)
        property = result.scalar_one_or_none()
        
        if not property:
            raise HTTPException(
                status_code=404,  # HTTP_404_NOT_FOUND
                detail=f"Property with ID {property_id} not found"
            )
            
        return property.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching property: {str(e)}"
        )
    finally:
        await session.close()


# County configuration endpoints
@app.get("/counties", tags=["Counties"], response_model=List[Dict[str, Any]])
async def get_counties():
    """
    Get a list of all configured counties.
    
    Returns:
        List of county dictionaries with basic information
    """
    # Check if county_manager is available
    if county_manager is None:
        logger.warning("CountyConfigManager is not available. Unable to retrieve county configurations.")
        return []
    
    try:
        county_list = county_manager.list_available_counties()
        result = []
        
        for county_name in county_list:
            try:
                config = county_manager.get_county_config(county_name)
                result.append({
                    "county_id": config.get_county_id(),
                    "county_name": config.get_county_name(),
                    "legacy_system_type": config.get_legacy_system_type()
                })
            except Exception as e:
                logger.error(f"Error loading county configuration for '{county_name}': {e}")
        
        return result
    except Exception as e:
        logger.error(f"Error retrieving county list: {e}")
        return []


@app.get("/counties/{county_id}", tags=["Counties"], response_model=Dict[str, Any])
async def get_county_config(county_id: str):
    """
    Get detailed configuration information for a specific county.
    
    Args:
        county_id: The county ID
        
    Returns:
        County configuration dictionary
        
    Raises:
        HTTPException: If county configuration not found
    """
    # Check if county_manager is available
    if county_manager is None:
        raise HTTPException(
            status_code=503,  # Service Unavailable
            detail="County configuration service is not available"
        )
    
    try:
        config = county_manager.get_county_config(county_id)
        return {
            "county_id": config.get_county_id(),
            "county_name": config.get_county_name(),
            "legacy_system_type": config.get_legacy_system_type(),
            "connection_params": config.get_legacy_connection_params(),
            "users_count": len(config.get_users()),
            "roles_count": len(config.get_role_definitions()),
            "mappings": {
                "tables": list(config.get_field_mappings().keys())
            }
        }
    except ValueError as e:
        raise HTTPException(
            status_code=404,  # Not Found
            detail=f"County configuration not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error retrieving county configuration for '{county_id}': {e}")
        raise HTTPException(
            status_code=500,  # Internal Server Error
            detail=f"Error retrieving county configuration: {str(e)}"
        )


# Sync Source System endpoints - SyncSourceSystem model has been removed
@app.get("/sync-sources", tags=["Sync"], response_model=List[Dict[str, Any]])
async def get_sync_sources(
    county_id: Optional[str] = None,
    system_type: Optional[str] = None
):
    """
    Get sync source systems with optional filtering.
    Note: SyncSourceSystem model has been removed, returns empty list temporarily.
    
    Args:
        county_id: Filter by county ID
        system_type: Filter by system type
        
    Returns:
        List of sync source system dictionaries (empty list for now)
    """
    logger.info("SyncSourceSystem model has been removed, returning empty list")
    return []


# Data seeding endpoint for development/testing
@app.post("/seed-sample-data", tags=["Development"])
async def seed_sample_data(
    count: int = 10,
    county_id: str = "SAMPLE-001",
    include_sync_sources: bool = False
):
    """
    Seed the database with sample property data for testing.
    This endpoint is for development and testing purposes only.
    
    Args:
        count: Number of sample properties to create (default: 10)
        county_id: County ID to use for sample data (default: SAMPLE-001)
        include_sync_sources: Whether to add sample sync sources (default: False)
        
    Returns:
        Dict with status and count of created records
    """
    # Only allow this in development environment
    if os.getenv("ENV", "development") != "development":
        raise HTTPException(
            status_code=403,  # Forbidden
            detail="Seed endpoint is only available in development environment"
        )
    
    logger.info(f"Seeding {count} sample properties for county {county_id}")
    
    from datetime import datetime, timedelta
    import random
    import string
    import uuid
    from terrafusion_sync.database import get_session
    
    # Property types for random selection
    property_types = ["residential", "commercial", "industrial", "agricultural", "vacant"]
    
    # Create sample properties
    created_count = 0
    sync_sources_count = 0
    session = await get_session()
    
    try:
        # Create sample properties
        for i in range(count):
            # Generate a unique property ID
            property_id = f"PROP-{uuid.uuid4().hex[:8]}"
            
            # Create random property data
            property_type = random.choice(property_types)
            year_built = random.randint(1950, 2023) if property_type != "vacant" else None
            sale_date = datetime.utcnow() - timedelta(days=random.randint(30, 3650))
            
            # Create the property
            new_property = PropertyOperational(
                property_id=property_id,
                county_id=county_id,
                parcel_number=f"P-{random.randint(100000, 999999)}",
                address_street=f"{random.randint(100, 9999)} Sample {random.choice(['St', 'Ave', 'Blvd', 'Rd'])}",
                address_city="Sample City",
                address_state="SC",
                address_zip=f"{random.randint(10000, 99999)}",
                property_type=property_type,
                land_area_sqft=random.randint(2000, 20000),
                building_area_sqft=random.randint(1000, 5000) if property_type != "vacant" else None,
                year_built=year_built,
                bedrooms=random.randint(2, 6) if property_type == "residential" else None,
                bathrooms=random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]) if property_type == "residential" else None,
                last_sale_date=sale_date,
                last_sale_price=random.randint(100000, 1000000),
                current_market_value=random.randint(150000, 1200000),
                assessed_value=random.randint(100000, 800000),
                assessment_year=datetime.utcnow().year - random.randint(0, 3),
                tax_district="Sample District",
                millage_rate=random.uniform(20.0, 50.0),
                tax_amount=random.randint(2000, 15000),
                owner_name=f"Sample Owner {i}",
                owner_type=random.choice(["individual", "business", "trust"]),
                latitude=random.uniform(32.0, 35.0),
                longitude=random.uniform(-81.0, -79.0),
                legal_description=f"Sample legal description for property {property_id}",
                is_exempt=random.choice([True, False]),
                exemption_type="Homestead" if random.random() > 0.7 else None,
                is_historical=random.random() > 0.9,
                data_source="seed-data",
                extended_attributes={
                    "seed_source": "terrafusion_sync",
                    "generator_version": "0.1.0",
                    "random_attributes": {
                        "attr1": random.randint(1, 100),
                        "attr2": ''.join(random.choices(string.ascii_letters, k=8))
                    }
                }
            )
            
            # Add the property to the session
            session.add(new_property)
            created_count += 1
        
        # Skip sync sources - SyncSourceSystem and ImportJob models have been removed
        if include_sync_sources:
            logger.info("SyncSourceSystem and ImportJob models have been removed, skipping sync sources creation in seed data")
            
        # Commit all changes
        await session.commit()
        logger.info(f"Successfully created {created_count} sample properties and {sync_sources_count} sync sources")
        
        return {
            "status": "success",
            "created_count": created_count,
            "sync_sources_count": sync_sources_count,
            "county_id": county_id
        }
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Error seeding sample data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error seeding sample data: {str(e)}"
        )
    finally:
        await session.close()


# Import Job endpoints - ImportJob model has been removed
@app.get("/import-jobs", tags=["Import"], response_model=List[Dict[str, Any]])
async def get_import_jobs(
    source_system_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get import jobs with optional filtering.
    Note: ImportJob model has been removed, returns empty list temporarily.
    
    Args:
        source_system_id: Filter by source system ID
        status: Filter by job status
        limit: Maximum number of jobs to return
        offset: Offset for pagination
        
    Returns:
        List of import job dictionaries (empty list for now)
    """
    logger.info("ImportJob model has been removed, returning empty list")
    return []