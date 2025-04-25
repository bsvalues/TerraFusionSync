"""
SyncPair model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync pairs, which
represent a source-target relationship for data synchronization.
"""

import json
from sqlalchemy import Column, String, JSON, Boolean, Integer, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class SyncPair(db.Model):
    """
    SQLAlchemy model for sync pairs.
    
    Sync pairs define the configuration for data synchronization
    between a source and target system.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(String(256), nullable=True)
    
    # Source system configuration
    source_system_type = Column(String(32), nullable=False)
    source_system = Column(JSON, nullable=True)
    
    # Target system configuration
    target_system_type = Column(String(32), nullable=False)
    target_system = Column(JSON, nullable=True)
    
    # Field mappings and transformation rules
    mappings = Column(JSON, nullable=True)
    
    # Synchronization settings
    sync_interval_minutes = Column(Integer, nullable=True)
    sync_schedule = Column(String(128), nullable=True)
    sync_enabled = Column(Boolean, default=True, nullable=False)
    
    # Change detection settings
    change_detection_method = Column(String(32), default='full_scan', nullable=False)
    incremental_key = Column(String(64), nullable=True)
    
    # Conflict resolution strategy
    conflict_resolution = Column(String(32), default='source_wins', nullable=False)
    
    # Audit fields
    created_at = Column(db.DateTime, default=func.now(), nullable=False)
    updated_at = Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(64), nullable=True)
    updated_by = Column(String(64), nullable=True)
    
    # Validation and security options
    validation_rules = Column(JSON, nullable=True)
    data_encryption = Column(Boolean, default=False, nullable=False)
    
    # Status tracking
    last_sync_at = Column(db.DateTime, nullable=True)
    last_sync_status = Column(String(32), nullable=True)
    
    __table_args__ = (
        Index('idx_sync_pair_source', source_system_type),
        Index('idx_sync_pair_target', target_system_type),
        Index('idx_sync_pair_enabled', sync_enabled),
    )
    
    def __init__(
        self,
        id,
        name,
        source_system_type,
        target_system_type,
        **kwargs
    ):
        """Initialize a new sync pair."""
        self.id = id
        self.name = name
        self.source_system_type = source_system_type
        self.target_system_type = target_system_type
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_system_type': self.source_system_type,
            'source_system': self.source_system,
            'target_system_type': self.target_system_type,
            'target_system': self.target_system,
            'mappings': self.mappings,
            'sync_interval_minutes': self.sync_interval_minutes,
            'sync_schedule': self.sync_schedule,
            'sync_enabled': self.sync_enabled,
            'change_detection_method': self.change_detection_method,
            'incremental_key': self.incremental_key,
            'conflict_resolution': self.conflict_resolution,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'updated_by': self.updated_by,
            'validation_rules': self.validation_rules,
            'data_encryption': self.data_encryption,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None,
            'last_sync_status': self.last_sync_status
        }
        return result