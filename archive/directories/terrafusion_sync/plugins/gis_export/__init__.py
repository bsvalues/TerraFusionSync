"""
TerraFusion SyncService - GIS Export Plugin

This plugin provides functionality for exporting geographic data in various formats
such as GeoJSON, Shapefile, and KML.
"""

import logging
from fastapi import APIRouter

# Configure plugin logger
logger = logging.getLogger(__name__)

# Import the router from router.py and expose it as a module-level variable
try:
    from .router import router
    logger.info("GIS Export router imported successfully")
except ImportError as e:
    logger.error(f"Failed to import GIS Export router: {e}", exc_info=True)
    router = None

# Initialize metrics
try:
    from .metrics import GisExportMetrics
    GisExportMetrics.initialize(use_default_registry=True)
    logger.info("GIS Export metrics initialized")
except ImportError as e:
    logger.error(f"Failed to initialize GIS Export metrics: {e}", exc_info=True)

# Explicitly export the router for importing by the main plugins package
__all__ = ["router"]

logger.info("GIS Export plugin initialized")