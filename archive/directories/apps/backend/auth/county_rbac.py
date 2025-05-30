"""
TerraFusion SyncService - County RBAC Authentication

This module provides Role-Based Access Control authentication for the
County Property Assessment system, including:

1. LDAP integration with County Active Directory
2. Role-specific permissions and access controls
3. Authentication decorators for securing routes
4. IP-based restriction to County networks
"""

import logging
import functools
from flask import request, redirect, url_for, session, g, flash, current_app

# Configure logger
logger = logging.getLogger(__name__)

# Role definitions
ROLES = {
    'ITAdmin': {
        'description': 'IT Administrator with full system access',
        'permissions': ['view', 'edit', 'approve', 'admin', 'system', 'audit']
    },
    'Assessor': {
        'description': 'Property Assessor with approval rights',
        'permissions': ['view', 'approve']
    },
    'Staff': {
        'description': 'Staff member with upload capabilities',
        'permissions': ['view', 'upload']
    },
    'Auditor': {
        'description': 'Auditor with view-only access',
        'permissions': ['view', 'audit']
    }
}

# LDAP configuration
COUNTY_LDAP_GROUPS = {
    'CN=IT Administrators,OU=Groups,DC=benton,DC=wa,DC=us': 'ITAdmin',
    'CN=Property Assessors,OU=Groups,DC=benton,DC=wa,DC=us': 'Assessor',
    'CN=Assessment Staff,OU=Groups,DC=benton,DC=wa,DC=us': 'Staff',
    'CN=County Auditors,OU=Groups,DC=benton,DC=wa,DC=us': 'Auditor'
}

