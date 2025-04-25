"""
Models package for TerraFusion SyncService platform.

This package provides SQLAlchemy models for the API Gateway and SyncService.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)

# Import models to make them available for imports from this package
from .audit import AuditEntry
from .system_metrics import SystemMetrics
from .sync_pair import SyncPair
from .sync_operation import SyncOperation