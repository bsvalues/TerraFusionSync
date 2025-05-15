"""
TerraFusion Platform - Authentication Decorators

This module provides decorators for securing routes and APIs with authentication and authorization.
"""
import logging
from functools import wraps
from typing import Callable, Union, List, Optional, Dict, Any, cast

from flask import request, redirect, url_for, session, jsonify, g, current_app
from werkzeug.local import LocalProxy

from auth.jwt_utils import get_token_from_header, verify_token
from auth.config import ROLE_PERMISSIONS

logger = logging.getLogger(__name__)

def jwt_required(f: Callable) -> Callable:
    """
    Decorator to require a valid JWT token for API routes.
    
    This decorator extracts the JWT token from the Authorization header,
    verifies it, and makes the payload available in request.token_payload.
    
    If the token is invalid, returns a 401 Unauthorized response.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Get the token from the Authorization header
        auth_header = request.headers.get('Authorization')
        success, token, error = get_token_from_header(auth_header)
        
        if not success:
            logger.warning(f"JWT authentication failed: {error}")
            return jsonify({"error": "Authentication required", "message": error}), 401
        
        # Verify the token
        success, payload, error = verify_token(token)
        
        if not success:
            logger.warning(f"JWT verification failed: {error}")
            return jsonify({"error": "Invalid token", "message": error}), 401
        
        # Store token payload in request
        g.token_payload = payload
        
        # Store user identity for easy access
        g.current_user = {
            "user_id": payload.get("sub"),
            "username": payload.get("username"),
            "role": payload.get("role"),
            "county_ids": payload.get("county_ids", [])
        }
        
        logger.debug(f"JWT authentication successful for user {g.current_user['username']}")
        return f(*args, **kwargs)
    
    return decorated

def session_required(f: Callable) -> Callable:
    """
    Decorator to require a valid session for web routes.
    
    This decorator checks if the user is logged in via session,
    redirects to login page if not.
    """
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Check if user is logged in via session
        if 'user_id' not in session:
            logger.info("Session authentication failed: User not logged in")
            return redirect(url_for('auth.login', next=request.path))
        
        # Store user identity for easy access
        g.current_user = {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role"),
            "county_ids": session.get("county_ids", [])
        }
        
        logger.debug(f"Session authentication successful for user {g.current_user.get('username')}")
        return f(*args, **kwargs)
    
    return decorated

def role_required(role: str) -> Callable:
    """
    Decorator factory to require a specific role for routes.
    
    This decorator checks if the user has the specified role,
    returning a 403 Forbidden response if not.
    
    Args:
        role: Required role (e.g., 'ITAdmin', 'Assessor', 'Staff')
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            # Get current user from g object
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("Role check failed: No authenticated user")
                return handle_authorization_error("Authentication required")
            
            user_role = current_user.get('role')
            
            # Check if the user has the required role
            if user_role != role and user_role != 'ITAdmin':  # ITAdmin has access to everything
                logger.warning(f"Role check failed: User {current_user.get('username')} with role {user_role} attempted to access resource requiring role {role}")
                return handle_authorization_error(f"Role '{role}' required")
            
            logger.debug(f"Role check successful for user {current_user.get('username')} with role {user_role}")
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def permission_required(permission: Union[str, List[str]]) -> Callable:
    """
    Decorator factory to require specific permissions for routes.
    
    This decorator checks if the user has the specified permission(s),
    returning a 403 Forbidden response if not.
    
    Args:
        permission: Required permission or list of permissions
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            # Get current user from g object
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("Permission check failed: No authenticated user")
                return handle_authorization_error("Authentication required")
            
            user_role = current_user.get('role')
            
            # ITAdmin role has all permissions
            if user_role == 'ITAdmin':
                return f(*args, **kwargs)
            
            # Get permissions for the user's role
            role_perms = ROLE_PERMISSIONS.get(user_role, [])
            
            # Convert single permission to list for consistent handling
            required_permissions = [permission] if isinstance(permission, str) else permission
            
            # Check if the user has all the required permissions
            for perm in required_permissions:
                if perm not in role_perms and '*' not in role_perms:
                    logger.warning(f"Permission check failed: User {current_user.get('username')} with role {user_role} lacks permission {perm}")
                    return handle_authorization_error(f"Permission '{perm}' required")
            
            logger.debug(f"Permission check successful for user {current_user.get('username')} with role {user_role}")
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def county_access_required(county_id_param: str = 'county_id') -> Callable:
    """
    Decorator factory to require access to a specific county.
    
    This decorator checks if the user has access to the county specified
    in the route parameter or request data, returning a 403 Forbidden response if not.
    
    Args:
        county_id_param: Name of the route parameter or request field containing the county ID
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            # Get current user from g object
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("County access check failed: No authenticated user")
                return handle_authorization_error("Authentication required")
            
            # Get the county ID from route params, query params, or request data
            county_id = None
            
            if county_id_param in kwargs:
                county_id = kwargs.get(county_id_param)
            elif request.method == 'GET' and county_id_param in request.args:
                county_id = request.args.get(county_id_param)
            elif request.is_json and county_id_param in request.json:
                county_id = request.json.get(county_id_param)
            elif request.form and county_id_param in request.form:
                county_id = request.form.get(county_id_param)
                
            if not county_id:
                logger.warning(f"County access check failed: No county ID found in parameter {county_id_param}")
                return handle_authorization_error(f"County ID is required")
            
            user_role = current_user.get('role')
            user_county_ids = current_user.get('county_ids', [])
            
            # ITAdmin role has access to all counties
            if user_role == 'ITAdmin':
                return f(*args, **kwargs)
            
            # Check if the user has access to the specified county
            if county_id not in user_county_ids and '*' not in user_county_ids:
                logger.warning(f"County access check failed: User {current_user.get('username')} attempted to access county {county_id} without permission")
                return handle_authorization_error(f"Access to county '{county_id}' is not authorized")
            
            logger.debug(f"County access check successful for user {current_user.get('username')} accessing county {county_id}")
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator

def handle_authorization_error(message: str) -> Any:
    """
    Handle authorization errors based on request type.
    
    For API requests, returns a JSON 403 Forbidden response.
    For HTML requests, redirects to the unauthorized page.
    
    Args:
        message: Error message
    
    Returns:
        Either a JSON response or redirect
    """
    # Check if request wants JSON
    if request.headers.get('Accept', '').startswith('application/json') or request.is_json:
        return jsonify({"error": "Forbidden", "message": message}), 403
    
    # For HTML requests, redirect to the login page or unauthorized page
    if 'user_id' in session:
        # User is logged in but doesn't have permission
        return redirect(url_for('auth.unauthorized', message=message))
    else:
        # User is not logged in
        return redirect(url_for('auth.login', next=request.path))

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user.
    
    Returns:
        Dictionary with user data or None if not authenticated
    """
    return getattr(g, 'current_user', None)

# Create a proxy for easier access to the current user
current_user = cast(Dict[str, Any], LocalProxy(get_current_user))