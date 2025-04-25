"""
SyncPair model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync pairs, which represent
pairs of source and target systems for data synchronization.
"""

import json
from sqlalchemy import Column, String, Boolean, JSON, DateTime, Text
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class SyncPair(db.Model):
    """
    SQLAlchemy model for sync pairs.
    
    A sync pair represents a configuration for transferring data between
    a source system and a target system, including field mappings.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    
    # System configurations stored as JSON
    source_system = Column(JSON, nullable=False)
    target_system = Column(JSON, nullable=False)
    
    # Entity and mapping configurations
    entities = Column(JSON, nullable=True)
    mappings = Column(JSON, nullable=True)
    
    # Status and metadata
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(64), nullable=True)
    
    def __init__(self, id, name, **kwargs):
        """Initialize a new sync pair."""
        self.id = id
        self.name = name
        
        # Set other fields from kwargs if provided
        self.description = kwargs.get('description')
        self.source_system = kwargs.get('source_system', {})
        self.target_system = kwargs.get('target_system', {})
        self.entities = kwargs.get('entities', [])
        self.mappings = kwargs.get('mappings', [])
        self.active = kwargs.get('active', True)
        self.created_by = kwargs.get('created_by')
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'entities': self.entities,
            'mappings': self.mappings,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a SyncPair instance from a dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            description=data.get('description'),
            source_system=data.get('source_system', {}),
            target_system=data.get('target_system', {}),
            entities=data.get('entities', []),
            mappings=data.get('mappings', []),
            active=data.get('active', True),
            created_by=data.get('created_by')
        )