"""
TerraFusion Platform - Authentication Decorators

This module provides decorators for authentication and authorization.
"""
import logging
import functools
from typing import Callable, Any, Dict, List, Optional, Union, TypeVar, cast

from flask import request, g, abort, jsonify, current_app

from auth.jwt_utils import get_current_user_from_token
from auth.config import has_permission, can_perform_action
from auth.audit import log_access_denied

logger = logging.getLogger(__name__)

F = TypeVar('F', bound=Callable[..., Any])

def jwt_required(f: F) -> F:
    """
    Decorator to require a valid JWT token.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        # Get the current user from the token
        current_user = get_current_user_from_token()
        
        if not current_user:
            logger.warning("JWT required but no valid token provided")
            abort(401, "Authentication required")
        
        # Store the current user in Flask's g object
        g.current_user = current_user
        
        return f(*args, **kwargs)
    
    return cast(F, decorated_function)

def role_required(role: Union[str, List[str]]) -> Callable[[F], F]:
    """
    Decorator to require a specific role or one of several roles.
    
    Args:
        role: Role name or list of role names
        
    Returns:
        Decorator function
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Get the current user from g
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("Role required but no authenticated user")
                abort(401, "Authentication required")
            
            # Check if the user has the required role
            user_role = current_user.get('role')
            required_roles = [role] if isinstance(role, str) else role
            
            if user_role not in required_roles:
                user_id = current_user.get('user_id')
                username = current_user.get('username')
                
                log_access_denied(
                    user_id=user_id,
                    username=username,
                    resource_type="role",
                    resource_id=str(role),
                    reason=f"User does not have required role(s): {', '.join(required_roles)}"
                )
                
                logger.warning(f"User {username} (role {user_role}) does not have required role(s): {', '.join(required_roles)}")
                abort(403, f"Insufficient permissions. Required role(s): {', '.join(required_roles)}")
            
            return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    
    return decorator

def permission_required(permission: Union[str, List[str]]) -> Callable[[F], F]:
    """
    Decorator to require a specific permission or one of several permissions.
    
    Args:
        permission: Permission name or list of permission names
        
    Returns:
        Decorator function
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Get the current user from g
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("Permission required but no authenticated user")
                abort(401, "Authentication required")
            
            # Check if the user has the required permission
            user_role = current_user.get('role')
            required_permissions = [permission] if isinstance(permission, str) else permission
            
            has_any_permission = False
            for perm in required_permissions:
                if has_permission(user_role, perm):
                    has_any_permission = True
                    break
            
            if not has_any_permission:
                user_id = current_user.get('user_id')
                username = current_user.get('username')
                
                log_access_denied(
                    user_id=user_id,
                    username=username,
                    resource_type="permission",
                    resource_id=str(permission),
                    reason=f"User does not have required permission(s): {', '.join(required_permissions)}"
                )
                
                logger.warning(f"User {username} (role {user_role}) does not have required permission(s): {', '.join(required_permissions)}")
                abort(403, f"Insufficient permissions. Required permission(s): {', '.join(required_permissions)}")
            
            return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    
    return decorator

def county_access_required(county_id_param: str = 'county_id') -> Callable[[F], F]:
    """
    Decorator to require access to a specific county.
    
    Args:
        county_id_param: Name of the parameter containing the county ID
        
    Returns:
        Decorator function
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Get the current user from g
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("County access required but no authenticated user")
                abort(401, "Authentication required")
            
            # Get the county ID from parameters or JSON body
            county_id = None
            
            # First try to get from URL parameters
            if county_id_param in kwargs:
                county_id = kwargs[county_id_param]
            
            # Then try to get from request body
            if county_id is None and request.is_json:
                county_id = request.json.get(county_id_param)
            
            # Then try to get from form data
            if county_id is None and request.form:
                county_id = request.form.get(county_id_param)
            
            # Then try to get from query string
            if county_id is None:
                county_id = request.args.get(county_id_param)
            
            if county_id is None:
                logger.warning(f"County access required but {county_id_param} not found in request")
                abort(400, f"County ID ({county_id_param}) is required")
            
            # Check if the user has access to the county
            user_county_ids = current_user.get('county_ids', [])
            
            # ITAdmin can access all counties
            if current_user.get('role') == 'ITAdmin':
                return f(*args, **kwargs)
            
            # Otherwise, check the county list
            if not user_county_ids or county_id not in user_county_ids:
                user_id = current_user.get('user_id')
                username = current_user.get('username')
                
                log_access_denied(
                    user_id=user_id,
                    username=username,
                    resource_type="county",
                    resource_id=county_id,
                    reason=f"User does not have access to county: {county_id}"
                )
                
                logger.warning(f"User {username} does not have access to county: {county_id}")
                abort(403, f"You do not have access to county: {county_id}")
            
            return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    
    return decorator

