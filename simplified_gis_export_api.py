"""
TerraFusion - Simplified GIS Export API

This script provides a simplified launcher for the GIS Export API, bypassing the
full TerraFusion SyncService infrastructure for faster testing and development.

Usage:
    python simplified_gis_export_api.py

This starts a FastAPI server with just the GIS Export endpoints enabled.
"""

import asyncio
import logging
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os
import sys
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import necessary modules without triggering other plugin imports
from terrafusion_sync.core_models import Base, GisExportJob

# Import directly from router module to avoid cross-plugin imports
import sys, os
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'terrafusion_sync/plugins/gis_export'))
from terrafusion_sync.database import get_async_session

# Directly import our GIS Export router, avoiding other plugin imports
from terrafusion_sync.plugins.gis_export.router import router as gis_export_router

# Database connection settings - use SQLite for simplicity in standalone mode
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./gis_export_test.db")

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Provide session dependency for FastAPI
async def get_async_session():
    async with async_session_maker() as session:
        yield session

# Context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created or verified")
    
    # Injecting the session dependency
    app.dependency_overrides = {
        # Override any existing session dependency in the router
        "get_async_session": get_async_session
    }
    
    yield
    
    # Shutdown: Close engine (optional as Python will handle this)
    logger.info("Shutting down simplified GIS Export API")

# Create FastAPI app with GIS Export router
app = FastAPI(
    title="TerraFusion GIS Export API (Simplified)",
    description="Standalone API for GIS Export functionality",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the GIS Export router
app.include_router(gis_export_router, prefix="/plugins/v1/gis-export", tags=["gis-export"])

# Health check endpoint at root
@app.get("/", tags=["health"])
async def root():
    return {
        "status": "healthy",
        "service": "simplified_gis_export_api",
        "message": "GIS Export API is running in standalone mode"
    }

# Main entry point
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8083))  # Different from market analysis (8082)
    logger.info(f"Starting simplified GIS Export API on port {port}")
    uvicorn.run("simplified_gis_export_api:app", host="0.0.0.0", port=port, reload=True)