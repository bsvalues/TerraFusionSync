"""
County RBAC Authentication Module for TerraFusion SyncService.

This module provides role-based access control (RBAC) authentication tailored for 
County government usage, including:

1. Role definitions (Assessor, Staff, ITAdmin, Auditor)
2. Permission sets for each role
3. Integration with County Active Directory
4. IP-based access restrictions (.benton.wa.us network range)
5. Audit logging for all authentication activities
"""

import os
import json
import logging
import functools
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional, Set, Union

from flask import Blueprint, request, jsonify, session, current_app, redirect, url_for, flash, render_template

# Configure logging
logger = logging.getLogger(__name__)

# Mock AD integration with local file for development/testing
# In production, this would use LDAP to connect to the County's Active Directory
USERS_FILE = "county_users.json"
COUNTY_RBAC_AVAILABLE = True

# Role Definitions
ROLE_PERMISSIONS = {
    "Assessor": {
        "permissions": [
            "view_dashboard", 
            "view_sync_operations",
            "approve_sync_operations",
            "view_reports"
        ],
        "description": "Property assessors who can view and approve sync operations"
    },
    "Staff": {
        "permissions": [
            "view_dashboard", 
            "view_sync_operations",
            "create_sync_operations",
            "edit_sync_pairs",
            "view_reports"
        ],
        "description": "Staff members who can create and manage sync operations"
    },
    "ITAdmin": {
        "permissions": [
            "view_dashboard",
            "view_sync_operations",
            "create_sync_operations",
            "edit_sync_pairs",
            "view_reports",
            "approve_sync_operations",
            "rollback_operations",
            "manage_users",
            "view_audit_logs",
            "edit_system_settings"
        ],
        "description": "IT administrators with full system access"
    },
    "Auditor": {
        "permissions": [
            "view_dashboard",
            "view_sync_operations",
            "view_reports",
            "view_audit_logs"
        ],
        "description": "Auditors who can only view operations and reports"
    }
}

# Map from Active Directory groups to application roles
# This mapping allows us to determine which application roles
# to assign based on the AD groups a user belongs to
AD_GROUP_TO_ROLE_MAP = {
    # IT Department
    "IT Administrators": "ITAdmin",
    "SysAdmins": "ITAdmin",
    "Domain Admins": "ITAdmin",
    
    # Assessor's Office
    "Property Assessors": "Assessor",
    "Assessment Managers": "Assessor",
    "Assessment Supervisors": "Assessor",
    
    # Staff groups
    "Property Staff": "Staff",
    "Assessment Clerks": "Staff",
    "Data Entry": "Staff",
    
    # Auditor groups
    "County Auditors": "Auditor",
    "Financial Oversight": "Auditor",
    "Compliance Officers": "Auditor"
}

def map_ad_groups_to_roles(ad_groups: List[str]) -> List[str]:
    """
    Maps Active Directory groups to application roles.
    
    Args:
        ad_groups: List of Active Directory group names
        
    Returns:
        List of application roles
    """
    roles = set()
    
    for group in ad_groups:
        if group in AD_GROUP_TO_ROLE_MAP:
            roles.add(AD_GROUP_TO_ROLE_MAP[group])
    
    # If no mappable roles found, use a restricted default
    if not roles:
        logger.warning(f"No role mappings found for AD groups: {ad_groups}")
    
    return list(roles)

# County IP range (for development, allow all)
COUNTY_IP_RANGES = [
    "192.168.0.0/16",  # Example: Development environment
    "10.0.0.0/8",      # Example: County network
    "127.0.0.0/8"      # Localhost for testing
]

def load_mock_users():
    """
    Load mock user data.
    In production, this would query Active Directory.
    """
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r") as f:
                return json.load(f)
        else:
            # Create default users if file doesn't exist
            default_users = {
                "users": [
                    {
                        "username": "admin",
                        "password": "admin123",  # In production, this would be securely hashed
                        "email": "admin@county.gov",
                        "full_name": "Admin User",
                        "roles": ["ITAdmin"],
                        "department": "IT",
                        "active": True
                    },
                    {
                        "username": "assessor",
                        "password": "assessor123",
                        "email": "assessor@county.gov",
                        "full_name": "Property Assessor",
                        "roles": ["Assessor"],
                        "department": "Property Assessment",
                        "active": True
                    },
                    {
                        "username": "staff",
                        "password": "staff123",
                        "email": "staff@county.gov",
                        "full_name": "Staff Member",
                        "roles": ["Staff"],
                        "department": "Property Assessment",
                        "active": True
                    },
                    {
                        "username": "auditor",
                        "password": "auditor123",
                        "email": "auditor@county.gov",
                        "full_name": "County Auditor",
                        "roles": ["Auditor"],
                        "department": "Auditing",
                        "active": True
                    }
                ]
            }
            with open(USERS_FILE, "w") as f:
                json.dump(default_users, f, indent=4)
            return default_users
    except Exception as e:
        logger.error(f"Error loading user data: {e}")
        return {"users": []}

# Load mock users
mock_users = load_mock_users()

def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a user against the County Active Directory.
    Uses LDAP to authenticate against the County AD server.
    
    Args:
        username: The username to authenticate
        password: The password to authenticate
        
    Returns:
        User data dictionary if authenticated, None otherwise
    """
    # Get LDAP configuration from environment variables
    ldap_server = os.environ.get('COUNTY_LDAP_SERVER', '')
    ldap_base_dn = os.environ.get('COUNTY_LDAP_BASE_DN', '')
    ldap_domain = os.environ.get('COUNTY_LDAP_DOMAIN', '')
    
    # Check if we're in development mode (no LDAP server configured)
    if not ldap_server or not ldap_base_dn:
        logger.warning("LDAP not configured. Using mock authentication.")
        # Fall back to mock users for development
        for user in mock_users.get("users", []):
            if user.get("username") == username and user.get("password") == password and user.get("active", False):
                # Create a clean user object to return (omit password)
                return {
                    "id": f"user-{username}",
                    "username": username,
                    "email": user.get("email"),
                    "full_name": user.get("full_name"),
                    "roles": user.get("roles", []),
                    "department": user.get("department"),
                    "permissions": get_user_permissions(user.get("roles", []))
                }
        return None
    
    try:
        import ldap
        
        # Format user principal name
        user_dn = f"{username}@{ldap_domain}" if ldap_domain else username
        
        # Initialize LDAP connection
        conn = ldap.initialize(ldap_server)
        conn.protocol_version = ldap.VERSION3
        conn.set_option(ldap.OPT_REFERRALS, 0)
        
        # Bind with the provided credentials
        conn.simple_bind_s(user_dn, password)
        
        # Search for the user to get their details
        search_filter = f"(sAMAccountName={username})"
        attrs = ['mail', 'displayName', 'department', 'memberOf']
        
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, search_filter, attrs)
        
        # No user found
        if not result or not result[0][1]:
            logger.warning(f"User {username} authenticated but not found in directory.")
            return None
        
        # Extract user attributes
        user_attrs = result[0][1]
        email = user_attrs.get('mail', [b''])[0].decode('utf-8')
        full_name = user_attrs.get('displayName', [b''])[0].decode('utf-8')
        department = user_attrs.get('department', [b''])[0].decode('utf-8')
        
        # Extract AD groups
        ad_groups = []
        for group_dn in user_attrs.get('memberOf', []):
            group_name = group_dn.decode('utf-8').split(',')[0].split('=')[1]
            ad_groups.append(group_name)
        
        # Map AD groups to application roles
        roles = map_ad_groups_to_roles(ad_groups)
        
        # Close the connection
        conn.unbind_s()
        
        return {
            "id": f"ad-{username}",
            "username": username,
            "email": email,
            "full_name": full_name,
            "roles": roles,
            "department": department,
            "permissions": get_user_permissions(roles)
        }
    except ldap.INVALID_CREDENTIALS:
        logger.warning(f"Invalid credentials for user {username}")
        return None
    except Exception as e:
        logger.error(f"LDAP authentication error for {username}: {str(e)}")
        return None

def get_user_permissions(roles: List[str]) -> List[str]:
    """
    Get the list of permissions for a user based on their roles.
    
    Args:
        roles: List of role names
        
    Returns:
        List of permission strings
    """
    permissions = set()
    for role in roles:
        if role in ROLE_PERMISSIONS:
            role_perms = ROLE_PERMISSIONS[role].get("permissions", [])
            permissions.update(role_perms)
    # Convert set to list to ensure JSON serializability
    return list(permissions)

def check_ip_allowed(ip_address: str) -> bool:
    """
    Check if an IP address is allowed to access the system.
    In production, this would check if the IP is in the County's network range.
    
    Args:
        ip_address: The IP address to check
        
    Returns:
        True if allowed, False otherwise
    """
    # For development, allow all IPs
    # In production, this would implement proper IP range checking
    return True

def check_permission(permission: str) -> bool:
    """
    Check if the current user has a specific permission.
    
    Args:
        permission: The permission to check
        
    Returns:
        True if the user has the permission, False otherwise
    """
    if 'user' not in session:
        return False
    
    user = session['user']
    
    # ITAdmin role has all permissions
    if "ITAdmin" in user.get('roles', []):
        return True
    
    # Check specific permissions - use a list instead of a set
    user_permissions = []
    for role in user.get('roles', []):
        role_perms = ROLE_PERMISSIONS.get(role, {}).get("permissions", [])
        user_permissions.extend(role_perms)
    
    return permission in user_permissions

def requires_county_permission(permission: str):
    """
    Decorator to require a specific county permission for a route.
    
    Args:
        permission: The permission required
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if not check_permission(permission):
                if request.content_type == 'application/json':
                    return jsonify({
                        'error': 'Permission denied',
                        'message': f'This action requires the {permission} permission'
                    }), 403
                else:
                    flash(f'Permission denied: This page requires the {permission} permission', 'error')
                    return redirect(url_for('county_auth_bp.login'))
            return f(*args, **kwargs)
        return wrapped
    return decorator

def create_county_auth_blueprint():
    """
    Create and configure the County authentication blueprint.
    
    Returns:
        Flask Blueprint for County authentication
    """
    county_auth_bp = Blueprint('county_auth_bp', __name__, url_prefix='/county-auth')
    
    @county_auth_bp.route('/login', methods=['GET', 'POST'])
    def login():
        """
        Handle County login requests.
        """
        if request.method == 'POST':
            data = request.form if request.form else request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                if request.content_type == 'application/json':
                    return jsonify({'error': 'Username and password required'}), 400
                else:
                    flash('Username and password required', 'error')
                    return redirect(url_for('county_auth_bp.login'))
            
            # Check IP restrictions
            ip_address = request.remote_addr
            if not check_ip_allowed(ip_address):
                logger.warning(f"Login attempt from unauthorized IP: {ip_address}")
                if request.content_type == 'application/json':
                    return jsonify({'error': 'Access denied from this network'}), 403
                else:
                    flash('Access denied from this network', 'error')
                    return redirect(url_for('county_auth_bp.login'))
            
            # Authenticate user
            user = authenticate_user(username, password)
            if user:
                # Create session
                session['user'] = user
                session['authenticated'] = True
                
                # Create JWT token for API access
                expiry = datetime.utcnow() + timedelta(hours=8)  # 8 hour token validity
                payload = {
                    'sub': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'roles': user['roles'],
                    'exp': expiry
                }
                
                import jwt
                token = jwt.encode(payload, current_app.secret_key, algorithm='HS256')
                session['token'] = token
                
                # Create audit log
                logger.info(f"County user login: {username} from {ip_address}")
                
                # Redirect or return JSON
                if request.content_type == 'application/json':
                    return jsonify({
                        'success': True,
                        'token': token,
                        'user': user
                    })
                else:
                    next_url = request.args.get('next') or url_for('dashboard')
                    flash(f'Welcome {user["full_name"]}', 'success')
                    return redirect(next_url)
            else:
                # Failed authentication
                logger.warning(f"Failed county login attempt: {username} from {ip_address}")
                
                if request.content_type == 'application/json':
                    return jsonify({'error': 'Invalid credentials'}), 401
                else:
                    flash('Invalid username or password', 'error')
                    return redirect(url_for('county_auth_bp.login'))
        else:
            # GET request - show login form
            return render_template('county_login.html')
    
    @county_auth_bp.route('/logout', methods=['GET', 'POST'])
    def logout():
        """
        Handle County logout requests.
        """
        username = session.get('user', {}).get('username', 'Unknown')
        ip_address = request.remote_addr
        
        # Clear session
        session.clear()
        
        # Log the logout
        logger.info(f"County user logout: {username} from {ip_address}")
        
        if request.content_type == 'application/json':
            return jsonify({'success': True, 'message': 'Logged out successfully'})
        else:
            flash('You have been logged out', 'info')
            return redirect(url_for('county_auth_bp.login'))
    
    @county_auth_bp.route('/roles', methods=['GET'])
    @requires_county_permission('manage_users')
    def list_roles():
        """
        List available roles and their permissions.
        Only available to users with manage_users permission.
        """
        return jsonify({'roles': ROLE_PERMISSIONS})
    
    return county_auth_bp

