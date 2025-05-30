"""
Script to drop and recreate database tables.

This script drops all tables in the database and recreates them based
on the current model definitions. This is useful during development
when the database schema changes.

WARNING: This will delete all data in the database.
"""

import os
import logging
from app import app, db

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_and_recreate_tables():
    """Drop all tables and recreate them."""
    with app.app_context():
        logger.info("Dropping all tables...")
        db.drop_all()
        logger.info("Creating all tables...")
        db.create_all()
        logger.info("Tables recreated successfully.")

if __name__ == "__main__":
    drop_and_recreate_tables()