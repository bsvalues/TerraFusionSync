"""
API package for the TerraFusion SyncService platform.

This package contains API endpoints for the platform,
including rollback API for ITAdmin users.
"""

try:
    from flask import Blueprint
    
    # Create a shared blueprint for validation API
    validation_bp = Blueprint('validation', __name__, url_prefix='/api/validation')
except ImportError:
    validation_bp = None