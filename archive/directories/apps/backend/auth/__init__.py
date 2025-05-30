"""
TerraFusion SyncService - Authentication Package

This package provides authentication and authorization for the
TerraFusion SyncService platform.
"""

import logging

# Configure logger
logger = logging.getLogger(__name__)

def init_app(app):
    """
    Initialize authentication for a Flask application.
    
    Args:
        app: Flask application instance
    """
    # Import the county RBAC module
    from .county_rbac import init_auth_routes
    
    # Initialize authentication routes
    init_auth_routes(app)
    
    logger.info("County RBAC module loaded successfully")
    logger.info("County auth routes initialized")