def resource_action_required(resource: str, action: str) -> Callable[[F], F]:
    """
    Decorator to require permission to perform an action on a resource.
    
    Args:
        resource: Resource name
        action: Action name
        
    Returns:
        Decorator function
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Get the current user from g
            current_user = getattr(g, 'current_user', None)
            
            if not current_user:
                logger.warning("Resource action required but no authenticated user")
                abort(401, "Authentication required")
            
            # Check if the user can perform the action
            user_role = current_user.get('role')
            
            if not can_perform_action(user_role, resource, action):
                user_id = current_user.get('user_id')
                username = current_user.get('username')
                
                log_access_denied(
                    user_id=user_id,
                    username=username,
                    resource_type=resource,
                    resource_id=None,
                    reason=f"User cannot perform action '{action}' on resource '{resource}'"
                )
                
                logger.warning(f"User {username} (role {user_role}) cannot perform action '{action}' on resource '{resource}'")
                abort(403, f"Insufficient permissions to perform {action} on {resource}")
            
            return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    
    return decorator

def rate_limit(limit: int, period: int) -> Callable[[F], F]:
    """
    Decorator to apply rate limiting to a route.
    
    Args:
        limit: Maximum number of requests
        period: Time period in seconds
        
    Returns:
        Decorator function
    """
    def decorator(f: F) -> F:
        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Get the client's IP address
            ip_address = request.remote_addr or 'unknown'
            
            # Check if rate limiting is enabled
            if not hasattr(current_app, 'rate_limiter'):
                logger.warning("Rate limiting is not configured")
                return f(*args, **kwargs)
            
            # Check if the client has exceeded the rate limit
            rate_limiter = current_app.rate_limiter
            key = f"{request.path}:{ip_address}"
            
            if not rate_limiter.is_allowed(key, limit, period):
                user_id = None
                username = None
                
                # If user is authenticated, get their details
                current_user = getattr(g, 'current_user', None)
                if current_user:
                    user_id = current_user.get('user_id')
                    username = current_user.get('username')
                
                log_access_denied(
                    user_id=user_id,
                    username=username,
                    resource_type="rate_limit",
                    resource_id=request.path,
                    reason=f"Rate limit exceeded: {limit} requests per {period} seconds"
                )
                
                logger.warning(f"Rate limit exceeded for {ip_address} on {request.path}")
                
                response = jsonify({
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded: {limit} requests per {period} seconds"
                })
                response.status_code = 429
                retry_after = rate_limiter.get_retry_after(key, period)
                if retry_after > 0:
                    response.headers['Retry-After'] = str(retry_after)
                
                return response
            
            return f(*args, **kwargs)
        
        return cast(F, decorated_function)
    
    return decorator

def add_security_headers(f: F) -> F:
    """
    Decorator to add security headers to responses.
    
    Args:
        f: The function to decorate
        
    Returns:
        Decorated function
    """
    @functools.wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        response = f(*args, **kwargs)
        
        # Add security headers from config
        from auth.config import SECURITY_HEADERS
        
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        
        return response
    
    return cast(F, decorated_function)