"""
TerraFusion Platform - Authentication Routes

This module handles the authentication routes for the TerraFusion Platform.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional

from flask import (
    request, redirect, url_for, session, render_template, flash, 
    jsonify, current_app, Response, abort
)
from werkzeug.security import check_password_hash

from auth import auth_bp
from auth.config import (
    AUTH_REDIRECT_PARAM, ROLE_PERMISSIONS, LDAP_ENABLED,
    ROLE_ADMIN, ROLE_ASSESSOR, ROLE_STAFF, ROLE_AUDITOR
)
from auth.jwt_utils import (
    create_access_token, create_refresh_token, blacklist_token
)
from auth.decorators import requires_auth

logger = logging.getLogger(__name__)

# Load test users from JSON file for development
try:
    with open('county_users.json', 'r') as f:
        TEST_USERS = json.load(f)
except FileNotFoundError:
    # Create default test users if file doesn't exist
    TEST_USERS = {
        "admin": {
            "username": "admin",
            "password": "admin_pwd",  # In production, use hashed passwords
            "role": ROLE_ADMIN,
            "county_ids": ["*"],  # Admin can access all counties
            "user_id": "1"
        },
        "assessor": {
            "username": "assessor",
            "password": "assessor_pwd",
            "role": ROLE_ASSESSOR,
            "county_ids": ["benton-wa", "franklin-wa"],
            "user_id": "2"
        },
        "staff": {
            "username": "staff",
            "password": "staff_pwd",
            "role": ROLE_STAFF,
            "county_ids": ["benton-wa"],
            "user_id": "3"
        },
        "auditor": {
            "username": "auditor",
            "password": "auditor_pwd",
            "role": ROLE_AUDITOR,
            "county_ids": ["benton-wa", "franklin-wa", "grant-wa"],
            "user_id": "4"
        }
    }
    # Save default users to file
    try:
        with open('county_users.json', 'w') as f:
            json.dump(TEST_USERS, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to create default users file: {str(e)}")


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handle user login.
    GET: Show login form
    POST: Process login form submission
    """
    # Get the 'next' parameter for redirect after successful login
    next_url = request.args.get(AUTH_REDIRECT_PARAM) or request.form.get('next')
    
    # If the user is already logged in, redirect to the next URL or dashboard
    if session.get('token'):
        return redirect(next_url or url_for('dashboard'))
    
    # Handle login form submission
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html', next=next_url)
            
        # Authenticate the user (using LDAP in production)
        user = authenticate_user(username, password)
        
        if not user:
            flash('Invalid username or password', 'error')
            logger.warning(f"Failed login attempt for username: {username}")
            return render_template('auth/login.html', next=next_url)
        
        # User authenticated successfully, create tokens
        access_token = create_access_token(
            user_id=user.get('user_id') or username,
            username=username,
            role=user.get('role'),
            permissions=get_permissions_for_role(user.get('role')),
            county_ids=user.get('county_ids')
        )
        
        refresh_token = create_refresh_token(
            user_id=user.get('user_id') or username,
            username=username,
            role=user.get('role')
        )
        
        # Store tokens in session
        session['token'] = access_token
        session['refresh_token'] = refresh_token
        
        # Log successful login
        logger.info(f"User {username} logged in successfully (role: {user.get('role')})")
        
        # Create audit log entry for login
        try:
            from app import create_audit_log
            create_audit_log(
                event_type='user_login',
                resource_type='user',
                description=f"User {username} logged in",
                resource_id=str(user.get('user_id') or username),
                user_id=str(user.get('user_id') or username),
                username=username,
                severity='info'
            )
        except ImportError:
            logger.warning("Audit log function not available")
        
        # Redirect to the next URL or dashboard
        flash(f'Welcome, {username}!', 'success')
        return redirect(next_url or url_for('dashboard'))
    
    # Show login form for GET requests
    return render_template('auth/login.html', next=next_url)


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    token = session.get('token')
    if token:
        # Add the token to the blacklist
        blacklist_token(token)
        
        # Log the logout
        logger.info(f"User logged out")
        
        # Create audit log entry for logout
        try:
            token_payload = None
            try:
                from auth.jwt_utils import decode_token
                token_payload = decode_token(token)
            except Exception:
                pass
            
            if token_payload:
                from app import create_audit_log
                create_audit_log(
                    event_type='user_logout',
                    resource_type='user',
                    description=f"User {token_payload.get('username')} logged out",
                    resource_id=str(token_payload.get('sub')),
                    user_id=str(token_payload.get('sub')),
                    username=token_payload.get('username'),
                    severity='info'
                )
        except ImportError:
            logger.warning("Audit log function not available")
    
    # Clear session data
    session.clear()
    
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh the access token using the refresh token.
    This endpoint is used by API clients to get a new access token.
    """
    # Get refresh token from request or session
    refresh_token = None
    if request.is_json:
        refresh_token = request.json.get('refresh_token')
    elif request.form:
        refresh_token = request.form.get('refresh_token')
    else:
        refresh_token = session.get('refresh_token')
    
    if not refresh_token:
        return jsonify({
            'success': False,
            'message': 'Refresh token is required',
            'error': 'missing_token'
        }), 400
    
    try:
        # Decode and validate refresh token
        from auth.jwt_utils import decode_token
        token_payload = decode_token(refresh_token)
        
        # Make sure it's a refresh token
        if token_payload.get('type') != 'refresh':
            return jsonify({
                'success': False,
                'message': 'Invalid token type',
                'error': 'invalid_token_type'
            }), 400
        
        # Create a new access token
        user_id = token_payload.get('sub')
        username = token_payload.get('username')
        role = token_payload.get('role')
        
        # Get user details to include county IDs and permissions
        user = get_user_details(username)
        county_ids = user.get('county_ids') if user else None
        
        # Create a new access token
        access_token = create_access_token(
            user_id=user_id,
            username=username,
            role=role,
            permissions=get_permissions_for_role(role),
            county_ids=county_ids
        )
        
        # Store the new access token in the session
        session['token'] = access_token
        
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'access_token': access_token
        })
    except Exception as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Invalid or expired refresh token',
            'error': 'invalid_token'
        }), 401


@auth_bp.route('/user')
@requires_auth()
def get_user_info():
    """
    Get information about the currently logged-in user.
    This endpoint is useful for client applications to check if the user is logged in.
    """
    token_payload = getattr(request, 'token_payload', None)
    
    if not token_payload:
        return jsonify({
            'success': False,
            'message': 'Not authenticated',
            'authenticated': False
        }), 401
    
    # Get user details from the token
    user_id = token_payload.get('sub')
    username = token_payload.get('username')
    role = token_payload.get('role')
    permissions = token_payload.get('permissions', [])
    county_ids = token_payload.get('county_ids', [])
    
    return jsonify({
        'success': True,
        'authenticated': True,
        'user': {
            'id': user_id,
            'username': username,
            'role': role,
            'permissions': permissions,
            'county_ids': county_ids
        }
    })


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with the given username and password.
    
    In production, this would use LDAP to authenticate against Active Directory.
    For development, we use a simple in-memory store of test users.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        User details dict if authentication is successful, None otherwise
    """
    if LDAP_ENABLED:
        return authenticate_user_ldap(username, password)
    else:
        return authenticate_user_dev(username, password)


