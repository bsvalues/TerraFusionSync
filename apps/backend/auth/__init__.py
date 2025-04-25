"""
Authentication package for the TerraFusion SyncService platform.

This package provides authentication and authorization functionality
for the API Gateway, integrating with the County's existing
Azure AD identity infrastructure.
"""

from .auth import requires_auth, get_current_user, init_auth_routes