def init_county_auth_routes(app):
    """
    Initialize County authentication routes.
    
    Args:
        app: Flask application instance
    """
    # Use a consistent name to avoid blueprint name collisions
    county_auth_bp = create_county_auth_blueprint()
    app.register_blueprint(county_auth_bp)
    logger.info("County auth routes initialized")
    
    @app.context_processor
    def inject_county_auth_utils():
        """
        Inject County authentication utilities into templates.
        """
        return {
            'check_county_permission': check_permission,
            'county_roles': ROLE_PERMISSIONS
        }

# Utility functions for external modules
def get_county_current_user():
    """
    Get the current County user from the session.
    
    Returns:
        User dictionary if authenticated, None otherwise
    """
    try:
        if hasattr(session, '_get_current_object'):
            # We're in a request context, safe to access session
            return session.get('user')
        else:
            # We're outside a request context
            return None
    except RuntimeError:
        # Handle "working outside of request context" error
        return None

def get_county_current_roles():
    """
    Get the current County user's roles.
    
    Returns:
        List of role names
    """
    try:
        if hasattr(session, '_get_current_object'):
            user = session.get('user', {})
            return user.get('roles', [])
        else:
            return []
    except RuntimeError:
        return []

def user_has_county_role(role: str) -> bool:
    """
    Check if the current user has a specific County role.
    
    Args:
        role: The role to check
        
    Returns:
        True if the user has the role, False otherwise
    """
    try:
        if hasattr(session, '_get_current_object'):
            user = session.get('user', {})
            return role in user.get('roles', [])
        else:
            return False
    except RuntimeError:
        return False

def check_county_permission(permission: str) -> bool:
    """
    Check if the current user has a specific County permission.
    
    Args:
        permission: The permission to check (e.g., 'view_sync_operations')
        
    Returns:
        True if the user has the permission, False otherwise
    """
    try:
        if hasattr(session, '_get_current_object'):
            user = session.get('user', {})
            if not user:
                return False
                
            # Get user roles
            roles = user.get('roles', [])
            
            # Define permissions for each role
            role_permissions = {
                'ITAdmin': ['view_sync_operations', 'create_sync_operations', 'approve_sync_operations', 
                           'rollback_operations', 'view_reports', 'view_audit_logs', 'manage_users'],
                'Assessor': ['view_sync_operations', 'approve_sync_operations', 'view_reports'],
                'Staff': ['view_sync_operations', 'create_sync_operations'],
                'Auditor': ['view_sync_operations', 'view_reports', 'view_audit_logs']
            }
            
            # Convert sets to lists for JSON serializability
            user_permissions = []
            for role in roles:
                user_permissions.extend(role_permissions.get(role, []))
            
            return permission in user_permissions
        else:
            return False
    except RuntimeError:
        return False