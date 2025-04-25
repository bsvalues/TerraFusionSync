"""
TerraFusion SyncService database module.

This module initializes and configures the database connection for the application.
"""

import os
from flask_sqlalchemy import SQLAlchemy
from .models.base import Base

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

def init_app(app):
    """
    Initialize database with the given Flask application.
    
    Args:
        app: Flask application instance
    """
    # Configure the database connection
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize the app with Flask-SQLAlchemy
    db.init_app(app)
    
    # Create all tables if they don't exist
    with app.app_context():
        # Import all models to ensure they're registered with SQLAlchemy
        from .models import SyncPair, SyncOperation, AuditEntry, SystemMetrics
        
        # Create database tables
        db.create_all()
        
def get_session():
    """
    Get a database session.
    
    Returns:
        SQLAlchemy session object
    """
    return db.session