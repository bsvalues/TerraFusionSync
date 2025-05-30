"""
Azure-integrated version of the TerraFusion SyncService.

This is a modified version of syncservice.py configured to run in Azure App Service with
Application Insights monitoring integrated.
"""

import os
import sys
import logging
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import Application Insights integration
from app_insights_integration import setup_app_insights_for_fastapi, track_custom_event, track_exception

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TerraFusion Sync Service",
    description="Azure-integrated version of the TerraFusion synchronization service",
    version="1.0.0-azure",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up Azure Application Insights
app_insights_middleware = setup_app_insights_for_fastapi(app)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    # Convert to asyncpg format
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Set up async database connection
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,
    pool_pre_ping=True,
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency to get database session
async def get_db():
    """Dependency for getting an async database session."""
    db = AsyncSessionLocal()
    try:
        yield db
    finally:
        await db.close()

# Middleware for logging and tracking requests
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Middleware for logging and tracking all requests."""
    start_time = asyncio.get_event_loop().time()
    
    # Track the request in Application Insights
    track_custom_event("syncservice_request", {
        "path": request.url.path,
        "method": request.method,
    })
    
    try:
        response = await call_next(request)
        
        # Track response time
        process_time = (asyncio.get_event_loop().time() - start_time) * 1000
        response.headers["X-Process-Time"] = str(process_time)
        
        # Track successful response
        track_custom_event("syncservice_response", {
            "path": request.url.path,
            "method": request.method,
            "status_code": response.status_code,
            "process_time_ms": process_time
        })
        
        return response
    except Exception as e:
        # Track exception
        track_exception(e)
        raise

# Basic health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check database connection
        async with AsyncSessionLocal() as session:
            result = await session.execute("SELECT 1")
            await result.fetchone()
        
        return {
            "service": "TerraFusion SyncService",
            "status": "healthy",
            "version": "Azure Edition 1.0.0",
            "time": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        track_exception(e)
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Import and register plugins
# This will need to be adapted to your specific plugin structure
from terrafusion_sync.plugins import register_all_plugins
register_all_plugins(app)

# Special Azure-specific endpoints
@app.get("/azure-readiness")
async def azure_readiness():
    """Readiness probe for Azure."""
    return {"status": "ready", "service": "TerraFusion SyncService"}

@app.get("/azure-liveness")
async def azure_liveness():
    """Liveness probe for Azure."""
    return {"status": "alive", "service": "TerraFusion SyncService"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment variable or use default
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting TerraFusion Azure-integrated SyncService on port {port}")
    
    uvicorn.run(
        "syncservice_azure:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=True,
    )