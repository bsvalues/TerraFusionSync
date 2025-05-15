"""
TerraFusion Platform - Authentication Configuration

This module provides configuration settings for the authentication system,
including JWT parameters, password policies, and session settings.
"""

import os
from datetime import timedelta

# JWT Configuration
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "development-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)  # Short-lived access tokens
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)  # Longer-lived refresh tokens

# Password Policy
PASSWORD_MIN_LENGTH = 10
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True
PASSWORD_SPECIAL_CHARS = "!@#$%^&*()-_=+[]{}|;:,.<>?/"
PASSWORD_MAX_AGE_DAYS = 90  # Password expiration
PASSWORD_HISTORY_COUNT = 5  # Prevent reuse of recent passwords

# Session Configuration
SESSION_COOKIE_NAME = "terrafusion_session"
SESSION_COOKIE_SECURE = True  # Only send over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Not accessible via JavaScript
SESSION_COOKIE_SAMESITE = "Lax"  # CSRF protection
SESSION_TIMEOUT_MINUTES = 30  # Inactive session timeout

# Authentication Rate Limiting
LOGIN_RATE_LIMIT = "5/minute"  # Max 5 login attempts per minute
API_RATE_LIMIT = "60/minute"  # Max 60 API calls per minute

# RBAC Default Roles
DEFAULT_ROLES = {
    "Admin": {
        "description": "System Administrator with full access",
        "permissions": ["*"]  # Wildcard for all permissions
    },
    "Manager": {
        "description": "County Manager with administrative access",
        "permissions": [
            "view_data", "edit_data", "approve_changes", "run_reports",
            "manage_users", "view_audit_logs"
        ]
    },
    "Operator": {
        "description": "System Operator with data management capabilities",
        "permissions": [
            "view_data", "edit_data", "run_exports", "run_reports"
        ]
    },
    "Viewer": {
        "description": "Read-only user with view access",
        "permissions": ["view_data", "run_reports"]
    }
}

# County-specific permissions
COUNTY_PERMISSIONS = {
    "view_county_data": "View county data",
    "edit_county_data": "Edit county data",
    "run_county_exports": "Run export operations for county data",
    "view_county_reports": "View reports for county data"
}

# Feature-specific permissions
FEATURE_PERMISSIONS = {
    # Sync operations
    "view_sync_pairs": "View sync pairs",
    "create_sync_pairs": "Create new sync pairs",
    "edit_sync_pairs": "Edit sync pair settings",
    "delete_sync_pairs": "Delete sync pairs",
    "run_sync_operations": "Run sync operations",
    
    # GIS Export plugin
    "view_gis_export": "View GIS export jobs",
    "run_gis_export": "Create new GIS export jobs",
    "download_gis_exports": "Download completed GIS exports",
    
    # User management
    "view_users": "View user accounts",
    "create_users": "Create new user accounts",
    "edit_users": "Edit user accounts",
    "delete_users": "Delete user accounts",
    "assign_roles": "Assign roles to users",
    
    # Audit functionality
    "view_audit_logs": "View audit logs",
    "export_audit_logs": "Export audit logs"
}

# Multi-factor Authentication
MFA_ENABLED = os.environ.get("MFA_ENABLED", "false").lower() == "true"
MFA_METHODS = ["totp", "email"]  # Supported MFA methods

# Authentication Providers
AUTH_PROVIDERS = {
    "local": {
        "enabled": True,
        "name": "Local Authentication"
    },
    "ldap": {
        "enabled": os.environ.get("LDAP_ENABLED", "false").lower() == "true",
        "name": "County LDAP",
        "server": os.environ.get("LDAP_SERVER", ""),
        "base_dn": os.environ.get("LDAP_BASE_DN", ""),
        "bind_dn": os.environ.get("LDAP_BIND_DN", ""),
        "bind_password": os.environ.get("LDAP_BIND_PASSWORD", ""),
        "user_filter": os.environ.get("LDAP_USER_FILTER", "(sAMAccountName={username})")
    }
}