"""
Database setup and utilities for the TerraFusion SyncService platform.
"""

# Import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy

# Create a reference to the database instance without initializing it yet
# This avoids circular imports
db = None

def init_db(app_db):
    """
    Initialize the database reference with the actual instance.
    
    Args:
        app_db: The Flask-SQLAlchemy database instance
    """
    global db
    db = app_db