"""
TerraFusion SyncService - Plugins

This package contains plugin modules that extend the functionality of the TerraFusion SyncService.
Plugins are registered with the main FastAPI application during startup.
"""

from fastapi import APIRouter

# Main plugins router with prefix
plugins_router = APIRouter(prefix="/plugins/v1")

# Import and register plugin modules here
# Example: from .some_plugin import router as some_plugin_router
# Then: plugins_router.include_router(some_plugin_router, prefix="/some_plugin", tags=["some_plugin"])

# This will be populated when plugins are imported and registered
__all__ = ["plugins_router"]