"""
TerraFusion Platform - Authentication Error Handlers

This module provides error handlers for authentication and authorization errors.
"""
import logging
from typing import Tuple, Dict, Any, Union

from flask import Blueprint, render_template, jsonify, request

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
    logger.warning(f"401 Unauthorized: {str(e)}")
    
    # Check if request wants JSON
    if request.headers.get('Accept', '').startswith('application/json') or request.is_json:
        return jsonify({
            "error": "Unauthorized",
            "message": "Authentication is required to access this resource",
            "status_code": 401
        }), 401
    
    # Return HTML for web requests
    return render_template(
        'auth/error.html',
        title='Authentication Required',
        error_code=401,
        message='You need to sign in to access this page.'
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
    logger.warning(f"403 Forbidden: {str(e)}")
    
    # Check if request wants JSON
    if request.headers.get('Accept', '').startswith('application/json') or request.is_json:
        return jsonify({
            "error": "Forbidden",
            "message": "You don't have permission to access this resource",
            "status_code": 403
        }), 403
    
    # Return HTML for web requests
    return render_template(
        'auth/error.html',
        title='Access Denied',
        error_code=403,
        message='You don\'t have permission to access this page.'
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
    logger.warning(f"429 Too Many Requests: {str(e)}")
    
    # Check if request wants JSON
    if request.headers.get('Accept', '').startswith('application/json') or request.is_json:
        return jsonify({
            "error": "Too Many Requests",
            "message": "Rate limit exceeded. Please try again later.",
            "status_code": 429
        }), 429
    
    # Return HTML for web requests
    return render_template(
        'auth/error.html',
        title='Rate Limit Exceeded',
        error_code=429,
        message='Too many requests. Please try again later.'
    ), 429