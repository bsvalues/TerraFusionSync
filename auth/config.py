"""
TerraFusion Platform - Authentication Configuration

This module contains configuration settings for the TerraFusion Platform authentication system.
"""
import os
from typing import Dict, List

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'super-secret-development-key')
JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour in seconds
JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days in seconds
JWT_ALGORITHM = 'HS256'

# Authentication Configuration
AUTH_REDIRECT_PARAM = 'next'  # Query parameter for redirect after login

# LDAP Configuration
LDAP_ENABLED = False  # Set to True to enable LDAP authentication in production
LDAP_SERVER = os.environ.get('LDAP_SERVER', 'ldap.example.com')
LDAP_PORT = int(os.environ.get('LDAP_PORT', 389))
LDAP_USE_SSL = os.environ.get('LDAP_USE_SSL', 'false').lower() == 'true'
LDAP_BIND_DN = os.environ.get('LDAP_BIND_DN', 'cn=service-account,dc=example,dc=com')
LDAP_BIND_PASSWORD = os.environ.get('LDAP_BIND_PASSWORD', 'service-account-password')
LDAP_BASE_DN = os.environ.get('LDAP_BASE_DN', 'dc=example,dc=com')
LDAP_USER_FILTER = os.environ.get('LDAP_USER_FILTER', '(&(objectClass=person)(sAMAccountName={username}))')
LDAP_GROUP_FILTER = os.environ.get('LDAP_GROUP_FILTER', '(&(objectClass=group)(member={user_dn}))')

# Roles
ROLE_ADMIN = 'Admin'
ROLE_ASSESSOR = 'Assessor'
ROLE_STAFF = 'Staff'
ROLE_AUDITOR = 'Auditor'

# Permissions for each role
DEFAULT_PERMISSIONS = [
    'view_county_info',
    'view_dashboard',
]

ADMIN_PERMISSIONS = [
    'manage_users',
    'manage_counties',
    'manage_roles',
    'view_audit_logs',
    'view_system_metrics',
    'manage_system_settings',
    'run_system_tasks',
    'view_all_counties',
    'run_all_exports',
    'admin_dashboard',
    # Plugin-specific permissions
    'run_sync_job',
    'view_sync_job_status',
    'manage_sync_job',
    'run_valuation',
    'view_valuation_status',
    'run_reporting',
    'view_reporting_status',
    'view_reporting_results',
    'run_market_analysis',
    'view_market_analysis_status',
    'view_market_analysis_results',
    'run_gis_export',
    'view_gis_export_status',
    'view_gis_export_results',
]

ASSESSOR_PERMISSIONS = [
    'manage_county_settings',
    'view_county_metrics',
    'run_county_exports',
    'assessor_dashboard',
    # Plugin-specific permissions
    'run_sync_job',
    'view_sync_job_status',
    'run_valuation',
    'view_valuation_status',
    'run_reporting',
    'view_reporting_status',
    'view_reporting_results',
    'run_market_analysis',
    'view_market_analysis_status',
    'view_market_analysis_results',
    'run_gis_export',
    'view_gis_export_status',
    'view_gis_export_results',
]

STAFF_PERMISSIONS = [
    'view_county_metrics',
    'run_basic_exports',
    'staff_dashboard',
    # Plugin-specific permissions
    'view_sync_job_status',
    'view_valuation_status',
    'view_reporting_status',
    'view_reporting_results',
    'view_market_analysis_status',
    'view_market_analysis_results',
    'run_gis_export',
    'view_gis_export_status',
    'view_gis_export_results',
]

AUDITOR_PERMISSIONS = [
    'view_county_metrics',
    'view_audit_reports',
    'auditor_dashboard',
    # Plugin-specific permissions
    'view_sync_job_status',
    'view_valuation_status',
    'view_reporting_status',
    'view_reporting_results',
    'view_market_analysis_status',
    'view_market_analysis_results',
    'view_gis_export_status',
    'view_gis_export_results',
]

# Map roles to permissions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    ROLE_ADMIN: DEFAULT_PERMISSIONS + ADMIN_PERMISSIONS,
    ROLE_ASSESSOR: DEFAULT_PERMISSIONS + ASSESSOR_PERMISSIONS,
    ROLE_STAFF: DEFAULT_PERMISSIONS + STAFF_PERMISSIONS,
    ROLE_AUDITOR: DEFAULT_PERMISSIONS + AUDITOR_PERMISSIONS,
}