"""
TerraFusion Platform - Authentication Routes

This module provides route handlers for authentication-related requests.
"""
import datetime
import logging
from typing import Tuple, Dict, Any, Optional, Union

from flask import (
    Blueprint, render_template, request, redirect, url_for, 
    flash, jsonify, session, current_app, g
)
from werkzeug.security import generate_password_hash, check_password_hash

from auth.models import User, RefreshToken, db
from auth.audit import (
    log_login_success, log_login_failure, log_logout, 
    log_token_created, log_token_refreshed, log_password_change
)
from auth.jwt_utils import generate_token, verify_token, refresh_access_token, get_token_from_header
from auth.config import (
    JWT_REFRESH_TOKEN_EXPIRES, PASSWORD_MIN_LENGTH, PASSWORD_REQUIRE_UPPERCASE,
    PASSWORD_REQUIRE_LOWERCASE, PASSWORD_REQUIRE_DIGIT, PASSWORD_REQUIRE_SPECIAL
)

logger = logging.getLogger(__name__)

# Create a Blueprint for authentication routes
auth = Blueprint('auth', __name__, url_prefix='/auth')

@auth.route('/login', methods=['GET', 'POST'])
def login() -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle login for web and API authentication.
    
    For web requests:
    - GET: Show the login form
    - POST: Process the login form
    
    For API requests:
    - POST: Return JWT tokens
    
    Returns:
        HTML page, redirect, or JSON response
    """
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    # Handle GET request for web pages
    if request.method == 'GET' and not is_api_request:
        return render_template('auth/login.html')
    
    # For POST requests, get the credentials
    if is_api_request and request.is_json:
        data = request.json
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')
    
    # Validate input
    if not username or not password:
        if is_api_request:
            return jsonify({
                "error": "Invalid request",
                "message": "Username and password are required"
            }), 400
        flash('Username and password are required', 'error')
        return render_template('auth/login.html', error='Username and password are required')
    
    # Find the user
    user = User.query.filter_by(username=username).first()
    
    # Verify credentials
    if not user or not user.check_password(password):
        log_login_failure(username, "Invalid credentials")
        if is_api_request:
            return jsonify({
                "error": "Authentication failed",
                "message": "Invalid username or password"
            }), 401
        flash('Invalid username or password', 'error')
        return render_template('auth/login.html', error='Invalid username or password')
    
    # Check if user is active
    if not user.active:
        log_login_failure(username, "Account is deactivated")
        if is_api_request:
            return jsonify({
                "error": "Authentication failed",
                "message": "Account is deactivated"
            }), 401
        flash('Your account is deactivated. Please contact an administrator.', 'error')
        return render_template('auth/login.html', error='Account is deactivated')
    
    # Authentication succeeded
    user.record_login()
    log_login_success(user.id, user.username)
    
    # For API requests, generate and return tokens
    if is_api_request:
        # Generate access and refresh tokens
        access_token = generate_token(
            user_id=user.id,
            username=user.username,
            role=user.role,
            county_ids=user.county_access,
            token_type='access'
        )
        
        refresh_token_expires = datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES)
        refresh_token_model = RefreshToken(user_id=user.id, expires_at=refresh_token_expires)
        db.session.add(refresh_token_model)
        db.session.commit()
        
        # Log token creation events
        log_token_created(user.id, user.username, 'access')
        log_token_created(user.id, user.username, 'refresh')
        
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token_model.token,
            "token_type": "Bearer",
            "expires_in": JWT_REFRESH_TOKEN_EXPIRES,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "county_access": user.county_access
            }
        }), 200
    
    # For web requests, set session and redirect
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['county_ids'] = user.county_access
    
    # Redirect to the next URL if provided, or the dashboard
    next_url = request.form.get('next') or request.args.get('next')
    if next_url:
        return redirect(next_url)
    return redirect(url_for('dashboard'))

@auth.route('/logout', methods=['GET', 'POST'])
def logout() -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle logout for web and API authentication.
    
    For web requests:
    - GET/POST: Clear session and redirect to login
    
    For API requests:
    - POST: Revoke refresh token
    
    Returns:
        Redirect or JSON response
    """
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    if is_api_request:
        # For API requests, check if a refresh token was provided
        if request.is_json:
            data = request.json
            token = data.get('refresh_token')
            if token:
                # Find and revoke the token
                refresh_token = RefreshToken.get_by_token(token)
                if refresh_token:
                    refresh_token.revoke()
                    user = User.query.get(refresh_token.user_id)
                    if user:
                        log_logout(user.id, user.username)
        
        return jsonify({"message": "Logged out successfully"}), 200
    
    # For web requests, clear the session
    user_id = session.get('user_id')
    username = session.get('username')
    
    session.clear()
    
    if user_id and username:
        log_logout(user_id, username)
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/refresh', methods=['POST'])
def refresh() -> Tuple[Dict[str, Any], int]:
    """
    Refresh an access token using a refresh token.
    
    Returns:
        JSON response with a new access token
    """
    # Only for API requests
    if not request.is_json:
        return jsonify({
            "error": "Invalid request",
            "message": "Request must be JSON"
        }), 400
    
    # Get the refresh token
    refresh_token = request.json.get('refresh_token')
    if not refresh_token:
        return jsonify({
            "error": "Invalid request",
            "message": "Refresh token is required"
        }), 400
    
    # Check if the refresh token is valid
    token_model = RefreshToken.get_by_token(refresh_token)
    if not token_model or not token_model.is_valid():
        return jsonify({
            "error": "Invalid token",
            "message": "Refresh token is invalid or expired"
        }), 401
    
    # Generate a new access token
    user = User.query.get(token_model.user_id)
    if not user or not user.active:
        return jsonify({
            "error": "Invalid token",
            "message": "User account is inactive or does not exist"
        }), 401
    
    access_token = generate_token(
        user_id=user.id,
        username=user.username,
        role=user.role,
        county_ids=user.county_access,
        token_type='access'
    )
    
    log_token_refreshed(user.id, user.username)
    
    return jsonify({
        "access_token": access_token,
        "token_type": "Bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "county_access": user.county_access
        }
    }), 200

