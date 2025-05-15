"""
TerraFusion Platform - Authentication Decorators

This module provides decorator functions for securing routes and endpoints
with JWT authentication and role-based access control.
"""

import logging
import functools
from typing import Callable, List, Union, Optional, Dict, Any

from flask import request, session, g, redirect, url_for, jsonify, current_app

from auth.jwt_utils import decode_token, validate_permissions, validate_county_access

# Configure logging
logger = logging.getLogger(__name__)


def requires_auth(redirect_to_login: bool = True) -> Callable:
    """
    Decorator to require authentication for API endpoints.
    
    Args:
        redirect_to_login: Whether to redirect to login page or return 401 JSON
        
    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check for token in session first (web app)
            token = session.get('token')
            
            # If not in session, try Authorization header (API)
            if not token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            # If still no token, redirect to login or return 401
            if not token:
                if redirect_to_login:
                    # Store the current URL for redirect after login
                    session['next'] = request.url
                    return redirect(url_for('auth.login'))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Validate token
            try:
                # Decode the token (also validates it)
                token_data = decode_token(token)
                
                # Store user info in Flask's g object for the current request
                g.user = token_data
                
                # Call the protected view function
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.warning(f"Authentication failed: {str(e)}")
                
                # Clear invalid token from session
                if 'token' in session:
                    session.pop('token', None)
                
                # Redirect or return 401 based on setting
                if redirect_to_login:
                    session['next'] = request.url
                    return redirect(url_for('auth.login'))
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Authentication failed: {str(e)}'
                    }), 401
        
        return decorated_function
    return decorator


def requires_permission(permissions: Union[str, List[str]], redirect_on_error: bool = False) -> Callable:
    """
    Decorator to require specific permissions for API endpoints.
    
    This decorator should be used after requires_auth.
    
    Args:
        permissions: Single permission string or list of permission strings
        redirect_on_error: Whether to redirect to error page or return 403 JSON
        
    Returns:
        Decorated function
    """
    # Convert single permission to list
    if isinstance(permissions, str):
        permissions = [permissions]
    
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.error("requires_permission used without requires_auth")
                if redirect_on_error:
                    return redirect(url_for('error_page', code=401))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Validate user permissions
            if not validate_permissions(g.user, permissions):
                username = g.user.get('username', 'unknown')
                role = g.user.get('role', 'unknown')
                user_permissions = g.user.get('permissions', [])
                
                logger.warning(
                    f"Permission denied: User {username} with role {role} and "
                    f"permissions {user_permissions} attempted to access endpoint "
                    f"{request.path} which requires permissions {permissions}"
                )
                
                if redirect_on_error:
                    return redirect(url_for('error_page', code=403))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'You do not have permission to access this resource'
                    }), 403
            
            # If permissions are valid, call the protected view function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def requires_county_access(county_id_param: str = 'county_id', redirect_on_error: bool = False) -> Callable:
    """
    Decorator to require access to a specific county.
    
    This decorator should be used after requires_auth.
    
    Args:
        county_id_param: Name of the URL parameter containing the county ID
        redirect_on_error: Whether to redirect to error page or return 403 JSON
        
    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.error("requires_county_access used without requires_auth")
                if redirect_on_error:
                    return redirect(url_for('error_page', code=401))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Get county ID from URL parameters, JSON body, or query parameters
            county_id = None
            
            if county_id_param in kwargs:
                # From URL parameter
                county_id = kwargs[county_id_param]
            elif request.is_json and county_id_param in request.json:
                # From JSON body
                county_id = request.json[county_id_param]
            elif county_id_param in request.args:
                # From query parameter
                county_id = request.args[county_id_param]
            
            if not county_id:
                logger.warning(f"County ID not found in request for {request.path}")
                if redirect_on_error:
                    return redirect(url_for('error_page', code=400))
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Missing county ID parameter: {county_id_param}'
                    }), 400
            
            # Validate county access
            if not validate_county_access(g.user, county_id):
                username = g.user.get('username', 'unknown')
                role = g.user.get('role', 'unknown')
                allowed_counties = g.user.get('county_ids', [])
                
                logger.warning(
                    f"County access denied: User {username} with role {role} and "
                    f"allowed counties {allowed_counties} attempted to access "
                    f"county {county_id} via endpoint {request.path}"
                )
                
                if redirect_on_error:
                    return redirect(url_for('error_page', code=403))
                else:
                    return jsonify({
                        'success': False,
                        'error': f'You do not have access to county: {county_id}'
                    }), 403
            
            # If county access is valid, call the protected view function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def admin_only(redirect_on_error: bool = False) -> Callable:
    """
    Decorator to restrict access to admin users only.
    
    This decorator should be used after requires_auth.
    
    Args:
        redirect_on_error: Whether to redirect to error page or return 403 JSON
        
    Returns:
        Decorated function
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                logger.error("admin_only used without requires_auth")
                if redirect_on_error:
                    return redirect(url_for('error_page', code=401))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Check if user has admin role
            user = g.user if hasattr(g, 'user') else {}
            if user.get('role') != 'Admin':
                username = user.get('username', 'unknown')
                role = user.get('role', 'unknown')
                logger.warning(f"Admin access denied: User {username} with role {role} attempted to access admin endpoint {request.path}")
                
                if redirect_on_error:
                    return redirect(url_for('error_page', code=403))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Admin access required'
                    }), 403
            
            # If user is admin, call the protected view function
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator