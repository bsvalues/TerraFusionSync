"""
TerraFusion Platform - Authentication Module

This module provides authentication and authorization functionality
for the TerraFusion Platform.
"""

import logging
from typing import Dict, Any, Optional

from flask import Flask, session, g

from auth.decorators import requires_auth, requires_permission, requires_county_access, admin_only
from auth.jwt_utils import create_access_token, create_refresh_token, decode_token, blacklist_token

# Configure logging
logger = logging.getLogger(__name__)


def init_auth(app: Flask) -> None:
    """
    Initialize authentication for a Flask application.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing TerraFusion authentication module")
    
    # Import auth routes (will be registered within the routes module)
    from auth.routes import init_auth_routes
    
    # Initialize auth routes
    init_auth_routes(app)
    
    # Set up before_request handler to load user from session
    @app.before_request
    def load_user_from_session():
        """Load the authenticated user from session if available."""
        if 'token' in session:
            try:
                # Decode the token (this also validates it)
                token_data = decode_token(session['token'])
                # Store user info in Flask's g object for the current request
                g.user = token_data
            except Exception as e:
                logger.warning(f"Failed to decode token from session: {str(e)}")
                # Clear invalid token from session
                session.pop('token', None)
                g.user = None
    
    logger.info("TerraFusion authentication module initialized successfully")


# Export the decorators for easier imports
__all__ = [
    'init_auth',
    'requires_auth',
    'requires_permission',
    'requires_county_access',
    'admin_only',
    'create_access_token',
    'create_refresh_token',
    'decode_token',
    'blacklist_token'
]