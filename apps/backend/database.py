"""
TerraFusion SyncService - Database Utilities

This module provides shared database access and utilities for the
TerraFusion SyncService platform.
"""

import logging
from flask_sqlalchemy import SQLAlchemy

# Configure logger
logger = logging.getLogger(__name__)

# Shared database instance
_shared_db = None

def set_shared_db(db_instance):
    """
    Set the shared database instance to be used across the application.
    
    Args:
        db_instance: SQLAlchemy database instance
    """
    global _shared_db
    _shared_db = db_instance
    logger.info("Shared database instance configured")

def get_shared_db():
    """
    Get the shared database instance.
    
    Returns:
        SQLAlchemy database instance
    
    Raises:
        RuntimeError: If shared database is not configured
    """
    if _shared_db is None:
        raise RuntimeError("Shared database instance has not been configured. "
                           "Call set_shared_db() before attempting to use the database.")
    return _shared_db

def init_db(app):
    """
    Initialize the database for a Flask application.
    
    Args:
        app: Flask application instance
    
    Returns:
        SQLAlchemy database instance
    """
    from sqlalchemy.orm import DeclarativeBase
    
    class Base(DeclarativeBase):
        pass
    
    db = SQLAlchemy(model_class=Base)
    db.init_app(app)
    
    set_shared_db(db)
    
    return db