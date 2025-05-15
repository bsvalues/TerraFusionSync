"""
TerraFusion Platform - Authentication Routes

This module provides the Flask routes for authentication, including
login, logout, token refresh, and password management.
"""

import logging
from datetime import datetime
from functools import wraps
from typing import Dict, Any, Optional, Tuple, Union

from flask import (
    Blueprint, request, jsonify, render_template, redirect,
    url_for, session, flash, Response, current_app
)
from werkzeug.security import check_password_hash

from auth.jwt_utils import (
    create_access_token, create_refresh_token,
    decode_token, blacklist_token, clean_expired_blacklist_tokens
)

# Configure logging
logger = logging.getLogger(__name__)


def init_auth_routes(app) -> None:
    """
    Initialize authentication routes for a Flask application.
    
    Args:
        app: Flask application instance
    """
    # Create a blueprint for auth routes
    auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
    
    @auth_bp.route('/login', methods=['GET', 'POST'])
    def login() -> Union[str, Response]:
        """
        Handle login requests.
        
        GET: Display login form
        POST: Authenticate and issue JWT token
        
        Returns:
            HTML page or JSON response
        """
        # For GET requests, display the login form
        if request.method == 'GET':
            return render_template('auth/login.html')
        
        # For POST requests, authenticate the user
        elif request.method == 'POST':
            # Handle both form submissions and JSON API requests
            if request.content_type == 'application/json':
                data = request.json
                username = data.get('username')
                password = data.get('password')
                remember = data.get('remember', False)
            else:
                username = request.form.get('username')
                password = request.form.get('password')
                remember = request.form.get('remember', False)
            
            # TODO: For demo purposes, accept any login with password 'password'
            # In production, replace with database lookup
            if password != 'password':
                if request.content_type == 'application/json':
                    return jsonify({
                        'success': False,
                        'message': 'Invalid credentials'
                    }), 401
                else:
                    flash('Invalid credentials', 'error')
                    return redirect(url_for('auth.login'))
            
            # Create tokens
            # In production, get user data and permissions from database
            user_id = 1  # Replace with actual user ID
            role = 'Admin'  # Replace with actual role
            permissions = ['*']  # Replace with actual permissions
            
            # Generate access and refresh tokens
            access_token = create_access_token(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions,
                county_ids=['*']  # Wildcard for all counties
            )
            
            refresh_token = create_refresh_token(
                user_id=user_id,
                username=username,
                role=role
            )
            
            # Store in session
            session['token'] = access_token
            session['refresh_token'] = refresh_token
            session['username'] = username
            session['role'] = role
            
            # Log successful login
            logger.info(f"User {username} logged in successfully")
            
            # Return based on request content type
            if request.content_type == 'application/json':
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'access_token': access_token,
                    'refresh_token': refresh_token,
                    'user': {
                        'username': username,
                        'role': role
                    }
                })
            else:
                # Redirect to the requested page or default to dashboard
                next_url = session.get('next', url_for('dashboard'))
                if 'next' in session:
                    session.pop('next', None)
                
                flash('Login successful', 'success')
                return redirect(next_url)
    
    @auth_bp.route('/logout', methods=['GET', 'POST'])
    def logout() -> Union[str, Response]:
        """
        Handle logout requests.
        
        Returns:
            Redirect to login page or JSON response
        """
        # Blacklist the current token
        if 'token' in session:
            try:
                blacklist_token(session['token'])
            except Exception as e:
                logger.warning(f"Failed to blacklist token: {str(e)}")
        
        # Clear session
        session.clear()
        
        # Return based on request content type
        if request.content_type == 'application/json':
            return jsonify({
                'success': True,
                'message': 'Logout successful'
            })
        else:
            flash('You have been logged out', 'info')
            return redirect(url_for('root'))
    
    @auth_bp.route('/refresh', methods=['POST'])
    def refresh_token() -> Response:
        """
        Refresh an access token using a refresh token.
        
        Returns:
            JSON response with new access token
        """
        # Get refresh token from request or session
        if request.content_type == 'application/json':
            data = request.json or {}
            refresh_token = data.get('refresh_token')
        else:
            refresh_token = session.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'success': False,
                'message': 'Refresh token required'
            }), 400
        
        try:
            # Decode and validate refresh token
            payload = decode_token(refresh_token)
            
            # Check if it's a refresh token
            if payload.get('type') != 'refresh':
                return jsonify({
                    'success': False,
                    'message': 'Invalid token type'
                }), 400
            
            # Create a new access token
            user_id = payload.get('sub')
            username = payload.get('username')
            role = payload.get('role')
            
            # TODO: In production, fetch latest permissions from database
            # For now, use admin permissions
            permissions = ['*']
            
            # Generate new access token
            new_access_token = create_access_token(
                user_id=user_id,
                username=username,
                role=role,
                permissions=permissions,
                county_ids=['*']  # Wildcard for all counties
            )
            
            # Update session
            session['token'] = new_access_token
            
            # Clean up expired tokens occasionally
            clean_expired_blacklist_tokens()
            
            return jsonify({
                'success': True,
                'message': 'Token refreshed',
                'access_token': new_access_token
            })
        
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            # Clear session on error
            session.clear()
            
            return jsonify({
                'success': False,
                'message': f'Token refresh failed: {str(e)}'
            }), 401
    
    @auth_bp.route('/status', methods=['GET'])
    def auth_status() -> Response:
        """
        Get current authentication status.
        
        Returns:
            JSON response with authentication status
        """
        if 'token' in session:
            try:
                # Validate token
                payload = decode_token(session['token'])
                return jsonify({
                    'authenticated': True,
                    'username': payload.get('username'),
                    'role': payload.get('role'),
                    'expires_at': datetime.fromtimestamp(payload.get('exp')).isoformat()
                })
            except Exception:
                return jsonify({
                    'authenticated': False,
                    'message': 'Invalid or expired token'
                })
        else:
            return jsonify({
                'authenticated': False,
                'message': 'Not authenticated'
            })
    
    # Register blueprint with app
    app.register_blueprint(auth_bp)
    
    # Create login page route at application root
    @app.route('/login', methods=['GET', 'POST'])
    def login_page():
        """Alias for auth.login for compatibility."""
        return login()