@auth.route('/password', methods=['POST'])
def change_password() -> Tuple[Dict[str, Any], int]:
    """
    Change a user's password.
    
    The user must provide their current password and a new password.
    
    Returns:
        JSON response
    """
    # Only for API requests
    if not request.is_json:
        return jsonify({
            "error": "Invalid request",
            "message": "Request must be JSON"
        }), 400
    
    # Get the current user
    current_user = getattr(g, 'current_user', None)
    if not current_user:
        return jsonify({
            "error": "Authentication required",
            "message": "You must be logged in to change your password"
        }), 401
    
    # Get the passwords
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validate input
    if not current_password or not new_password or not confirm_password:
        return jsonify({
            "error": "Invalid request",
            "message": "Current password, new password, and confirm password are required"
        }), 400
    
    if new_password != confirm_password:
        return jsonify({
            "error": "Invalid request",
            "message": "New password and confirm password do not match"
        }), 400
    
    # Validate password strength
    password_validation = validate_password_strength(new_password)
    if not password_validation['valid']:
        return jsonify({
            "error": "Invalid password",
            "message": password_validation['message']
        }), 400
    
    # Find the user
    user = User.query.get(current_user['user_id'])
    if not user or not user.active:
        return jsonify({
            "error": "Authentication failed",
            "message": "User account is inactive or does not exist"
        }), 401
    
    # Verify current password
    if not user.check_password(current_password):
        return jsonify({
            "error": "Authentication failed",
            "message": "Current password is incorrect"
        }), 401
    
    # Update the password
    user.set_password(new_password)
    db.session.commit()
    
    log_password_change(user.id, user.username)
    
    return jsonify({
        "message": "Password changed successfully"
    }), 200

