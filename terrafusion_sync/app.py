"""
TerraFusion SyncService - FastAPI Application

This module provides the FastAPI application for the TerraFusion SyncService platform.
It initializes the database and sets up routes for property assessment synchronization.
"""

import logging
import os
import json
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Import database and models
from terrafusion_sync.database import get_db_session, initialize_db, get_db_status
from terrafusion_sync.core_models import (
    PropertyOperational,
    PropertyValuation,
    PropertyImprovement,
    SyncSourceSystem,
    ImportJob
)

# Configure logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger(__name__)

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
@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """
    Get system metrics for monitoring.
    
    This endpoint provides resource utilization and application performance metrics.
    
    Returns:
        dict: System metrics
    """
    import psutil
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
            from terrafusion_sync.core_models import PropertyOperational, SyncSourceSystem, ImportJob
            
            # Get counts if tables exist (safely)
            try:
                result = await session.execute(select(func.count()).select_from(PropertyOperational))
                property_count = result.scalar() or 0
            except Exception as e:
                logger.warning(f"Could not count PropertyOperational records: {e}")
            
            try:
                result = await session.execute(select(func.count()).select_from(SyncSourceSystem))
                sync_source_count = result.scalar() or 0
            except Exception as e:
                logger.warning(f"Could not count SyncSourceSystem records: {e}")
                
            try:
                result = await session.execute(select(func.count()).select_from(ImportJob))
                import_job_count = result.scalar() or 0
            except Exception as e:
                logger.warning(f"Could not count ImportJob records: {e}")
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


# Sync Source System endpoints
@app.get("/sync-sources", tags=["Sync"], response_model=List[Dict[str, Any]])
async def get_sync_sources(
    county_id: Optional[str] = None,
    system_type: Optional[str] = None
):
    """
    Get sync source systems with optional filtering.
    
    Args:
        county_id: Filter by county ID
        system_type: Filter by system type
        
    Returns:
        List of sync source system dictionaries
    """
    from terrafusion_sync.database import get_session
    
    query = select(SyncSourceSystem)
    
    # Apply filters if provided
    if county_id:
        query = query.where(SyncSourceSystem.county_id == county_id)
    if system_type:
        query = query.where(SyncSourceSystem.system_type == system_type)
    
    session = await get_session()
    try:
        result = await session.execute(query)
        systems = result.scalars().all()
        return [
            {
                "id": system.id,
                "name": system.name,
                "system_type": system.system_type,
                "county_id": system.county_id,
                "connection_type": system.connection_type,
                "is_active": system.is_active,
                "last_successful_sync": system.last_successful_sync.isoformat() if system.last_successful_sync else None,
                "created_at": system.created_at.isoformat()
            }
            for system in systems
        ]
    except Exception as e:
        logger.error(f"Error fetching sync sources: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching sync sources: {str(e)}"
        )
    finally:
        await session.close()


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
        
        # Create sample sync sources if requested
        if include_sync_sources:
            # System types for random selection
            system_types = ["tax", "assessment", "gis", "permits", "legacy"]
            connection_types = ["api", "database", "file", "sftp", "web"]
            
            # Create 3 sample sync sources for the county
            for i in range(3):
                system_type = system_types[i % len(system_types)]
                connection_type = connection_types[i % len(connection_types)]
                
                # Create the sync source
                auth_type = "basic" if random.random() > 0.5 else "oauth"
                connection_config = json.dumps({
                    "host": f"sample-{system_type}-host.example.com",
                    "port": random.randint(1000, 9000),
                    "username": f"demo_user_{system_type}",
                    "use_ssl": random.choice([True, False])
                })
                auth_config = json.dumps({
                    "type": auth_type,
                    "credentials": {
                        "username": f"demo_user_{system_type}",
                        "api_key": f"sample_key_{uuid.uuid4().hex[:8]}"
                    }
                })
                
                new_source = SyncSourceSystem(
                    name=f"{county_id} {system_type.capitalize()} System",
                    system_type=system_type,
                    county_id=county_id,
                    connection_type=connection_type,
                    connection_config=connection_config,
                    auth_type=auth_type,
                    auth_config=auth_config,
                    is_active=random.random() > 0.3,  # 70% chance of being active
                    last_successful_sync=datetime.utcnow() - timedelta(days=random.randint(1, 30)) if random.random() > 0.2 else None
                )
                
                # Add the sync source to the session
                session.add(new_source)
                sync_sources_count += 1
                
                # If this is the first sync source, add a few import jobs for it
                if i == 0:
                    # We'll need to flush to get the ID of the new source
                    await session.flush()
                    source_id = new_source.id
                    
                    # Add 3 sample import jobs with different statuses
                    job_statuses = ["completed", "in_progress", "failed"]
                    for j in range(3):
                        status = job_statuses[j]
                        start_time = datetime.utcnow() - timedelta(hours=random.randint(1, 48))
                        
                        # For completed jobs, set end time and success metrics
                        end_time = None
                        if status == "completed":
                            end_time = start_time + timedelta(minutes=random.randint(5, 60))
                        elif status == "failed":
                            end_time = start_time + timedelta(minutes=random.randint(1, 20))
                        
                        total_records = random.randint(100, 5000)
                        processed_records = total_records if status != "in_progress" else random.randint(0, total_records)
                        successful_records = processed_records - random.randint(0, 50) if status == "completed" else processed_records - random.randint(50, 200) if status == "failed" else 0
                        failed_records = processed_records - successful_records
                        
                        # Calculate metrics
                        progress = processed_records / total_records * 100 if total_records > 0 else 0
                        success_rate = successful_records / processed_records * 100 if processed_records > 0 else 0
                        duration = (end_time - start_time).total_seconds() if end_time else None
                        
                        # Create the import job
                        new_job = ImportJob(
                            source_system_id=source_id,
                            job_type="full_sync" if random.random() > 0.7 else "incremental_sync",
                            status=status,
                            total_records=total_records,
                            processed_records=processed_records,
                            successful_records=successful_records,
                            failed_records=failed_records,
                            start_time=start_time,
                            end_time=end_time,
                            created_by="seed_utility",
                            progress_percentage=round(progress, 2),
                            success_rate=round(success_rate, 2),
                            duration_seconds=duration
                        )
                        
                        # Add the import job to the session
                        session.add(new_job)
            
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


# Import Job endpoints
@app.get("/import-jobs", tags=["Import"], response_model=List[Dict[str, Any]])
async def get_import_jobs(
    source_system_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    Get import jobs with optional filtering.
    
    Args:
        source_system_id: Filter by source system ID
        status: Filter by job status
        limit: Maximum number of jobs to return
        offset: Offset for pagination
        
    Returns:
        List of import job dictionaries
    """
    from terrafusion_sync.database import get_session
    
    query = select(ImportJob).order_by(ImportJob.created_at.desc())
    
    # Apply filters if provided
    if source_system_id:
        query = query.where(ImportJob.source_system_id == source_system_id)
    if status:
        query = query.where(ImportJob.status == status)
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    session = await get_session()
    try:
        result = await session.execute(query)
        jobs = result.scalars().all()
        return [
            {
                "id": job.id,
                "source_system_id": job.source_system_id,
                "job_type": job.job_type,
                "status": job.status,
                "total_records": job.total_records,
                "processed_records": job.processed_records,
                "successful_records": job.successful_records,
                "failed_records": job.failed_records,
                "start_time": job.start_time.isoformat() if job.start_time else None,
                "end_time": job.end_time.isoformat() if job.end_time else None,
                "created_at": job.created_at.isoformat(),
                "created_by": job.created_by,
                "progress_percentage": job.progress_percentage,
                "success_rate": job.success_rate,
                "duration_seconds": job.duration_seconds
            }
            for job in jobs
        ]
    except Exception as e:
        logger.error(f"Error fetching import jobs: {e}")
        raise HTTPException(
            status_code=500,  # HTTP_500_INTERNAL_SERVER_ERROR
            detail=f"Error fetching import jobs: {str(e)}"
        )
    finally:
        await session.close()