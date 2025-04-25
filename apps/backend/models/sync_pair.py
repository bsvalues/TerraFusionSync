"""
SyncPair model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync pairs, which
represent a configured connection between source and target systems.
"""

from sqlalchemy import Column, String, JSON, Boolean, Text, DateTime, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class SyncPair(db.Model):
    """
    SQLAlchemy model for sync pairs.
    
    Sync pairs represent a configured connection between source and target systems,
    including the mappings and transformations to apply to the data.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    
    # Configuration details for source and target systems
    source_system = Column(JSON, nullable=True)
    target_system = Column(JSON, nullable=True)
    
    # List of entities to sync
    entities = Column(JSON, nullable=True)
    
    # Field mappings and transformations
    mappings = Column(JSON, nullable=True)
    
    # Boolean to enable/disable this sync pair
    active = Column(Boolean, nullable=False, default=True)
    
    # Description and metadata
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_sync_at = Column(DateTime, nullable=True)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_sync_pair_active', active),
        Index('idx_sync_pair_last_sync', last_sync_at),
    )
    
    def __init__(
        self,
        id,
        name,
        **kwargs
    ):
        """Initialize a new sync pair."""
        self.id = id
        self.name = name
        
        # Set other fields from kwargs if provided
        self.source_system = kwargs.get('source_system')
        self.target_system = kwargs.get('target_system')
        self.entities = kwargs.get('entities')
        self.mappings = kwargs.get('mappings')
        self.active = kwargs.get('active', True)
        self.description = kwargs.get('description')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow())
        self.last_sync_at = kwargs.get('last_sync_at')
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'entities': self.entities,
            'mappings': self.mappings,
            'active': self.active,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_sync_at': self.last_sync_at.isoformat() if self.last_sync_at else None
        }