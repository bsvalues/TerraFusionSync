"""
TerraFusion SyncService - Market Analysis Plugin

This plugin provides market analysis functionality for real estate data,
including trend analysis, comparable market area evaluation, and price metrics.

Capabilities:
- Price trend analysis by zip code
- Comparable market area identification
- Sales velocity metrics
- Property market valuation
- Price per square foot analytics
"""

import logging
from terrafusion_sync.plugins.market_analysis.router import plugin_router

# Configure plugin logger
logger = logging.getLogger(__name__)
logger.info("Market Analysis plugin initialized")

# Expose the router for registration with the main app
__all__ = ["plugin_router"]