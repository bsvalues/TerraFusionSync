"""
TerraFusion Platform - Authentication Configuration

This module provides configuration settings for the authentication system.
"""
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# General Authentication Settings
AUTH_ENABLED = True
SESSION_LIFETIME = 24 * 60 * 60  # 24 hours in seconds
REFRESH_TOKEN_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds

# JWT Settings
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.environ.get('FLASK_SECRET_KEY', 'default_jwt_secret_key'))
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = 8 * 60 * 60  # 8 hours in seconds
JWT_REFRESH_TOKEN_EXPIRES = 7 * 24 * 60 * 60  # 7 days in seconds

# Password Settings
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True
PASSWORD_MAX_AGE = 90 * 24 * 60 * 60  # 90 days in seconds

# Rate Limiting
LOGIN_RATE_LIMIT = 5  # Max login attempts per minute
LOGIN_LOCKOUT_DURATION = 15 * 60  # 15 minutes in seconds

# LDAP Integration Settings (if applicable)
LDAP_ENABLED = os.environ.get('LDAP_ENABLED', 'false').lower() == 'true'
LDAP_SERVER = os.environ.get('LDAP_SERVER', '')
LDAP_PORT = int(os.environ.get('LDAP_PORT', '389'))
LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'false').lower() == 'true'
LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', '')
LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', '')
LDAP_USER_BASE_DN = os.environ.get('LDAP_USER_BASE_DN', '')
LDAP_USER_SEARCH_FILTER = os.environ.get('LDAP_USER_SEARCH_FILTER', '(sAMAccountName=%s)')
LDAP_GROUP_BASE_DN = os.environ.get('LDAP_GROUP_BASE_DN', '')
LDAP_GROUP_SEARCH_FILTER = os.environ.get('LDAP_GROUP_SEARCH_FILTER', '(member=%s)')

# Role & Permission Mappings
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    'ITAdmin': ['*'],  # Wildcard for all permissions
    'Assessor': [
        'run_sync', 'view_sync', 
        'run_validation', 'view_validation',
        'run_reporting', 'view_reporting',
        'run_gis_export', 'view_gis_export',
        'run_market_analysis', 'view_market_analysis'
    ],
    'Staff': [
        'view_sync', 'view_validation', 'view_reporting',
        'view_gis_export', 'view_market_analysis'
    ],
    'Auditor': ['view_audit_logs', 'view_reporting', 'view_validation']
}

# LDAP Group to Role Mappings (if applicable)
LDAP_GROUP_ROLE_MAPPINGS: Dict[str, str] = {
    'CN=IT Administrators,OU=Security Groups,DC=county,DC=local': 'ITAdmin',
    'CN=Assessors,OU=Security Groups,DC=county,DC=local': 'Assessor',
    'CN=Staff,OU=Security Groups,DC=county,DC=local': 'Staff',
    'CN=Auditors,OU=Security Groups,DC=county,DC=local': 'Auditor'
}

# County Access Control
COUNTY_ACCESS_REQUIRED = True
DEFAULT_COUNTY_ACCESS = []  # Default counties accessible for new users
ADMIN_COUNTY_ACCESS = ['*']  # Wildcard for all counties (for ITAdmin role)

# Restricted IPs (optional)
RESTRICT_TO_COUNTY_NETWORK = os.environ.get('RESTRICT_TO_COUNTY_NETWORK', 'false').lower() == 'true'
COUNTY_NETWORK_IPS = os.environ.get('COUNTY_NETWORK_IPS', '').split(',')
ALLOWED_IPS = os.environ.get('ALLOWED_IPS', '').split(',') + ['127.0.0.1', 'localhost']

# Audit Logging
AUDIT_LOGIN_ATTEMPTS = True
AUDIT_USER_ACTIONS = True
AUDIT_RETENTION_DAYS = 365  # 1 year

# MFA Settings (for future implementation)
MFA_ENABLED = False
MFA_METHODS = ['totp']  # Time-based One-Time Password

# Get configuration level from env (development, testing, production)
ENV = os.environ.get('FLASK_ENV', 'development')
if ENV == 'development':
    # Override settings for development
    PASSWORD_MIN_LENGTH = 4
    PASSWORD_REQUIRE_UPPERCASE = False
    PASSWORD_REQUIRE_LOWERCASE = False
    PASSWORD_REQUIRE_DIGIT = False
    PASSWORD_REQUIRE_SPECIAL = False
    LOGIN_RATE_LIMIT = 999  # Essentially disabled
    RESTRICT_TO_COUNTY_NETWORK = False

# Log configuration
logger.info(f"Authentication configuration loaded for environment: {ENV}")
if LDAP_ENABLED:
    logger.info("LDAP authentication enabled")
if RESTRICT_TO_COUNTY_NETWORK:
    logger.info("County network IP restriction enabled")