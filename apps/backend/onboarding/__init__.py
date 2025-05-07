"""
Onboarding module for TerraFusion SyncService.

This module provides interactive onboarding and tutorials 
for new users based on their role.
"""

import logging

# Configure logging
logger = logging.getLogger(__name__)

def init_onboarding():
    """Initialize the onboarding module."""
    logger.info("Initializing onboarding module")
    
    # Import here to avoid circular imports
    from .routes import create_onboarding_blueprint
    
    return {
        "create_onboarding_blueprint": create_onboarding_blueprint
    }