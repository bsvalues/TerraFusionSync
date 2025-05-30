"""
API package for the SyncService.

This package contains the API endpoints for the SyncService.
"""

# Import API modules
from . import dashboard
from . import compatibility

# For backward compatibility
try:
    from . import sync
except ImportError:
    # sync module may not exist yet
    pass