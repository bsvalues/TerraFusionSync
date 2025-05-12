"""
TerraFusion SyncService - Market Analysis Plugin

This plugin provides market analysis functionality for the TerraFusion platform, 
enabling trend analysis, comparable market area evaluation, and other real estate market metrics.
"""

from fastapi import APIRouter

# Create the plugin router
plugin_name = "market_analysis"
plugin_router = APIRouter()

# Import and include the market analysis routes
from . import router
plugin_router.include_router(router.router, prefix="")

__all__ = ["plugin_name", "plugin_router"]