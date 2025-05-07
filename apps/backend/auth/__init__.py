"""
Authentication package for the TerraFusion SyncService platform.

This package provides authentication and authorization functionality
for the API Gateway, integrating with the County's existing
Azure AD identity infrastructure.

It provides both standard authentication and County-specific RBAC functionality
with AD-style user accounts, role permissions, and comprehensive audit logging.
"""

# Standard auth functionality
from .auth import requires_auth, get_current_user, init_auth_routes, requires_role

# County RBAC functionality
try:
    from .county_rbac import (
        requires_county_auth, requires_county_permission, 
        get_current_county_user, authenticate_county_user,
        init_county_auth_routes, log_user_action,
        COUNTY_ROLES, COUNTY_USERS
    )
    COUNTY_RBAC_AVAILABLE = True
except ImportError:
    COUNTY_RBAC_AVAILABLE = False