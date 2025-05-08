"""
TerraFusion Onboarding Module

This module provides an interactive onboarding experience for new users
of the TerraFusion platform, with role-specific tutorials.
"""

import logging
from flask import Flask

from apps.backend.database import db
from apps.backend.onboarding.routes import onboarding_bp

logger = logging.getLogger(__name__)

def init_onboarding(app: Flask):
    """
    Initialize the onboarding module and register its routes with the Flask app.
    
    Args:
        app: The Flask application instance
    """
    # Register the blueprint
    app.register_blueprint(onboarding_bp)
    
    logger.info("Initializing onboarding module")
    
    # Ensure database tables are created
    with app.app_context():
        from apps.backend.models.onboarding import UserOnboarding
        
        # Create tables if they don't exist
        if not app.config.get('ONBOARDING_INITIALIZED', False):
            db.create_all()
            app.config['ONBOARDING_INITIALIZED'] = True
            logger.info("Onboarding database tables created")
    
    return app