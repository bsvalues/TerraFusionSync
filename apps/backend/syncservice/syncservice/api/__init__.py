"""
API package for the SyncService.

This package contains API endpoints for managing and interacting with the SyncService.
"""

# You can uncomment these imports once the modules are created
# from syncservice.api import health, sync, dashboard

# Import just sync for now to avoid circular imports
from syncservice.api import sync

__all__ = [
    'sync'
]