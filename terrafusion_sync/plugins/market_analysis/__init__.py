"""
TerraFusion SyncService - Market Analysis Plugin

This plugin provides market analysis functionality for the TerraFusion platform, 
enabling trend analysis, comparable market area evaluation, and other real estate market metrics.
"""

from fastapi import APIRouter

from . import router as market_analysis_router

# Create the plugin router
plugin_name = "market_analysis"
plugin_router = APIRouter()

# Include the market analysis routes
plugin_router.include_router(market_analysis_router.router, prefix="")

__all__ = ["plugin_name", "plugin_router"]