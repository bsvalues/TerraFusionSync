"""
TerraFusion Platform - Authentication Configuration

This module provides configuration settings for the authentication system,
including JWT secret key, token lifetimes, and other security settings.
"""

import os
import secrets
from datetime import timedelta

# JWT Secret Key (used for signing tokens)
# In production, set this in environment variable JWT_SECRET_KEY
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', secrets.token_hex(32))

# JWT Token Settings
JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)  # 1 hour
JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)  # 30 days

# JWT Algorithm
JWT_ALGORITHM = 'HS256'

# Token prefix for Authorization header
TOKEN_PREFIX = 'Bearer'

# RBAC Configuration
ROLE_PERMISSIONS = {
    'Admin': ['*'],  # Wildcard for all permissions
    'ITAdmin': [
        'manage_users',
        'manage_counties',
        'manage_sync_pairs',
        'view_audit_logs',
        'run_sync_operations',
        'view_metrics',
        'run_gis_export',
        'view_gis_export_status',
        'view_gis_export_results',
        'manage_system_config'
    ],
    'Assessor': [
        'manage_sync_pairs',
        'run_sync_operations',
        'view_metrics',
        'run_gis_export',
        'view_gis_export_status',
        'view_gis_export_results'
    ],
    'Staff': [
        'view_sync_pairs',
        'view_metrics',
        'run_gis_export',
        'view_gis_export_status',
        'view_gis_export_results'
    ],
    'Auditor': [
        'view_audit_logs',
        'view_metrics',
        'view_gis_export_status',
        'view_gis_export_results'
    ]
}

# Authentication Behavior
LOGIN_ATTEMPTS_LIMIT = 5  # Maximum failed login attempts before lockout
LOGIN_LOCKOUT_MINUTES = 15  # Lockout duration after exceeding attempts

# Session Configuration
SESSION_TYPE = 'filesystem'
SESSION_PERMANENT = True
PERMANENT_SESSION_LIFETIME = timedelta(days=1)
SESSION_FILE_DIR = os.environ.get('SESSION_FILE_DIR', './flask_session')
SESSION_KEY_PREFIX = 'tf_'

# Cookie Settings
SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to cookies
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection

# Password Policy
PASSWORD_MIN_LENGTH = 10
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBERS = True
PASSWORD_REQUIRE_SPECIAL_CHARS = True

# API Security
CORS_ALLOW_ORIGINS = os.environ.get('CORS_ALLOW_ORIGINS', '*').split(',')
RATE_LIMIT_DEFAULT = '100/hour'  # Default rate limit for API endpoints