"""
Main entry point for the SyncService API.

This module configures and launches the FastAPI application with all required
dependencies and endpoints for the SyncService plugin.
"""

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from syncservice.api import health, sync
from syncservice.config import get_settings
from syncservice.utils.database import close_db_connections, init_db_connections
from syncservice.utils.event_bus import close_nats_connection, init_nats_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan events.
    
    This context manager handles startup and shutdown events for the FastAPI application.
    """
    # Startup: initialize connections
    logger.info("Initializing database connections")
    await init_db_connections()
    
    logger.info("Initializing NATS connection")
    await init_nats_connection()
    
    logger.info("Application startup complete")
    yield
    
    # Shutdown: close connections
    logger.info("Closing database connections")
    await close_db_connections()
    
    logger.info("Closing NATS connection")
    await close_nats_connection()
    
    logger.info("Application shutdown complete")


# Initialize FastAPI app with lifespan manager
app = FastAPI(
    title="TerraFusion SyncService",
    description="Service for syncing data between legacy PACS and CAMA systems",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sync.router, prefix="/sync", tags=["sync"])
app.include_router(health.router, prefix="/health", tags=["health"])


@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "status": "running",
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "syncservice.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug_mode,
    )