@auth.route('/register', methods=['GET', 'POST'])
def register() -> Union[str, Tuple[Dict[str, Any], int]]:
    """
    Handle user registration.
    
    For web requests:
    - GET: Show the registration form
    - POST: Process the registration form
    
    For API requests:
    - POST: Create a new user
    
    Returns:
        HTML page, redirect, or JSON response
    """
    # Check if it's an API request
    is_api_request = request.headers.get('Accept', '').startswith('application/json') or request.is_json
    
    # Handle GET request for web pages
    if request.method == 'GET' and not is_api_request:
        return render_template('auth/register.html')
    
    # For POST requests, get the user data
    if is_api_request and request.is_json:
        data = request.json
    else:
        data = request.form
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    
    # Validate input
    if not username or not email or not password or not confirm_password:
        if is_api_request:
            return jsonify({
                "error": "Invalid request",
                "message": "Username, email, password, and confirm password are required"
            }), 400
        flash('All fields are required', 'error')
        return render_template('auth/register.html', error='All fields are required')
    
    if password != confirm_password:
        if is_api_request:
            return jsonify({
                "error": "Invalid request",
                "message": "Passwords do not match"
            }), 400
        flash('Passwords do not match', 'error')
        return render_template('auth/register.html', error='Passwords do not match')
    
    # Validate password strength
    password_validation = validate_password_strength(password)
    if not password_validation['valid']:
        if is_api_request:
            return jsonify({
                "error": "Invalid password",
                "message": password_validation['message']
            }), 400
        flash(password_validation['message'], 'error')
        return render_template('auth/register.html', error=password_validation['message'])
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        if is_api_request:
            return jsonify({
                "error": "Invalid request",
                "message": "Username already exists"
            }), 400
        flash('Username already exists', 'error')
        return render_template('auth/register.html', error='Username already exists')
    
    if User.query.filter_by(email=email).first():
        if is_api_request:
            return jsonify({
                "error": "Invalid request",
                "message": "Email already exists"
            }), 400
        flash('Email already exists', 'error')
        return render_template('auth/register.html', error='Email already exists')
    
    # Create the user
    user = User(
        username=username,
        email=email,
        password=password,
        role='Staff',  # Default role
        first_name=first_name,
        last_name=last_name,
        county_access=[]  # No county access by default
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Registration succeeded
    if is_api_request:
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
        }), 201
    
    flash('Registration successful. Please log in.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/unauthorized', methods=['GET'])
def unauthorized() -> str:
    """
    Display an unauthorized error page.
    
    Returns:
        HTML page
    """
    message = request.args.get('message', 'You do not have permission to access this page')
    return render_template(
        'auth/error.html',
        title='Access Denied',
        error_code=403,
        message=message
    )

@auth.route('/me', methods=['GET'])
def get_current_user() -> Tuple[Dict[str, Any], int]:
    """
    Get the current user's profile.
    
    Returns:
        JSON response with user data
    """
    # Get current user from g object
    current_user = getattr(g, 'current_user', None)
    
    if not current_user:
        return jsonify({
            "error": "Authentication required",
            "message": "You must be logged in to access this resource"
        }), 401
    
    # Find the user
    user = User.query.get(current_user['user_id'])
    if not user or not user.active:
        return jsonify({
            "error": "Authentication failed",
            "message": "User account is inactive or does not exist"
        }), 401
    
    return jsonify({
        "user": user.to_dict()
    }), 200

def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate the strength of a password.
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation result and message
    """
    # Check length
    if len(password) < PASSWORD_MIN_LENGTH:
        return {
            "valid": False,
            "message": f"Password must be at least {PASSWORD_MIN_LENGTH} characters long"
        }
    
    # Check for uppercase
    if PASSWORD_REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
        return {
            "valid": False,
            "message": "Password must contain at least one uppercase letter"
        }
    
    # Check for lowercase
    if PASSWORD_REQUIRE_LOWERCASE and not any(c.islower() for c in password):
        return {
            "valid": False,
            "message": "Password must contain at least one lowercase letter"
        }
    
    # Check for digit
    if PASSWORD_REQUIRE_DIGIT and not any(c.isdigit() for c in password):
        return {
            "valid": False,
            "message": "Password must contain at least one digit"
        }
    
    # Check for special character
    if PASSWORD_REQUIRE_SPECIAL and not any(not c.isalnum() for c in password):
        return {
            "valid": False,
            "message": "Password must contain at least one special character"
        }
    
    return {
        "valid": True,
        "message": "Password meets requirements"
    }