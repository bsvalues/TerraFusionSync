"""
TerraFusion Platform - Authentication Decorators

This module provides decorator functions for securing routes and endpoints
with JWT authentication and role-based access control.
"""
import functools
import logging
from typing import Callable, List, Union, Optional

from flask import request, redirect, url_for, session, flash, jsonify

from auth.jwt_utils import decode_token, validate_permissions, validate_county_access

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
            # Get token from header or session
            token = None
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
            else:
                token = session.get('token')
            
            # Check if token exists
            if not token:
                if redirect_to_login:
                    logger.warning(f"Unauthorized access attempt to {request.path}")
                    flash('Please log in to access this page', 'error')
                    return redirect(url_for('auth.login', next=request.path))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Authentication required',
                        'error': 'unauthorized'
                    }), 401
            
            try:
                # Decode and validate token
                token_payload = decode_token(token)
                
                # Store token payload in request for use in the route handler
                request.token_payload = token_payload
                
                return f(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Token validation failed: {str(e)}")
                
                if redirect_to_login:
                    flash('Your session has expired. Please log in again.', 'error')
                    return redirect(url_for('auth.login', next=request.path))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid or expired token',
                        'error': 'invalid_token'
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
            # Get token payload from request (set by requires_auth)
            token_payload = getattr(request, 'token_payload', None)
            
            if not token_payload:
                logger.warning(f"Permission check without token payload: {request.path}")
                if redirect_on_error:
                    flash('Authentication required', 'error')
                    return redirect(url_for('auth.login', next=request.path))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Authentication required',
                        'error': 'unauthorized'
                    }), 401
            
            # Check permissions
            if not validate_permissions(token_payload, permissions):
                username = token_payload.get('username', 'Unknown')
                role = token_payload.get('role', 'Unknown')
                user_permissions = token_payload.get('permissions', [])
                
                logger.warning(
                    f"Permission denied for user {username} (role: {role}): "
                    f"Required {permissions}, has {user_permissions}"
                )
                
                if redirect_on_error:
                    flash('You do not have permission to access this resource', 'error')
                    return redirect(url_for('error.forbidden'))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'You do not have permission to access this resource',
                        'error': 'forbidden',
                        'required_permissions': permissions
                    }), 403
            
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
            # Get token payload from request (set by requires_auth)
            token_payload = getattr(request, 'token_payload', None)
            
            if not token_payload:
                logger.warning(f"County access check without token payload: {request.path}")
                if redirect_on_error:
                    flash('Authentication required', 'error')
                    return redirect(url_for('auth.login', next=request.path))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Authentication required',
                        'error': 'unauthorized'
                    }), 401
            
            # Get county ID from URL params, query string, or form data
            county_id = kwargs.get(county_id_param)
            if county_id is None:
                county_id = request.args.get(county_id_param)
            if county_id is None and request.is_json:
                county_id = request.json.get(county_id_param)
            if county_id is None and request.form:
                county_id = request.form.get(county_id_param)
            
            if county_id is None:
                logger.warning(f"County ID parameter '{county_id_param}' not found in request")
                if redirect_on_error:
                    flash('County ID is required', 'error')
                    return redirect(url_for('error.bad_request'))
                else:
                    return jsonify({
                        'success': False,
                        'message': f"County ID parameter '{county_id_param}' is required",
                        'error': 'missing_parameter'
                    }), 400
            
            # Check county access
            if not validate_county_access(token_payload, county_id):
                username = token_payload.get('username', 'Unknown')
                role = token_payload.get('role', 'Unknown')
                user_county_ids = token_payload.get('county_ids', [])
                
                logger.warning(
                    f"County access denied for user {username} (role: {role}): "
                    f"Required access to {county_id}, has access to {user_county_ids}"
                )
                
                if redirect_on_error:
                    flash('You do not have access to the specified county', 'error')
                    return redirect(url_for('error.forbidden'))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'You do not have access to the specified county',
                        'error': 'forbidden',
                        'county_id': county_id
                    }), 403
            
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
            # Get token payload from request (set by requires_auth)
            token_payload = getattr(request, 'token_payload', None)
            
            if not token_payload:
                logger.warning(f"Admin check without token payload: {request.path}")
                if redirect_on_error:
                    flash('Authentication required', 'error')
                    return redirect(url_for('auth.login', next=request.path))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Authentication required',
                        'error': 'unauthorized'
                    }), 401
            
            # Check if user is admin
            if token_payload.get('role') != 'Admin':
                username = token_payload.get('username', 'Unknown')
                role = token_payload.get('role', 'Unknown')
                
                logger.warning(
                    f"Admin access denied for user {username} (role: {role})"
                )
                
                if redirect_on_error:
                    flash('Administrator access required', 'error')
                    return redirect(url_for('error.forbidden'))
                else:
                    return jsonify({
                        'success': False,
                        'message': 'Administrator access required',
                        'error': 'forbidden'
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator