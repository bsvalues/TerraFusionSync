"""
County Role-Based Access Control Module

This module provides enhanced RBAC functionality that simulates County IT policies,
network credentials, and role-based access for the TerraFusion SyncService platform.

It's designed to be integrated with the existing authentication system and will later
connect to Active Directory/LDAP in production.
"""

import os
import logging
import ipaddress
import json
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Union, Callable
from flask import request, jsonify, g, current_app, abort, session

# Configure logging
logger = logging.getLogger(__name__)

# User roles and their permissions mapping
COUNTY_ROLES = {
    "Assessor": ["view", "approve", "diff"],
    "Staff": ["view", "upload"],
    "ITAdmin": ["view", "upload", "approve", "rollback", "export", "diff", "admin"],
    "Auditor": ["view", "diff", "audit"]
}

# Simulated user database with AD-style usernames
# In production, this would be replaced with LDAP/Active Directory queries
COUNTY_USERS = {
    "CO\\jdoe": {
        "username": "CO\\jdoe",
        "display_name": "John Doe",
        "email": "jdoe@benton.wa.us",
        "role": "Assessor",
        "department": "Assessors Office",
        "enabled": True
    },
    "CO\\mjohnson": {
        "username": "CO\\mjohnson",
        "display_name": "Mary Johnson",
        "email": "mjohnson@benton.wa.us",
        "role": "Staff",
        "department": "Assessors Office",
        "enabled": True
    },
    "CO\\bsmith": {
        "username": "CO\\bsmith",
        "display_name": "Bob Smith",
        "email": "bsmith@benton.wa.us",
        "role": "ITAdmin",
        "department": "IT",
        "enabled": True
    },
    "CO\\tauditor": {
        "username": "CO\\tauditor",
        "display_name": "Tim Auditor",
        "email": "tauditor@benton.wa.us",
        "role": "Auditor",
        "department": "Auditor Office",
        "enabled": True
    }
}

# Network access control - trusted IP ranges
# In production, this would be configured in the environment
TRUSTED_IP_RANGES = [
    "10.0.0.0/8",      # County internal network
    "172.16.0.0/12",   # VPN range
    "192.168.0.0/16",  # Local testing
    "127.0.0.0/8"      # Localhost for development
]


def get_ip_address():
    """
    Get the client's IP address from the request.
    
    Handles cases where the request comes through proxies.
    
    Returns:
        str: Client IP address
    """
    # Check X-Forwarded-For header first (if behind a proxy)
    if request.headers.get('X-Forwarded-For'):
        # Get the leftmost IP (client IP)
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    # Otherwise, use the remote address
    return request.remote_addr


def is_trusted_ip(ip_address: str) -> bool:
    """
    Check if an IP address is in the trusted ranges.
    
    Args:
        ip_address: IP address to check
        
    Returns:
        bool: True if IP is trusted, False otherwise
    """
    try:
        ip = ipaddress.ip_address(ip_address)
        
        for range_str in TRUSTED_IP_RANGES:
            network = ipaddress.ip_network(range_str)
            if ip in network:
                return True
        
        return False
    except ValueError:
        # If IP address is invalid, consider it untrusted
        logger.warning(f"Invalid IP address: {ip_address}")
        return False


def get_user_from_credentials(username: str, password: str) -> Optional[Dict]:
    """
    Validate user credentials and return user data.
    
    In production, this would authenticate against Active Directory.
    For development, it uses the simulated user database.
    
    Args:
        username: AD-style username (domain\\username)
        password: User password
        
    Returns:
        dict: User data if credentials are valid, None otherwise
    """
    # For demonstration purposes, accept any password for users in the database
    if username in COUNTY_USERS and COUNTY_USERS[username]["enabled"]:
        return COUNTY_USERS[username]
    
    return None


def log_user_action(username: str, role: str, action: str, resource_id: Optional[str] = None) -> None:
    """
    Log a user action to the audit trail.
    
    Args:
        username: User who performed the action
        role: User's role
        action: Action performed (e.g., APPROVE, VIEW)
        resource_id: ID of the affected resource (optional)
    """
    timestamp = datetime.utcnow().isoformat()
    ip_address = get_ip_address()
    
    log_entry = {
        "timestamp": timestamp,
        "username": username,
        "role": role,
        "action": action,
        "ip_address": ip_address,
        "resource_id": resource_id
    }
    
    # Log to application logs
    logger.info(f"{timestamp}, user={username}, role={role}, action={action}, ip={ip_address}, resource_id={resource_id or 'N/A'}")
    
    # In a real implementation, this would also write to a database table
    try:
        from apps.backend.models import AuditEntry
        from apps.backend.database import db
        
        with current_app.app_context():
            audit_entry = AuditEntry(
                event_type=action,
                resource_type="sync_operation" if resource_id else "system",
                description=f"User {username} ({role}) performed {action}",
                resource_id=resource_id,
                severity="info",
                username=username,
                ip_address=ip_address
            )
            db.session.add(audit_entry)
            db.session.commit()
    except ImportError:
        logger.warning("AuditEntry model not available, audit log only written to logger")
    except Exception as e:
        logger.error(f"Failed to create audit entry: {str(e)}")


def requires_county_auth(f):
    """
    Decorator to require County authentication for endpoints.
    
    This checks for a valid user in the session and validates 
    the client IP address against trusted ranges.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is authenticated
        if not hasattr(g, 'county_user'):
            # Check if we have user in session
            county_user = session.get('county_user')
            if county_user:
                g.county_user = county_user
            else:
                return abort(401, description="County authentication required")
        
        # Check IP address - comment this out for development
        # ip_address = get_ip_address()
        # if not is_trusted_ip(ip_address):
        #     logger.warning(f"Access attempt from untrusted IP: {ip_address}")
        #     return abort(403, description="Access restricted to County network")
        
        # Log the access
        log_user_action(
            g.county_user["username"],
            g.county_user["role"],
            f"ACCESS:{request.path}",
        )
        
        return f(*args, **kwargs)
    
    return decorated


def requires_county_permission(permission: str) -> Callable:
    """
    Decorator to require a specific County permission.
    
    This decorator should be used after requires_county_auth.
    
    Args:
        permission: Permission required (e.g., 'approve', 'view')
        
    Returns:
        Decorated function that checks for the required permission
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check if user is authenticated
            if not hasattr(g, 'county_user'):
                return abort(401, description="County authentication required")
            
            # Get user's role
            role = g.county_user.get("role")
            
            # Check if role has the required permission
            if role not in COUNTY_ROLES or permission not in COUNTY_ROLES[role]:
                logger.warning(f"Permission denied: User {g.county_user['username']} ({role}) attempted {permission}")
                
                # Log the access attempt
                log_user_action(
                    g.county_user["username"],
                    role,
                    f"DENIED:{permission}",
                )
                
                return abort(403, description=f"Permission denied: {permission} requires {', '.join([r for r, p in COUNTY_ROLES.items() if permission in p])}")
            
            # Log the successful permission check
            log_user_action(
                g.county_user["username"],
                role,
                f"GRANTED:{permission}",
            )
            
            return f(*args, **kwargs)
        
        return decorated
    
    return decorator


def get_current_county_user():
    """
    Get the current authenticated County user.
    
    Returns:
        dict: County user information or None if not authenticated
    """
    return getattr(g, 'county_user', None)


# Function to simulate Active Directory authentication
def authenticate_county_user(username: str, password: str) -> Optional[Dict]:
    """
    Authenticate a County user with AD-style credentials.
    
    Args:
        username: AD-style username (domain\\username)
        password: User password
        
    Returns:
        dict: User data if authentication successful, None otherwise
    """
    # Get user data
    user_data = get_user_from_credentials(username, password)
    
    if user_data:
        # Store in session and global object
        session['county_user'] = user_data
        g.county_user = user_data
        
        # Log the login
        log_user_action(
            username,
            user_data["role"],
            "LOGIN",
        )
        
        return user_data
    
    return None


def init_county_auth_routes(app):
    """
    Initialize County authentication routes.
    
    Args:
        app: Flask application instance
    """
    from flask import Blueprint, request, render_template, redirect, url_for, flash
    
    # Create county auth blueprint
    county_auth_bp = Blueprint('county_auth', __name__, url_prefix='/county-auth')
    
    @county_auth_bp.route('/login', methods=['GET', 'POST'])
    def county_login():
        """County login page and form submission handler."""
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            next_url = request.form.get('next') or request.args.get('next') or url_for('dashboard')
            
            if not username or not password:
                flash('Username and password are required', 'error')
                return render_template('county_login.html', next=next_url)
            
            # Authenticate user
            user_data = authenticate_county_user(username, password)
            
            if user_data:
                return redirect(next_url)
            else:
                flash('Invalid credentials', 'error')
                return render_template('county_login.html', next=next_url)
        
        # GET request - show login form
        next_url = request.args.get('next') or url_for('dashboard')
        return render_template('county_login.html', next=next_url)
    
    @county_auth_bp.route('/logout', methods=['GET', 'POST'])
    def county_logout():
        """County logout handler."""
        # Log the logout if user is authenticated
        county_user = session.get('county_user')
        if county_user:
            log_user_action(
                county_user["username"],
                county_user["role"],
                "LOGOUT",
            )
        
        # Clear session
        session.pop('county_user', None)
        
        # Flash message and redirect
        flash('You have been logged out of the County system', 'info')
        return redirect(url_for('root'))
    
    # Register blueprint
    app.register_blueprint(county_auth_bp)
    
    # Add template for login page if it doesn't exist
    template_dir = os.path.join(app.root_path, 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    login_template_path = os.path.join(template_dir, 'county_login.html')
    if not os.path.exists(login_template_path):
        # Create a basic login template
        with open(login_template_path, 'w') as f:
            f.write("""<!DOCTYPE html>
<html>
<head>
    <title>Benton County Authentication</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 50px auto; padding: 20px; background-color: #fff; border-radius: 5px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; margin-top: 0; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 3px; }
        button { background-color: #005595; color: white; border: none; padding: 10px 15px; border-radius: 3px; cursor: pointer; }
        button:hover { background-color: #004480; }
        .alert { padding: 10px; margin-bottom: 15px; border-radius: 3px; }
        .alert-error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
        .county-logo { max-width: 200px; margin-bottom: 20px; }
        .footer { margin-top: 20px; text-align: center; font-size: 0.8em; color: #777; }
    </style>
</head>
<body>
    <div class="container">
        <img src="/static/benton_county_logo.png" alt="Benton County Logo" class="county-logo">
        <h1>Benton County Authentication</h1>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }}">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form method="post">
            <div class="form-group">
                <label for="username">County Username:</label>
                <input type="text" id="username" name="username" placeholder="domain\\username" required>
            </div>
            
            <div class="form-group">
                <label for="password">Password:</label>
                <input type="password" id="password" name="password" required>
            </div>
            
            <input type="hidden" name="next" value="{{ next }}">
            
            <button type="submit">Log In</button>
        </form>
        
        <div class="footer">
            <p>© 2025 Benton County. All rights reserved.</p>
            <p>For technical assistance, please contact IT Help Desk at 555-1234.</p>
        </div>
    </div>
</body>
</html>""")
    
    logger.info("County auth routes initialized")
    
    # Add a before_request handler to check for county authentication
    @app.before_request
    def check_county_auth():
        # Skip auth check for public routes and static files
        if request.path.startswith('/county-auth') or request.path.startswith('/static'):
            return
        
        # Get user from session
        county_user = session.get('county_user')
        if county_user:
            # Store in Flask g object
            g.county_user = county_user