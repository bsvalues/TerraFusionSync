"""
API module for SyncService.

This module provides API endpoints for the SyncService, including health checks,
sync operations, and dashboard functionality.
"""

# Import sub-modules for easy access
from syncservice.api import health, sync, dashboard

__all__ = ["health", "sync", "dashboard"]