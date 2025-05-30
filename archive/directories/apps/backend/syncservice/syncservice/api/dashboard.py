"""
Dashboard API for the SyncService.

This module provides endpoints for the SyncService dashboard.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from ..auth import verify_api_key

# Create router
router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

# Logger
logger = logging.getLogger("syncservice.api.dashboard")


@router.get("/", include_in_schema=False)
async def dashboard_root():
    """
    Redirect to the dashboard index page.
    
    Returns:
        RedirectResponse to the dashboard index page
    """
    return RedirectResponse(url="/dashboard/index.html")


@router.get("/compatibility", dependencies=[Depends(verify_api_key)])
async def get_compatibility_dashboard():
    """
    Get compatibility matrix dashboard data.
    
    Returns:
        Dashboard data for compatibility matrix
    """
    return {
        "title": "System Compatibility Matrix",
        "description": "Configure and manage system synchronization compatibilities",
        "url": "/compatibility.html",
    }


@router.get("/sync", dependencies=[Depends(verify_api_key)])
async def get_sync_dashboard():
    """
    Get sync dashboard data.
    
    Returns:
        Dashboard data for sync operations
    """
    return {
        "title": "Sync Operations Dashboard",
        "description": "Monitor and manage sync operations",
        "url": "/sync.html",
    }


@router.get("/metrics", dependencies=[Depends(verify_api_key)])
async def get_metrics_dashboard():
    """
    Get metrics dashboard data.
    
    Returns:
        Dashboard data for metrics and analytics
    """
    return {
        "title": "Metrics & Analytics",
        "description": "View system performance metrics and sync analytics",
        "url": "/metrics.html",
    }


@router.get("/features", dependencies=[Depends(verify_api_key)])
async def get_dashboard_features():
    """
    Get all available dashboard features.
    
    Returns:
        List of available dashboard features
    """
    return {
        "features": [
            {
                "id": "compatibility",
                "title": "System Compatibility Matrix",
                "description": "Configure and manage system compatibility with drag-and-drop interface",
                "icon": "diagram-3",
                "url": "/compatibility.html",
                "enabled": True,
            },
            {
                "id": "sync",
                "title": "Sync Operations",
                "description": "Monitor and manage ongoing and scheduled sync operations",
                "icon": "arrow-repeat",
                "url": "/sync.html",
                "enabled": False,
            },
            {
                "id": "metrics",
                "title": "Metrics & Analytics",
                "description": "View performance metrics and synchronization analytics",
                "icon": "graph-up",
                "url": "/metrics.html",
                "enabled": False,
            },
        ]
    }