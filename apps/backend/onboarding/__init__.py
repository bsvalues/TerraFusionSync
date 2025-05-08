"""
TerraFusion SyncService - Onboarding Module

This module provides an interactive onboarding experience for new users,
with role-specific tutorials and progress tracking.
"""

import logging
from flask import Blueprint

# Configure logger
logger = logging.getLogger(__name__)

# Create blueprint
onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/onboarding',
                         template_folder='../../templates/onboarding')

# Import routes
from . import routes

def init_app(app):
    """
    Initialize the onboarding module for a Flask application.
    
    Args:
        app: Flask application instance
    """
    logger.info("Initializing onboarding module")
    
    # Create tables if they don't exist
    with app.app_context():
        from apps.backend.models.onboarding import UserOnboarding, OnboardingEvent
        from apps.backend.database import get_shared_db
        
        db = get_shared_db()
        db.create_all()
        logger.info("Onboarding database tables created")
    
    # Register blueprint
    app.register_blueprint(onboarding_bp)

# Alias for compatibility with app.py
init_onboarding = init_app