"""
TerraFusion Platform - Authentication Decorators

This module provides decorator functions for securing routes and endpoints
with JWT authentication and role-based access control.
"""

import logging
from functools import wraps
from typing import List, Union, Callable, Optional

from flask import request, redirect, url_for, session, g, jsonify
from jwt.exceptions import InvalidTokenError

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
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if authenticated
            try:
                # First try to get token from Authorization header
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    # Decode and validate the token
                    payload = decode_token(token)
                    # Store user info in Flask's g object for the current request
                    g.user = payload
                    # Continue to the wrapped function
                    return f(*args, **kwargs)
                    
                # Then try to get token from session
                elif 'token' in session:
                    token = session['token']
                    # Decode and validate the token
                    payload = decode_token(token)
                    # Store user info in Flask's g object for the current request
                    g.user = payload
                    # Continue to the wrapped function
                    return f(*args, **kwargs)
                
                # No valid authentication found
                else:
                    if redirect_to_login:
                        # Store the requested URL in session for redirect after login
                        session['next'] = request.path
                        return redirect(url_for('login_page'))
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Authentication required'
                        }), 401
                        
            except InvalidTokenError as e:
                # Token is invalid or expired
                logger.warning(f"Invalid token: {str(e)}")
                if 'token' in session:
                    # Clear the invalid token from session
                    session.pop('token', None)
                    
                if redirect_to_login:
                    # Redirect to login page
                    return redirect(url_for('login_page'))
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Invalid authentication token: {str(e)}'
                    }), 401
                    
            except Exception as e:
                # Unexpected error during authentication
                logger.error(f"Authentication error: {str(e)}")
                if redirect_to_login:
                    return redirect(url_for('login_page'))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication error'
                    }), 500
                
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
    if isinstance(permissions, str):
        permissions = [permissions]
        
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                if redirect_on_error:
                    return redirect(url_for('error_page', code=401))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Check if user has the required permissions
            user = g.user if hasattr(g, 'user') else {}
            if not validate_permissions(user, permissions):
                username = user.get('username', 'unknown')
                role = user.get('role', 'unknown')
                logger.warning(f"Permission denied: User {username} with role {role} attempted to access {request.path} requiring permissions {permissions}")
                
                if redirect_on_error:
                    return redirect(url_for('error_page', code=403))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Insufficient permissions'
                    }), 403
            
            # Continue to the wrapped function
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
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                if redirect_on_error:
                    return redirect(url_for('error_page', code=401))
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Authentication required'
                    }), 401
            
            # Get county ID from URL parameters
            county_id = kwargs.get(county_id_param)
            
            # If county_id is not in URL parameters, try to get it from query string
            if not county_id:
                county_id = request.args.get(county_id_param)
                
            # If county_id is not in query string, try to get it from form data
            if not county_id and request.method in ['POST', 'PUT']:
                if request.content_type == 'application/json':
                    county_id = request.json.get(county_id_param)
                else:
                    county_id = request.form.get(county_id_param)
            
            # If county_id is not found, allow access (no county-specific restriction)
            if not county_id:
                return f(*args, **kwargs)
                
            # Check if user has access to the specified county
            user = g.user if hasattr(g, 'user') else {}
            if not validate_county_access(user, county_id):
                username = user.get('username', 'unknown')
                role = user.get('role', 'unknown')
                logger.warning(f"County access denied: User {username} with role {role} attempted to access county {county_id}")
                
                if redirect_on_error:
                    return redirect(url_for('error_page', code=403))
                else:
                    return jsonify({
                        'success': False,
                        'error': f'Access to county {county_id} denied'
                    }), 403
            
            # Continue to the wrapped function
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
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
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
            
            # Continue to the wrapped function
            return f(*args, **kwargs)
            
        return decorated_function
    return decorator