def authenticate_user_dev(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user using the development test users.
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        User details dict if authentication is successful, None otherwise
    """
    user = TEST_USERS.get(username)
    
    if not user:
        logger.warning(f"User not found: {username}")
        return None
    
    # In production, we would use hashed passwords
    if user.get('password') != password:
        logger.warning(f"Invalid password for user: {username}")
        return None
    
    return user


def authenticate_user_ldap(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user using LDAP (Active Directory).
    
    Args:
        username: The username to authenticate
        password: The password to verify
        
    Returns:
        User details dict if authentication is successful, None otherwise
    """
    try:
        import ldap
        from auth.config import (
            LDAP_SERVER, LDAP_PORT, LDAP_USE_SSL, 
            LDAP_BIND_DN, LDAP_BIND_PASSWORD, 
            LDAP_BASE_DN, LDAP_USER_FILTER, LDAP_GROUP_FILTER
        )
        
        # Connect to LDAP server
        ldap_uri = f"{'ldaps' if LDAP_USE_SSL else 'ldap'}://{LDAP_SERVER}:{LDAP_PORT}"
        ldap_conn = ldap.initialize(ldap_uri)
        ldap_conn.set_option(ldap.OPT_REFERRALS, 0)
        
        # Bind with service account
        ldap_conn.simple_bind_s(LDAP_BIND_DN, LDAP_BIND_PASSWORD)
        
        # Search for the user
        user_filter = LDAP_USER_FILTER.format(username=username)
        result = ldap_conn.search_s(
            LDAP_BASE_DN, ldap.SCOPE_SUBTREE, user_filter, ['cn', 'mail', 'memberOf']
        )
        
        if not result or not result[0] or not result[0][0]:
            logger.warning(f"LDAP: User not found: {username}")
            return None
        
        user_dn = result[0][0]
        user_attrs = result[0][1]
        
        # Authenticate the user
        try:
            ldap_conn.simple_bind_s(user_dn, password)
        except ldap.INVALID_CREDENTIALS:
            logger.warning(f"LDAP: Invalid credentials for user: {username}")
            return None
        
        # Get user's groups and determine role
        role = ROLE_STAFF  # Default role
        county_ids = []
        
        # Extract group memberships
        member_of = user_attrs.get('memberOf', [])
        for group_dn in member_of:
            group_dn = group_dn.decode('utf-8')
            
            # Determine role based on group membership
            if 'CN=TerraFusion_Admins' in group_dn:
                role = ROLE_ADMIN
                county_ids = ['*']  # Admin can access all counties
            elif 'CN=TerraFusion_Assessors' in group_dn:
                role = ROLE_ASSESSOR
            elif 'CN=TerraFusion_Auditors' in group_dn:
                role = ROLE_AUDITOR
            
            # Extract county access
            if 'CN=TerraFusion_County_' in group_dn:
                # Extract county ID from group name (e.g., "TerraFusion_County_benton-wa")
                parts = group_dn.split(',')[0].split('=')[1].split('_')
                if len(parts) >= 3:
                    county_id = parts[2].lower()
                    if county_id and county_id not in county_ids and county_ids != ['*']:
                        county_ids.append(county_id)
        
        # Create user details
        user = {
            'username': username,
            'role': role,
            'county_ids': county_ids,
            'user_id': user_dn,  # Use the DN as the user ID
            'email': user_attrs.get('mail', [b''])[0].decode('utf-8')
        }
        
        return user
        
    except ImportError:
        logger.error("LDAP module not available")
        return None
    except Exception as e:
        logger.error(f"LDAP authentication error: {str(e)}")
        return None


def get_user_details(username: str) -> Optional[Dict[str, Any]]:
    """
    Get user details for the given username.
    
    Args:
        username: The username to look up
        
    Returns:
        User details dict if found, None otherwise
    """
    if LDAP_ENABLED:
        # In production, we would fetch this from LDAP or a database
        # For now, just return the default values
        return TEST_USERS.get(username)
    else:
        return TEST_USERS.get(username)


def get_permissions_for_role(role: str) -> List[str]:
    """
    Get the permissions for a given role.
    
    Args:
        role: The role to get permissions for
        
    Returns:
        List of permission strings
    """
    return ROLE_PERMISSIONS.get(role, [])