def requires_auth(f):
    """
    Decorator to require authentication for a route.
    
    If the user is not authenticated, redirects to the login page.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is logged in
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        
        # Set current user in g for easy access
        from apps.backend.models.user import User
        user = User.query.get(session['user_id'])
        if not user:
            session.clear()
            flash('User not found. Please log in again.', 'error')
            return redirect(url_for('login'))
        
        # Check if user is active
        if not user.is_active:
            session.clear()
            flash('Your account has been deactivated. Please contact support.', 'error')
            return redirect(url_for('login'))
        
        # IP restriction check (only benton.wa.us networks)
        if current_app.config.get('ENABLE_IP_RESTRICTION'):
            client_ip = request.remote_addr
            allowed_networks = current_app.config.get('ALLOWED_NETWORKS', ['127.0.0.1'])
            if not any(ip in client_ip for ip in allowed_networks):
                logger.warning(f"Access denied for IP {client_ip} to {request.path}")
                flash('Access is only allowed from County networks.', 'error')
                return redirect(url_for('login'))
        
        # Set current user in g
        g.user = user
        
        return f(*args, **kwargs)
    return decorated

def requires_role(role):
    """
    Decorator to require a specific role for a route.
    
    Args:
        role: Required role(s) as string or list
    """
    def decorator(f):
        @functools.wraps(f)
        @requires_auth
        def decorated(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            
            # Convert role to list if it's a string
            required_roles = [role] if isinstance(role, str) else role
            
            # Check if user has any of the required roles
            if g.user.role not in required_roles:
                flash(f'Access denied. This page requires {" or ".join(required_roles)} role.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def requires_permission(permission):
    """
    Decorator to require a specific permission for a route.
    
    Args:
        permission: Required permission(s) as string or list
    """
    def decorator(f):
        @functools.wraps(f)
        @requires_auth
        def decorated(*args, **kwargs):
            if not g.user:
                return redirect(url_for('login'))
            
            # Convert permission to list if it's a string
            required_permissions = [permission] if isinstance(permission, str) else permission
            
            # Get user's permissions based on role
            user_permissions = ROLES.get(g.user.role, {}).get('permissions', [])
            
            # Check if user has any of the required permissions
            if not any(perm in user_permissions for perm in required_permissions):
                flash(f'Access denied. You do not have the required permissions.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated
    return decorator

def validate_ldap_user(username, password):
    """
    Validate user against County LDAP server.
    
    Args:
        username: Username to authenticate
        password: Password to authenticate
        
    Returns:
        Tuple (success, user_data) where user_data contains role and other info
    """
    try:
        # Check if LDAP is configured
        if not current_app.config.get('COUNTY_LDAP_SERVER'):
            logger.warning("LDAP not configured, falling back to mock authentication")
            return _mock_authenticate(username, password)
        
        import ldap
        
        # LDAP configuration
        ldap_server = current_app.config.get('COUNTY_LDAP_SERVER')
        base_dn = current_app.config.get('COUNTY_LDAP_BASE_DN')
        domain = current_app.config.get('COUNTY_LDAP_DOMAIN')
        
        # Connect to LDAP server
        ldap_client = ldap.initialize(f"ldap://{ldap_server}")
        ldap_client.set_option(ldap.OPT_REFERRALS, 0)
        
        # Build user DN
        user_dn = f"{username}@{domain}" if '@' not in username else username
        
        # Attempt to bind with user credentials
        ldap_client.simple_bind_s(user_dn, password)
        
        # Search for user details
        search_filter = f"(sAMAccountName={username})"
        attributes = ['memberOf', 'mail', 'givenName', 'sn']
        result = ldap_client.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attributes)
        
        if not result:
            logger.warning(f"User {username} authenticated but not found in directory")
            return False, None
        
        # Extract user data
        user_data = result[0][1]
        groups = user_data.get('memberOf', [])
        groups = [g.decode('utf-8') for g in groups]
        
        # Determine role based on group membership
        role = None
        for group_dn, role_name in COUNTY_LDAP_GROUPS.items():
            if group_dn in groups:
                role = role_name
                break
        
        if not role:
            logger.warning(f"User {username} is not a member of any mapped groups")
            return False, None
        
        # Extract user details
        email = user_data.get('mail', [b''])[0].decode('utf-8')
        first_name = user_data.get('givenName', [b''])[0].decode('utf-8')
        last_name = user_data.get('sn', [b''])[0].decode('utf-8')
        
        user_info = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'is_ldap_user': True
        }
        
        return True, user_info
        
    except ImportError:
        logger.error("python-ldap module not available")
        return _mock_authenticate(username, password)
    except Exception as e:
        logger.error(f"LDAP authentication error: {str(e)}")
        return False, None

def _mock_authenticate(username, password):
    """
    Mock authentication for development and testing.
    
    Args:
        username: Username to authenticate
        password: Password to authenticate
        
    Returns:
        Tuple (success, user_data) where user_data contains role and other info
    """
    # Test accounts for development
    test_accounts = {
        'admin': {
            'password': 'admin123',
            'email': 'admin@benton.wa.us',
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'ITAdmin'
        },
        'assessor': {
            'password': 'assessor123',
            'email': 'assessor@benton.wa.us',
            'first_name': 'Assessment',
            'last_name': 'Officer',
            'role': 'Assessor'
        },
        'staff': {
            'password': 'staff123',
            'email': 'staff@benton.wa.us',
            'first_name': 'Staff',
            'last_name': 'Member',
            'role': 'Staff'
        },
        'auditor': {
            'password': 'auditor123',
            'email': 'auditor@benton.wa.us',
            'first_name': 'Audit',
            'last_name': 'Officer',
            'role': 'Auditor'
        }
    }
    
    if username in test_accounts and test_accounts[username]['password'] == password:
        user_info = dict(test_accounts[username])
        user_info.pop('password')  # Remove password from returned data
        user_info['username'] = username
        user_info['is_ldap_user'] = False
        return True, user_info
    
    return False, None

def init_auth_routes(app):
    """
    Initialize authentication routes for a Flask application.
    
    Args:
        app: Flask application instance
    """
    from flask import render_template, request, session, redirect, url_for, flash
    from apps.backend.database import get_shared_db
    from apps.backend.models.user import User
    
    db = get_shared_db()
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login route."""
        if session.get('user_id'):
            return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            
            success, user_data = validate_ldap_user(username, password)
            
            if not success:
                flash('Invalid username or password.', 'error')
                return render_template('county_login.html')
            
            # Check if user exists in database
            user = User.query.filter_by(username=username).first()
            
            if not user:
                # Create new user
                user = User(
                    username=username,
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    is_ldap_user=user_data['is_ldap_user']
                )
                
                # Set password for non-LDAP users
                if not user_data['is_ldap_user']:
                    user.set_password(password)
                    
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new user: {username}")
            elif not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
                return render_template('county_login.html')
            elif not user.is_ldap_user and not user.check_password(password):
                flash('Invalid username or password.', 'error')
                return render_template('county_login.html')
            
            # Update user information if needed
            if user.role != user_data['role'] or user.email != user_data['email']:
                user.role = user_data['role']
                user.email = user_data['email']
                user.first_name = user_data['first_name']
                user.last_name = user_data['last_name']
                db.session.commit()
            
            # Record login
            user.record_login()
            db.session.commit()
            
            # Set session as permanent (will last for the duration defined in PERMANENT_SESSION_LIFETIME)
            session.permanent = True
            
            # Set session values
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            # Log debug info
            logger.debug(f"Login successful for {username} with role {user.role}")
            logger.debug(f"Session is permanent: {session.permanent}")
            
            # Check if user needs onboarding
            from apps.backend.models.onboarding import UserOnboarding
            onboarding = UserOnboarding.query.filter_by(user_id=user.id).first()
            
            if not onboarding or (not onboarding.tutorial_complete and not onboarding.dismissed):
                logger.info(f"Redirecting {username} to onboarding")
                return redirect(url_for('onboarding_bp.onboarding_home'))
            
            return redirect(url_for('dashboard'))
        
        return render_template('county_login.html')
    
    @app.route('/logout')
    def logout():
        """Logout route."""
        session.clear()
        flash('You have been logged out.', 'success')
        return redirect(url_for('login'))
    
    logger.info("County auth routes initialized")