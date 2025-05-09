"""
TerraFusion SyncService - Plugins

This package contains plugin modules that extend the functionality of the TerraFusion SyncService.
Plugins are registered with the main FastAPI application during startup.
"""

import logging
from fastapi import APIRouter

# Configure logging
logger = logging.getLogger(__name__)

# Main plugins router with prefix
plugins_router = APIRouter(prefix="/plugins/v1")

# Import and register plugin modules
try:
    from .reporting import router as reporting_router
    plugins_router.include_router(reporting_router, prefix="/reporting", tags=["reporting"])
    logger.info("Registered reporting plugin")
except ImportError as e:
    logger.warning(f"Could not register reporting plugin: {e}")

# Export the main plugins router
__all__ = ["plugins_router"]