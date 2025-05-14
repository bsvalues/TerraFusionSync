"""
TerraFusion SyncService - Isolated GIS Export API

This is a completely isolated version of the GIS Export API that avoids
importing any other plugins or modules that might cause conflicts.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Union

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, validator

# Import prometheus_client for metrics
try:
    import prometheus_client
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client not available, metrics endpoint will return minimal data")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TerraFusion GIS Export API",
    description="Isolated GIS Export API service",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# System metrics - defined here to avoid duplication
if PROMETHEUS_AVAILABLE:
    # Basic system metrics
    SYSTEM_CPU_USAGE = Gauge('gis_export_system_cpu_percent', 'Current CPU usage percentage')
    SYSTEM_MEMORY_USAGE = Gauge('gis_export_system_memory_percent', 'Current memory usage percentage')
    SYSTEM_DISK_USAGE = Gauge('gis_export_system_disk_percent', 'Current disk usage percentage')
    
    # API metrics
    API_REQUESTS_TOTAL = Counter('gis_export_api_requests_total', 'Total API requests', ['endpoint', 'method', 'status'])
    API_REQUEST_DURATION = Histogram('gis_export_api_request_duration_seconds', 'API request duration in seconds', ['endpoint'])

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define models
class GisExportRequest(BaseModel):
    county_id: str = Field(..., description="ID of the county")
    username: str = Field(..., description="Username of the requester")
    format: str = Field(..., description="Export format (geojson, shapefile, kml)")
    area_of_interest: Dict[str, Any] = Field(..., description="GeoJSON defining the area of interest")
    layers: List[str] = Field(..., description="Layers to include in the export")
    
    class Config:
        schema_extra = {
            "example": {
                "county_id": "county123",
                "username": "user@example.com",
                "format": "geojson",
                "area_of_interest": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "layers": ["parcels", "buildings", "roads"]
            }
        }

class GisExportJobBase(BaseModel):
    job_id: int
    county_id: str
    username: str
    status: str
    created_at: datetime

class GisExportJobDetail(GisExportJobBase):
    export_format: str  # Changed from format to match frontend expectations
    area_of_interest: Dict[str, Any]
    layers: List[str]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_url: Optional[str] = None
    message: Optional[str] = None

# Database configuration
import uuid
import os
import json
import asyncio
from sqlalchemy import create_engine, Column, String, DateTime, Integer, Float, JSON, select, update, MetaData, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager
import time

# Get database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not found in environment variables!")
    raise ValueError("DATABASE_URL environment variable is required")

# Create SQLAlchemy engine and session
# Convert synchronous URL to async format for asyncpg
if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

try:
    # Create async engine
    async_engine = create_async_engine(
        ASYNC_DATABASE_URL,
        echo=False,
        pool_recycle=300,
        pool_pre_ping=True
    )
    logger.info("Created async database engine with PostgreSQL")
    
    # Create async session factory
    async_session_factory = sessionmaker(
        bind=async_engine,  # Fixed: use bind parameter instead of positional
        class_=AsyncSession, 
        expire_on_commit=False
    )
except Exception as e:
    logger.error(f"Failed to create async database engine: {e}")
    # Fallback to the in-memory storage
    async_engine = None
    async_session_factory = None

# Function to get a fresh database session
async def get_fresh_db_session():
    """
    Get a fresh database session for use in the application.
    Returns None if the database connection is not available.
    """
    if async_session_factory:
        return async_session_factory()
    return None

# Context manager for database operations
@asynccontextmanager
async def managed_db_session():
    """
    Asynchronous context manager for database operations with commit/rollback handling.
    Yields None if the database connection is not available.
    """
    if not async_session_factory:
        yield None
        return
        
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise
    finally:
        await session.close()

# In-memory storage for jobs (fallback if DB not available)
JOB_ID_COUNTER = 0
EXPORT_JOBS = {
    # Add a sample job for testing
    1: {
        "job_id": 1,
        "county_id": "TEST_COUNTY",
        "username": "admin",
        "export_format": "geojson",
        "area_of_interest": {
            "type": "Polygon",
            "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        },
        "layers": ["parcels", "buildings"],
        "status": "COMPLETED",
        "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        "started_at": datetime.now(timezone.utc) - timedelta(minutes=55),
        "completed_at": datetime.now(timezone.utc) - timedelta(minutes=50),
        "download_url": "/api/v1/gis-export/download/1",
        "message": "Export completed successfully"
    }
}

def get_next_job_id():
    # Generate a UUID for new jobs (DB uses UUID strings not integers)
    return str(uuid.uuid4())

async def process_export_job(job_id: str):
    """
    Process an export job in the background.
    If DB is available, uses the GisExportJob table, otherwise uses in-memory storage.
    
    Args:
        job_id: The UUID string of the job to process
    """
    logger.info(f"Processing GIS export job {job_id}")
    start_time = time.monotonic()
    
    # Try database first if available
    if async_session_factory:
        try:
            # Step 1: Get the job from database
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                # Use SQLAlchemy text to make raw SQL executable
                from sqlalchemy.sql import text
                
                query = text("SELECT * FROM gis_export_jobs WHERE job_id = :job_id")
                result = await session.execute(query, {"job_id": job_id})
                job_row = result.mappings().first()
                
                if not job_row:
                    logger.error(f"GIS export job {job_id} not found in database")
                    return
                
                logger.info(f"Found job {job_id} in database: {job_row['export_format']} for {job_row['county_id']}")
            
            # Step 2: Update to RUNNING status (new session)
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                update_query = text("""
                UPDATE gis_export_jobs
                SET status = 'RUNNING',
                    started_at = :started_at,
                    updated_at = :updated_at,
                    message = 'GIS export job is being processed.'
                WHERE job_id = :job_id
                """)
                
                now = datetime.now(timezone.utc)
                await session.execute(
                    update_query, 
                    {
                        "job_id": job_id,
                        "started_at": now,
                        "updated_at": now
                    }
                )
                # Commit happens in context manager
                logger.info(f"Updated job {job_id} status to RUNNING")
            
            # Store job details for use outside session
            export_format = job_row["export_format"]
            county_id = job_row["county_id"]
            
            # Step 3: Simulate processing time
            await asyncio.sleep(3)
            
            # Step 4: Update to COMPLETED status with result information (new session)
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                complete_query = text("""
                UPDATE gis_export_jobs
                SET status = 'COMPLETED',
                    completed_at = :completed_at,
                    updated_at = :updated_at,
                    message = 'GIS export completed successfully.',
                    result_file_location = :result_file_location,
                    result_file_size_kb = :result_file_size_kb,
                    result_record_count = :result_record_count
                WHERE job_id = :job_id
                """)
                
                # Calculate simulated file path and metadata
                now = datetime.now(timezone.utc)
                file_path = f"/gis_exports/{county_id}/{job_id}.{export_format.lower()}"
                file_size_kb = 5120  # Simulated 5MB file
                record_count = 2500  # Simulated record count
                
                await session.execute(
                    complete_query,
                    {
                        "job_id": job_id,
                        "completed_at": now,
                        "updated_at": now,
                        "result_file_location": file_path,
                        "result_file_size_kb": file_size_kb,
                        "result_record_count": record_count
                    }
                )
                # Commit happens in context manager
            
            # Record processing metrics
            processing_time = time.monotonic() - start_time
            logger.info(f"GIS export job {job_id} completed in {processing_time:.2f}s")
            return
                
        except Exception as e:
            logger.error(f"Error processing GIS export job in database: {e}", exc_info=True)
            # Try to mark as failed in database
            try:
                async with managed_db_session() as session:
                    if session is None:
                        raise ValueError("Database session not available")
                    
                    error_msg = str(e)
                    now = datetime.now(timezone.utc)
                    fail_query = text("""
                    UPDATE gis_export_jobs
                    SET status = 'FAILED',
                        completed_at = :completed_at,
                        updated_at = :updated_at,
                        message = :message
                    WHERE job_id = :job_id
                    """)
                    
                    await session.execute(
                        fail_query,
                        {
                            "job_id": job_id,
                            "completed_at": now,
                            "updated_at": now,
                            "message": f"GIS export failed: {error_msg}"
                        }
                    )
                    # Commit happens in context manager
                    logger.info(f"Marked job {job_id} as FAILED after exception")
            except Exception as inner_e:
                logger.error(f"Failed to mark job as failed in database: {inner_e}")
    
    # Fallback to in-memory storage if database not available
    # or if there was an error with the database operations
    try:
        # For in-memory storage, convert UUID to integer for backward compatibility
        memory_job_id = int(job_id.split("-")[0], 16) % 10000
        
        # Get the job
        job = EXPORT_JOBS.get(memory_job_id)
        if not job:
            logger.error(f"GIS export job {memory_job_id} not found in memory storage")
            return
        
        # Update job status to RUNNING
        job["status"] = "RUNNING"
        job["started_at"] = datetime.now(timezone.utc)
        job["message"] = "Processing export job"
        
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Update job status to COMPLETED
        job["status"] = "COMPLETED"
        job["completed_at"] = datetime.now(timezone.utc)
        job["download_url"] = f"/api/v1/gis-export/download/{memory_job_id}"
        job["message"] = "Export completed successfully"
        
        logger.info(f"GIS export job {memory_job_id} processed in memory storage")
    except Exception as e:
        logger.error(f"Error processing GIS export job in memory: {e}", exc_info=True)

# API endpoints
@app.post("/plugins/v1/gis-export/run", response_model=GisExportJobBase)
async def create_export_job(request: GisExportRequest, background_tasks: BackgroundTasks):
    """Create a new GIS export job."""
    job_id = get_next_job_id()
    now = datetime.now(timezone.utc)
    
    # Try to use the database if available
    if async_session_factory:
        try:
            # Use SQLAlchemy text for raw SQL
            from sqlalchemy.sql import text
            
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                # Use raw SQL to insert job
                insert_query = text("""
                INSERT INTO gis_export_jobs (
                    job_id, county_id, export_format, status, 
                    area_of_interest_json, layers_json, parameters_json,
                    message, created_at, updated_at
                ) VALUES (
                    :job_id, :county_id, :export_format, :status,
                    :area_of_interest_json, :layers_json, :parameters_json,
                    :message, :created_at, :updated_at
                ) RETURNING job_id
                """)
                
                # Additional parameters/settings
                parameters = {"username": request.username}
                
                result = await session.execute(
                    insert_query,
                    {
                        "job_id": job_id,
                        "county_id": request.county_id,
                        "export_format": request.format,
                        "status": "PENDING",
                        "area_of_interest_json": request.area_of_interest,
                        "layers_json": request.layers,
                        "parameters_json": parameters,
                        "message": "GIS export job accepted and queued for processing.",
                        "created_at": now,
                        "updated_at": now
                    }
                )
                
                # Commit happens in context manager
                logger.info(f"Created GIS export job {job_id} in database")
                
                # Prepare response with simplified numeric job_id for API
                simple_numeric_id = int(job_id.split("-")[0], 16) % 10000
                
                # Response payload
                db_job = {
                    "job_id": simple_numeric_id,  # Convert UUID to simple ID for response only
                    "county_id": request.county_id,
                    "username": request.username,
                    "status": "PENDING",
                    "created_at": now
                }
                
                # Start processing the job in the background
                background_tasks.add_task(process_export_job, job_id)
                
                return db_job
                
        except Exception as e:
            logger.error(f"Error creating GIS export job in database: {e}", exc_info=True)
    
    # Fallback to in-memory storage
    # Convert the UUID string to a simple integer ID for the in-memory storage
    memory_job_id = int(job_id.split("-")[0], 16) % 10000
    
    job = {
        "job_id": memory_job_id,
        "county_id": request.county_id,
        "username": request.username,
        "status": "PENDING",
        "created_at": now,
        "message": "Job created, waiting to be processed"
    }
    
    # Store additional data in memory
    memory_job_data = {
        **job,
        "export_format": request.format,
        "area_of_interest": request.area_of_interest,
        "layers": request.layers,
    }
    
    EXPORT_JOBS[memory_job_id] = memory_job_data
    logger.info(f"Created GIS export job {memory_job_id} in memory storage (fallback)")
    
    # Start processing the job in the background
    # Use string job_id for process_export_job function
    background_tasks.add_task(process_export_job, job_id)
    
    return job

@app.get("/plugins/v1/gis-export/status/{job_id_param}", response_model=GisExportJobDetail)
async def get_job_status(job_id_param: int):
    """Get the status of a GIS export job."""
    # Try to use the database if available
    if async_session_factory:
        try:
            from sqlalchemy.sql import text
            
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                # Query by job_id pattern (using LIKE) to match UUIDs starting with this value
                # in hexadecimal format. This is not efficient but works for the demo
                query = text("""
                SELECT * FROM gis_export_jobs 
                WHERE job_id::text LIKE :id_prefix || '%'
                LIMIT 1
                """)
                
                # Convert integer ID back to a hex prefix
                id_prefix = format(job_id_param, 'x')
                
                result = await session.execute(query, {"id_prefix": id_prefix})
                job = result.mappings().first()
                
                if job:
                    # Extract username from parameters_json if available
                    job_username = "admin"  # Default
                    if job["parameters_json"] and "username" in job["parameters_json"]:
                        job_username = job["parameters_json"]["username"]
                    
                    # Build response
                    response = {
                        "job_id": job_id_param,  # Use the original simple ID for response
                        "county_id": job["county_id"],
                        "username": job_username,
                        "export_format": job["export_format"],
                        "status": job["status"],
                        "created_at": job["created_at"],
                        "started_at": job["started_at"],
                        "completed_at": job["completed_at"],
                        "area_of_interest": job["area_of_interest_json"],
                        "layers": job["layers_json"],
                        "message": job["message"]
                    }
                    
                    # Add download URL if job is completed
                    if job["status"] == "COMPLETED" and job["result_file_location"]:
                        response["download_url"] = f"/api/v1/gis-export/download/{job_id_param}"
                    
                    logger.info(f"Retrieved GIS export job {job_id_param} from database")
                    return response
                
        except Exception as e:
            logger.error(f"Error getting GIS export job from database: {e}", exc_info=True)
    
    # Fallback to in-memory storage
    if job_id_param not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    logger.info(f"Retrieved GIS export job {job_id_param} from memory storage (fallback)")
    return EXPORT_JOBS[job_id_param]

@app.get("/plugins/v1/gis-export/list", response_model=List[GisExportJobBase])
async def list_jobs(
    county_id: Optional[str] = None,
    username: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """List GIS export jobs with optional filtering."""
    # Try to use the database if available
    if async_session_factory:
        try:
            from sqlalchemy.sql import text
            
            async with managed_db_session() as session:
                if session is None:
                    raise ValueError("Database session not available")
                
                # Build a dynamic SQL query based on filters
                base_query = """
                SELECT 
                    job_id, county_id, export_format, status, 
                    message, created_at, updated_at, 
                    started_at, completed_at, parameters_json
                FROM gis_export_jobs
                """
                
                where_clauses = []
                params = {}
                
                if county_id:
                    where_clauses.append("county_id = :county_id")
                    params["county_id"] = county_id
                
                if status:
                    where_clauses.append("status = :status")
                    params["status"] = status
                
                # Add username filter by checking in parameters_json
                if username:
                    where_clauses.append("parameters_json->>'username' = :username")
                    params["username"] = username
                
                # Add WHERE clause if there are any filters
                if where_clauses:
                    base_query += " WHERE " + " AND ".join(where_clauses)
                
                # Add sorting and pagination
                base_query += " ORDER BY created_at DESC LIMIT :limit OFFSET :offset"
                params["limit"] = limit
                params["offset"] = offset
                
                # Execute the query with SQLAlchemy text
                query = text(base_query)
                result = await session.execute(query, params)
                db_jobs = result.mappings().all()
                
                # Transform database results to response model format
                response_jobs = []
                for job in db_jobs:
                    # Extract username from parameters_json if available
                    job_username = "admin"  # Default
                    if job["parameters_json"] and "username" in job["parameters_json"]:
                        job_username = job["parameters_json"]["username"]
                    
                    # Create a synthetic integer ID for the response
                    synthetic_id = int(job["job_id"].split("-")[0], 16) % 10000 if isinstance(job["job_id"], str) else job["job_id"]
                    
                    response_jobs.append({
                        "job_id": synthetic_id,
                        "county_id": job["county_id"],
                        "username": job_username,
                        "status": job["status"],
                        "created_at": job["created_at"],
                        "export_format": job["export_format"]
                    })
                
                logger.info(f"Listed {len(response_jobs)} GIS export jobs from database")
                return response_jobs
                
        except Exception as e:
            logger.error(f"Error listing GIS export jobs from database: {e}", exc_info=True)
    
    # Fallback to in-memory storage
    filtered_jobs = EXPORT_JOBS.values()
    
    if county_id:
        filtered_jobs = [job for job in filtered_jobs if job["county_id"] == county_id]
    
    if username:
        filtered_jobs = [job for job in filtered_jobs if job["username"] == username]
    
    if status:
        filtered_jobs = [job for job in filtered_jobs if job["status"] == status]
    
    # Sort by created_at (newest first) and apply pagination
    sorted_jobs = sorted(filtered_jobs, key=lambda job: job["created_at"], reverse=True)
    paginated_jobs = sorted_jobs[offset:offset + limit]
    
    logger.info(f"Listed {len(paginated_jobs)} GIS export jobs from memory storage (fallback)")
    return paginated_jobs

@app.delete("/plugins/v1/gis-export/cancel/{job_id}", response_model=GisExportJobBase)
async def cancel_job(job_id: int):
    """Cancel a GIS export job."""
    if job_id not in EXPORT_JOBS:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = EXPORT_JOBS[job_id]
    
    if job["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job with status {job['status']}")
    
    job["status"] = "CANCELLED"
    job["message"] = "Job cancelled by user"
    
    return job

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion GIS Export Service",
        "version": "0.1.0",
        "status": "running",
        "documentation": "/docs",
        "health": "/health"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "service": "TerraFusion GIS Export Service",
        "status": "healthy",
        "version": "0.1.0",
        "time": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)