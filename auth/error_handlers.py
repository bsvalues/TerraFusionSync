"""
TerraFusion Platform - Authentication Error Handlers

This module provides error handlers for authentication and authorization errors.
"""
import logging
from typing import Any, Dict, Tuple, Union

from flask import Blueprint, render_template, request, jsonify

from auth.audit import log_access_denied

logger = logging.getLogger(__name__)

# Create a Blueprint for error handlers
error_handlers = Blueprint('error_handlers', __name__)

@error_handlers.app_errorhandler(401)
def unauthorized_error(e: Any) -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle 401 Unauthorized errors.
    
    Args:
        e: Exception object
        
    Returns:
        Rendered template or JSON response
    """
    message = str(e) or "Authentication required"
    
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    logger.warning(f"Unauthorized error: {message}")
    
    if is_api_request:
        return jsonify({
            "error": "Unauthorized",
            "message": message
        }), 401
    
    return render_template(
        'auth/error.html',
        title='Authentication Required',
        error_code=401,
        message=message
    ), 401

@error_handlers.app_errorhandler(403)
def forbidden_error(e: Any) -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle 403 Forbidden errors.
    
    Args:
        e: Exception object
        
    Returns:
        Rendered template or JSON response
    """
    message = str(e) or "You do not have permission to access this resource"
    
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    # Get details from error object if available
    details = {}
    user_id = None
    username = None
    resource_type = "endpoint"
    resource_id = request.path
    
    if hasattr(e, 'user_id'):
        user_id = e.user_id
        details['user_id'] = user_id
    
    if hasattr(e, 'username'):
        username = e.username
        details['username'] = username
    
    if hasattr(e, 'resource_type'):
        resource_type = e.resource_type
        details['resource_type'] = resource_type
    
    if hasattr(e, 'resource_id'):
        resource_id = e.resource_id
        details['resource_id'] = resource_id
    
    # Log the access denied event
    log_access_denied(
        user_id=user_id,
        username=username,
        resource_type=resource_type,
        resource_id=resource_id,
        reason=message
    )
    
    logger.warning(f"Forbidden error: {message}")
    
    if is_api_request:
        return jsonify({
            "error": "Forbidden",
            "message": message
        }), 403
    
    return render_template(
        'auth/error.html',
        title='Access Denied',
        error_code=403,
        message=message
    ), 403

@error_handlers.app_errorhandler(429)
def too_many_requests_error(e: Any) -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle 429 Too Many Requests errors (rate limiting).
    
    Args:
        e: Exception object
        
    Returns:
        Rendered template or JSON response
    """
    message = str(e) or "Too many requests. Please try again later."
    
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    # Get retry-after header if available
    retry_after = None
    if hasattr(e, 'retry_after'):
        retry_after = e.retry_after
    
    logger.warning(f"Rate limit exceeded: {message}")
    
    if is_api_request:
        response = jsonify({
            "error": "Too Many Requests",
            "message": message
        })
        if retry_after:
            response.headers['Retry-After'] = str(retry_after)
        return response, 429
    
    return render_template(
        'auth/error.html',
        title='Too Many Requests',
        error_code=429,
        message=message,
        retry_after=retry_after
    ), 429