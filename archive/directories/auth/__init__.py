"""
TerraFusion Platform - Authentication Package

This package provides authentication, authorization, and audit functionality.
"""
import logging
from flask import Flask

from auth.routes import auth
from auth.error_handlers import error_handlers

logger = logging.getLogger(__name__)

def init_app(app: Flask) -> None:
    """
    Initialize the authentication package with the Flask application.
    
    Args:
        app: Flask application
    """
    # Register blueprints
    app.register_blueprint(auth)
    app.register_blueprint(error_handlers)
    
    logger.info("Authentication package initialized")