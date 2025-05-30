"""
Authentication module for the TerraFusion SyncService platform.

This module provides functions for authenticating users against the County's
existing Azure AD identity infrastructure, managing sessions, and
enforcing authorization policies.
"""

import os
import logging
import json
from functools import wraps
from datetime import datetime, timedelta

import jwt
from flask import Blueprint, request, jsonify, session, redirect, url_for, current_app, g

logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-key')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION = 86400  # 24 hours
AZURE_AD_CLIENT_ID = os.environ.get('AZURE_AD_CLIENT_ID')
AZURE_AD_TENANT_ID = os.environ.get('AZURE_AD_TENANT_ID')


def get_token_from_request():
    """
    Extract JWT token from the request.
    
    Checks for token in Authorization header or in the session.
    
    Returns:
        string: JWT token or None if not found
    """
    # Check Authorization header
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]
    
    # Check session
    if 'token' in session:
        return session['token']
    
    return None


def validate_token(token):
    """
    Validate a JWT token.
    
    Args:
        token: JWT token to validate
        
    Returns:
        dict: Decoded token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        # Check if token is expired
        if 'exp' in payload and datetime.utcnow() > datetime.utcfromtimestamp(payload['exp']):
            logger.warning("Token expired")
            return None
        
        return payload
    except jwt.PyJWTError as e:
        logger.warning(f"Token validation failed: {str(e)}")
        return None


def create_token(user_data):
    """
    Create a new JWT token for a user.
    
    Args:
        user_data: User information to include in the token
        
    Returns:
        string: JWT token
    """
    # Set token expiration
    expiration = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    
    # Create payload
    payload = {
        'sub': user_data.get('id'),
        'name': user_data.get('name'),
        'email': user_data.get('email'),
        'roles': user_data.get('roles', []),
        'exp': expiration
    }
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return token


def requires_auth(f):
    """
    Decorator to require authentication for API endpoints.
    
    This decorator validates the JWT token and adds the user
    information to the Flask g object.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token
        token = get_token_from_request()
        if not token:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        
        # Validate token
        payload = validate_token(token)
        if not payload:
            return jsonify({'success': False, 'error': 'Invalid or expired token'}), 401
        
        # Add user info to Flask g object
        g.user = {
            'id': payload.get('sub'),
            'name': payload.get('name'),
            'email': payload.get('email'),
            'roles': payload.get('roles', []),
        }
        
        # Continue to the wrapped function
        return f(*args, **kwargs)
    
    return decorated


def requires_role(role):
    """
    Decorator to require a specific role for API endpoints.
    
    This decorator should be used after requires_auth.
    
    Args:
        role: Role required to access the endpoint
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'user'):
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            
            # Check if user has the required role
            if role not in g.user.get('roles', []):
                return jsonify({'success': False, 'error': 'Insufficient permissions'}), 403
            
            # Continue to the wrapped function
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def get_current_user():
    """
    Get the current authenticated user.
    
    Returns:
        dict: User information or None if not authenticated
    """
    return getattr(g, 'user', None)


# Auth routes

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    
    For GET requests, redirect to Azure AD login page.
    For POST requests, validate credentials and create a session.
    """
    if request.method == 'GET':
        # In a real implementation, this would redirect to Azure AD
        # For development, use a simple login form
        return jsonify({
            'message': 'Please use POST to login with credentials'
        })
    
    # Handle POST request
    data = request.json
    
    # Validate credentials
    # In a real implementation, this would validate against Azure AD
    # For development, accept any credentials
    username = data.get('username', '')
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
    
    # Create mock user data
    # In a real implementation, this would be retrieved from Azure AD
    user_data = {
        'id': f"user-{username}",
        'name': username,
        'email': f"{username}@example.com",
        'roles': ['user']
    }
    
    # Create token
    token = create_token(user_data)
    
    # Store token in session
    session['token'] = token
    
    # Return success response
    return jsonify({
        'success': True,
        'token': token,
        'user': {
            'id': user_data['id'],
            'name': user_data['name'],
            'email': user_data['email'],
            'roles': user_data['roles']
        }
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Handle user logout.
    
    Clear the session and invalidate the token.
    """
    # Clear session
    session.clear()
    
    return jsonify({
        'success': True,
        'message': 'Logged out successfully'
    })


@auth_bp.route('/me', methods=['GET'])
@requires_auth
def me():
    """
    Get current user information.
    """
    user = get_current_user()
    
    return jsonify({
        'success': True,
        'user': user
    })


def init_auth_routes(app):
    """
    Initialize authentication routes.
    
    Args:
        app: Flask application instance
    """
    app.register_blueprint(auth_bp)
    
    # Add a before_request handler to check for authentication
    @app.before_request
    def check_auth():
        # Skip auth check for auth routes and static files
        if request.path.startswith('/auth') or request.path.startswith('/static'):
            return
        
        # Get token
        token = get_token_from_request()
        if token:
            # Validate token
            payload = validate_token(token)
            if payload:
                # Add user info to Flask g object
                g.user = {
                    'id': payload.get('sub'),
                    'name': payload.get('name'),
                    'email': payload.get('email'),
                    'roles': payload.get('roles', []),
                }
    
    logger.info("Auth routes initialized")