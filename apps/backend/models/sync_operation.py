"""
SyncOperation model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync operations, which represent
individual synchronization jobs executed by the system.
"""

import json
from sqlalchemy import Column, Integer, String, JSON, DateTime, ForeignKey, Enum, Text, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db
from ..syncservice.syncservice.models.base import SyncStatus, OperationType


class SyncOperation(db.Model):
    """
    SQLAlchemy model for sync operations.
    
    A sync operation represents a single synchronization job, including its
    status, progress, and results.
    """
    __tablename__ = 'sync_operations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_pair_id = Column(String(64), ForeignKey('sync_pairs.id'), nullable=False)
    
    # Operation type and status
    operation_type = Column(String(32), nullable=False)
    status = Column(String(32), nullable=False, default='pending')
    
    # Timestamps for operation lifecycle
    created_at = Column(DateTime, default=func.now(), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Execution details
    details = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # User information
    user_id = Column(String(64), nullable=True)
    username = Column(String(128), nullable=True)
    
    # Additional metadata
    priority = Column(Integer, default=0)
    retry_count = Column(String(16), nullable=True)
    correlation_id = Column(String(64), nullable=True)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_sync_ops_status', status),
        Index('idx_sync_ops_pair_id', sync_pair_id),
        Index('idx_sync_ops_pair_status', sync_pair_id, status),
    )
    
    def __init__(self, sync_pair_id, **kwargs):
        """Initialize a new sync operation."""
        self.sync_pair_id = sync_pair_id
        
        # Set other fields from kwargs if provided
        self.operation_type = kwargs.get('operation_type', 'full')
        self.status = kwargs.get('status', 'pending')
        self.scheduled_at = kwargs.get('scheduled_at')
        self.user_id = kwargs.get('user_id')
        self.username = kwargs.get('username')
        self.priority = kwargs.get('priority', 0)
        self.retry_count = kwargs.get('retry_count')
        self.correlation_id = kwargs.get('correlation_id')
        self.details = kwargs.get('details', {})
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'sync_pair_id': self.sync_pair_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'details': self.details,
            'error': self.error,
            'user_id': self.user_id,
            'username': self.username,
            'priority': self.priority,
            'retry_count': self.retry_count,
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a SyncOperation instance from a dictionary."""
        details = data.get('details', {})
        
        # Handle both string and dict for details
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except (json.JSONDecodeError, TypeError):
                details = {}
        
        return cls(
            sync_pair_id=data.get('sync_pair_id'),
            operation_type=data.get('operation_type', 'full'),
            status=data.get('status', 'pending'),
            scheduled_at=data.get('scheduled_at'),
            user_id=data.get('user_id'),
            username=data.get('username'),
            priority=data.get('priority', 0),
            retry_count=data.get('retry_count'),
            correlation_id=data.get('correlation_id'),
            details=details
        )