"""
TerraFusion SyncService Onboarding Module

This module provides interactive tutorials and onboarding resources
for users based on their role in the system.
"""

import logging
import os

from apps.backend.database import db
from apps.backend.models.onboarding import UserOnboarding

logger = logging.getLogger(__name__)

def init_onboarding():
    """Initialize the onboarding module."""
    logger.info("Initializing onboarding module")
    
    def create_onboarding_blueprint():
        """Create the onboarding blueprint."""
        from .routes import onboarding_bp
        return onboarding_bp
    
    # Check if onboarding assets exist
    static_dir = os.path.join('static', 'images', 'onboarding')
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        logger.warning(f"Created onboarding static directory: {static_dir}")
    
    # Ensure onboarding blueprint and routes are loaded
    from . import routes
    
    return {
        "create_onboarding_blueprint": create_onboarding_blueprint,
    }