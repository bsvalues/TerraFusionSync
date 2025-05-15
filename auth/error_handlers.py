"""
TerraFusion Platform - Authentication Error Handlers

This module provides error handling for authentication-related errors.
"""
import logging
from typing import Dict, Any, Tuple, Optional

from flask import Blueprint, render_template, jsonify, request

logger = logging.getLogger(__name__)

# Create error blueprint for handling authentication errors
error_bp = Blueprint('error', __name__)


@error_bp.route('/unauthorized')
def unauthorized():
    """Handle unauthorized access (401 errors)."""
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'Authentication required',
            'error': 'unauthorized'
        }), 401
    
    return render_template(
        'auth/error.html',
        title='Authentication Required',
        message='You must log in to access this resource.',
        error_code='401'
    ), 401


@error_bp.route('/forbidden')
def forbidden():
    """Handle forbidden access (403 errors)."""
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'You do not have permission to access this resource',
            'error': 'forbidden'
        }), 403
    
    return render_template(
        'auth/error.html',
        title='Access Denied',
        message='You do not have permission to access this resource. ' +
                'If you believe this is an error, please contact your administrator.',
        error_code='403'
    ), 403


@error_bp.route('/bad_request')
def bad_request():
    """Handle bad request errors (400 errors)."""
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'Invalid request parameters',
            'error': 'bad_request'
        }), 400
    
    return render_template(
        'auth/error.html',
        title='Bad Request',
        message='The request was invalid. Please check your input and try again.',
        error_code='400'
    ), 400


@error_bp.app_errorhandler(401)
def handle_unauthorized_error(error):
    """Handle 401 errors."""
    logger.warning(f"Unauthorized error: {str(error)}")
    
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'Authentication required',
            'error': 'unauthorized'
        }), 401
    
    return render_template(
        'auth/error.html',
        title='Authentication Required',
        message='You must log in to access this resource.',
        error_code='401'
    ), 401


@error_bp.app_errorhandler(403)
def handle_forbidden_error(error):
    """Handle 403 errors."""
    logger.warning(f"Forbidden error: {str(error)}")
    
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'You do not have permission to access this resource',
            'error': 'forbidden'
        }), 403
    
    return render_template(
        'auth/error.html',
        title='Access Denied',
        message='You do not have permission to access this resource. ' +
                'If you believe this is an error, please contact your administrator.',
        error_code='403'
    ), 403


@error_bp.app_errorhandler(400)
def handle_bad_request_error(error):
    """Handle 400 errors."""
    logger.warning(f"Bad request error: {str(error)}")
    
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'The request was invalid',
            'error': 'bad_request'
        }), 400
    
    return render_template(
        'auth/error.html',
        title='Bad Request',
        message='The request was invalid. Please check your input and try again.',
        error_code='400'
    ), 400


@error_bp.app_errorhandler(404)
def handle_not_found_error(error):
    """Handle 404 errors."""
    logger.warning(f"Not found error: {request.path}")
    
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'The requested resource was not found',
            'error': 'not_found'
        }), 404
    
    return render_template(
        'auth/error.html',
        title='Not Found',
        message='The requested resource was not found. Please check the URL and try again.',
        error_code='404'
    ), 404


@error_bp.app_errorhandler(500)
def handle_server_error(error):
    """Handle 500 errors."""
    logger.error(f"Server error: {str(error)}")
    
    if _is_api_request():
        return jsonify({
            'success': False,
            'message': 'An internal server error occurred',
            'error': 'server_error'
        }), 500
    
    return render_template(
        'auth/error.html',
        title='Server Error',
        message='An internal server error occurred. Please try again later.',
        error_code='500'
    ), 500


def _is_api_request() -> bool:
    """
    Check if the current request is an API request.
    
    API requests typically accept JSON responses, contain an Authorization header,
    or are directed to paths starting with /api/.
    
    Returns:
        bool: True if the request is an API request, False otherwise
    """
    # Check if the request accepts JSON
    accepts_json = 'application/json' in request.headers.get('Accept', '')
    
    # Check if the request has an Authorization header
    has_auth_header = 'Authorization' in request.headers
    
    # Check if the request path starts with /api/
    is_api_path = request.path.startswith('/api/')
    
    # Return True if any of the conditions are met
    return accepts_json or has_auth_header or is_api_path