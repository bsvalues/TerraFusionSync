"""
TerraFusion SyncService - GIS Analysis Plugin

This plugin provides Geographic Information System (GIS) analysis capabilities
for county property data, including spatial querying, boundary analysis, 
and geographic visualizations.
"""

import logging
from fastapi import APIRouter

from terrafusion_sync.plugins.gis_analysis.router import router as gis_analysis_router
from terrafusion_sync.plugins.gis_analysis.metrics import init_metrics

# Configure logging
logger = logging.getLogger(__name__)

# Initialize metrics
init_metrics()

# Create plugin router
plugin_router = APIRouter(prefix="/api/gis-analysis", tags=["GIS Analysis"])

# Include sub-routers
plugin_router.include_router(gis_analysis_router)

logger.info("GIS Analysis plugin initialized")