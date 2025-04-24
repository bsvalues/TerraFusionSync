"""
Entry point for the SyncService API.

This module configures and launches the FastAPI application with all required
dependencies and endpoints for the SyncService plugin.
"""

import logging
import os
import sys

# Add the src directory to the Python path so syncservice module can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps/backend/syncservice/src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create a simple FastAPI app for testing
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TerraFusion SyncService",
    description="Service for syncing data between legacy PACS and CAMA systems",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["root"])
async def root():
    """Root endpoint providing basic service information."""
    return {
        "service": "TerraFusion SyncService",
        "version": "0.1.0",
        "status": "running",
    }

@app.get("/health/live", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "up",
        "service": "terrafusion-sync-service",
        "version": "0.1.0",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "syncservice:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )