"""
Models package for TerraFusion SyncService platform.

This package contains SQLAlchemy models for the database.
"""

from app import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Import all models to make them available through the package
from .sync_pair import SyncPair
from .sync_operation import SyncOperation