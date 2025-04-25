"""
API package for TerraFusion SyncService platform.

This package provides API blueprints and routes for the platform.
"""

# Import blueprints to make them available to the main application
try:
    from .sync_operations import sync_bp
except ImportError:
    # This will be logged by the main application
    pass