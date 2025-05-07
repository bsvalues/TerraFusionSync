"""
Database configuration for TerraFusion SyncService.

This module provides the shared database instance for the application.
"""

from flask_sqlalchemy import SQLAlchemy

# Create the database instance - but this should be initialized with app in the main app.py
db = SQLAlchemy()

def set_shared_db(shared_db_instance):
    """Set the shared database instance from the main application."""
    global db
    db = shared_db_instance