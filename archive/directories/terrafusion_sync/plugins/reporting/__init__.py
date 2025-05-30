"""
TerraFusion SyncService - Reporting Plugin

This plugin provides reporting functionality for TerraFusion SyncService, allowing
users to generate various reports based on property assessment data.
"""

from fastapi import APIRouter
from .routes import router as reporting_router

# Re-export the router for plugin registration
router = APIRouter()
router.include_router(reporting_router, prefix="")

__all__ = ["router"]