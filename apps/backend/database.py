"""
TerraFusion Database Module

This module provides a shared SQLAlchemy database instance for the application.
"""

import logging
from flask_sqlalchemy import SQLAlchemy

# Create a shared database instance
db = SQLAlchemy()

logger = logging.getLogger(__name__)

def set_shared_db(app_db):
    """
    Set a shared database instance.
    
    This allows other modules to import the database instance from this module.
    
    Args:
        app_db: The SQLAlchemy database instance
    """
    global db
    db = app_db
    logger.info("Shared database instance configured")
    
    return db