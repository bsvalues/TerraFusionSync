"""
Authentication module for TerraFusion SyncService.

This module provides authentication and authorization functionality,
including County RBAC integration.
"""

import logging
import functools
from typing import Callable, Optional, Dict, Any

from flask import request, session, redirect, url_for, flash, jsonify

# Configure logging
logger = logging.getLogger(__name__)
logger.info("Initializing authentication module")

# Try to import County RBAC
try:
    from apps.backend.auth.county_rbac import (
        requires_county_permission,
        get_county_current_user,
        user_has_county_role,
        check_permission,
        init_county_auth_routes,
        COUNTY_RBAC_AVAILABLE
    )
    
    # Use County RBAC as the primary authentication system
    requires_auth = requires_county_permission("view_dashboard")
    get_current_user = get_county_current_user
    
    logger.info("County RBAC module loaded successfully")
except ImportError as e:
    # County RBAC not available, use fallback
    COUNTY_RBAC_AVAILABLE = False
    logger.warning(f"County RBAC module not available: {e}")
    
    # Basic authentication decorator
    def requires_auth(f: Callable) -> Callable:
        """
        Basic authentication decorator that checks if user is authenticated.
        """
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            if not session.get('authenticated', False):
                if request.content_type == 'application/json':
                    return jsonify({'error': 'Authentication required'}), 401
                else:
                    flash('You must be logged in to access this page', 'error')
                    return redirect(url_for('login_page'))
            return f(*args, **kwargs)
        return decorated
    
    def check_permission(permission: str) -> bool:
        """Fallback permission check."""
        return session.get('authenticated', False)
    
    def get_current_user() -> Optional[Dict[str, Any]]:
        """Fallback current user function."""
        return session.get('user')
    
    def init_county_auth_routes(app):
        """Fallback for County auth routes."""
        logger.warning("County auth routes not initialized (module not available)")

def init_auth_routes(app):
    """
    Initialize authentication routes.
    
    This is called from the main app.py to set up authentication routes.
    It uses County RBAC if available, otherwise falls back to basic auth.
    """
    # Set up County RBAC routes if available
    if COUNTY_RBAC_AVAILABLE:
        init_county_auth_routes(app)
        logger.info("County auth routes initialized")
    else:
        logger.warning("County RBAC not available, using fallback authentication")
        
        # Set up fallback auth routes here if needed
        # (Usually defined in the main app.py)