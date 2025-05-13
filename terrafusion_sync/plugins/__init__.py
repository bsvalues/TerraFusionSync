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

# Import and register Market Analysis plugin
try:
    from .market_analysis import plugin_router as market_analysis_router
    plugins_router.include_router(market_analysis_router, prefix="/market-analysis", tags=["market-analysis"])
    logger.info("Registered market analysis plugin")
except ImportError as e:
    logger.warning(f"Could not register market analysis plugin: {e}")

# Import and register GIS Export plugin
try:
    from .gis_export.router import router as gis_export_router
    plugins_router.include_router(gis_export_router, prefix="/gis-export", tags=["gis-export"])
    logger.info("Registered GIS export plugin")
except ImportError as e:
    logger.warning(f"Could not register GIS export plugin: {e}")

# Export the main plugins router
__all__ = ["plugins_router"]