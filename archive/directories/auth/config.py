"""
TerraFusion Platform - Authentication Configuration

This module provides configuration settings for the authentication package.
"""
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'dev-secret-key-change-in-production'
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days

# Password Policies
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True

# Authentication Rate Limiting
AUTH_RATE_LIMIT_ATTEMPTS = 5
AUTH_RATE_LIMIT_PERIOD = 300  # 5 minutes

# County-specific Authentication
COUNTY_AUTH_TYPES: Dict[str, str] = {
    'ldap': 'LDAP Authentication',
    'oauth': 'OAuth Authentication',
    'local': 'Local Authentication'
}

# Role Definitions and Permissions
ROLES = {
    'ITAdmin': {
        'description': 'IT Administrator',
        'permissions': [
            'view_all_counties',
            'manage_users',
            'manage_system_config',
            'run_gis_export',
            'view_gis_export_status',
            'view_gis_export_results',
            'audit_log_view',
            'audit_log_export'
        ]
    },
    'Assessor': {
        'description': 'County Assessor',
        'permissions': [
            'view_assigned_counties',
            'run_gis_export',
            'view_gis_export_status',
            'view_gis_export_results',
            'audit_log_view'
        ]
    },
    'Staff': {
        'description': 'Staff Member',
        'permissions': [
            'view_assigned_counties',
            'run_gis_export',
            'view_gis_export_status',
            'view_gis_export_results'
        ]
    },
    'Auditor': {
        'description': 'Auditor',
        'permissions': [
            'view_assigned_counties',
            'audit_log_view',
            'audit_log_export'
        ]
    }
}

# Resource-based Access Control
RESOURCES = {
    'county': {
        'description': 'County data',
        'actions': ['view', 'export']
    },
    'user': {
        'description': 'User management',
        'actions': ['view', 'create', 'update', 'delete']
    },
    'config': {
        'description': 'System configuration',
        'actions': ['view', 'update']
    },
    'gis_export': {
        'description': 'GIS Export functionality',
        'actions': ['run', 'view_status', 'view_results']
    },
    'audit_log': {
        'description': 'Audit logs',
        'actions': ['view', 'export']
    }
}

# Permission Mapping
PERMISSIONS: Dict[str, Dict[str, List[str]]] = {
    'view_all_counties': {
        'resource': 'county',
        'actions': ['view'],
        'scope': 'all'
    },
    'view_assigned_counties': {
        'resource': 'county',
        'actions': ['view'],
        'scope': 'assigned'
    },
    'manage_users': {
        'resource': 'user',
        'actions': ['view', 'create', 'update', 'delete'],
        'scope': 'all'
    },
    'manage_system_config': {
        'resource': 'config',
        'actions': ['view', 'update'],
        'scope': 'all'
    },
    'run_gis_export': {
        'resource': 'gis_export',
        'actions': ['run'],
        'scope': 'assigned'
    },
    'view_gis_export_status': {
        'resource': 'gis_export',
        'actions': ['view_status'],
        'scope': 'assigned'
    },
    'view_gis_export_results': {
        'resource': 'gis_export',
        'actions': ['view_results'],
        'scope': 'assigned'
    },
    'audit_log_view': {
        'resource': 'audit_log',
        'actions': ['view'],
        'scope': 'assigned'
    },
    'audit_log_export': {
        'resource': 'audit_log',
        'actions': ['export'],
        'scope': 'assigned'
    }
}

# LDAP Configuration (for county integrations)
LDAP_ENABLED = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
LDAP_SERVER = os.environ.get('LDAP_SERVER', '')
LDAP_PORT = int(os.environ.get('LDAP_PORT', 389))
LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'false').lower() == 'true'
LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN', '')
LDAP_USER_DN = os.environ.get('LDAP_USER_DN', '')
LDAP_USER_RDN_ATTR = os.environ.get('LDAP_USER_RDN_ATTR', 'uid')
LDAP_USER_LOGIN_ATTR = os.environ.get('LDAP_USER_LOGIN_ATTR', 'uid')
LDAP_BIND_USER_DN = os.environ.get('LDAP_BIND_USER_DN', '')
LDAP_BIND_USER_PASSWORD = os.environ.get('LDAP_BIND_USER_PASSWORD', '')

# OAuth Configuration (for county integrations)
OAUTH_ENABLED = os.environ.get('OAUTH_ENABLED', 'false').lower() == 'true'
OAUTH_CLIENT_ID = os.environ.get('OAUTH_CLIENT_ID', '')
OAUTH_CLIENT_SECRET = os.environ.get('OAUTH_CLIENT_SECRET', '')
OAUTH_AUTHORIZE_URL = os.environ.get('OAUTH_AUTHORIZE_URL', '')
OAUTH_TOKEN_URL = os.environ.get('OAUTH_TOKEN_URL', '')
OAUTH_USERINFO_URL = os.environ.get('OAUTH_USERINFO_URL', '')
OAUTH_SCOPE = os.environ.get('OAUTH_SCOPE', 'openid email profile')
OAUTH_REDIRECT_URI = os.environ.get('OAUTH_REDIRECT_URI', '')

# Security Headers
SECURITY_HEADERS = {
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'",
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Referrer-Policy': 'same-origin',
    'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    'Pragma': 'no-cache'
}

# Two-Factor Authentication
MFA_ENABLED = os.environ.get('MFA_ENABLED', 'false').lower() == 'true'
MFA_ISSUER = os.environ.get('MFA_ISSUER', 'TerraFusion Platform')

# Function to get role permissions
def get_role_permissions(role: str) -> List[str]:
    """
    Get permissions for a specific role.
    
    Args:
        role: Role name
        
    Returns:
        List of permission names
    """
    if role not in ROLES:
        logger.warning(f"Unknown role: {role}")
        return []
    
    return ROLES[role]['permissions']

# Function to check permission
def has_permission(role: str, permission: str) -> bool:
    """
    Check if a role has a specific permission.
    
    Args:
        role: Role name
        permission: Permission name
        
    Returns:
        True if the role has the permission, False otherwise
    """
    if role not in ROLES:
        logger.warning(f"Unknown role: {role}")
        return False
    
    role_permissions = ROLES[role]['permissions']
    return permission in role_permissions

# Function to check resource action permission
def can_perform_action(role: str, resource: str, action: str, county_id: str = None) -> bool:
    """
    Check if a role can perform an action on a resource.
    
    Args:
        role: Role name
        resource: Resource name
        action: Action name
        county_id: County ID (for county-specific resources)
        
    Returns:
        True if the role can perform the action, False otherwise
    """
    if role not in ROLES:
        logger.warning(f"Unknown role: {role}")
        return False
    
    role_permissions = ROLES[role]['permissions']
    
    # Find permissions for this resource and action
    allowed_permissions = []
    for perm_name, perm_details in PERMISSIONS.items():
        if perm_details['resource'] == resource and action in perm_details['actions']:
            allowed_permissions.append(perm_name)
    
    # Check if the role has any of the allowed permissions
    has_any_permission = any(perm in role_permissions for perm in allowed_permissions)
    
    # For county-specific resources, we need to check county access separately
    # This would be implemented in a more specific function that checks the user's
    # county_access list against the requested county_id
    
    return has_any_permission