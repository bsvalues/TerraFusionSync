"""
SyncOperation model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync operations, which
represent individual data synchronization tasks.
"""

from sqlalchemy import Column, String, JSON, Integer, ForeignKey, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class SyncOperation(db.Model):
    """
    SQLAlchemy model for sync operations.
    
    Sync operations represent individual data synchronization tasks,
    including their configuration, status, and results.
    """
    __tablename__ = 'sync_operations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Reference to the sync pair this operation is for
    sync_pair_id = Column(String(64), ForeignKey('sync_pairs.id'), nullable=False)
    
    # Operation details
    operation_type = Column(String(32), nullable=False, default='full_sync')
    status = Column(String(32), nullable=False, default='pending')
    
    # Custom configuration for this specific operation
    configuration = Column(JSON, nullable=True)
    
    # Timing information
    created_at = Column(db.DateTime, default=func.now(), nullable=False)
    scheduled_at = Column(db.DateTime, nullable=True)
    started_at = Column(db.DateTime, nullable=True)
    completed_at = Column(db.DateTime, nullable=True)
    
    # Results and statistics
    result = Column(JSON, nullable=True)
    records_processed = Column(Integer, nullable=True)
    records_succeeded = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    
    # Error information
    error_message = Column(String, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Tracking and correlation
    correlation_id = Column(String(64), nullable=True)
    
    __table_args__ = (
        Index('idx_sync_op_status', status),
        Index('idx_sync_op_pair', sync_pair_id),
        Index('idx_sync_op_created', created_at),
        Index('idx_sync_op_correlation', correlation_id),
    )
    
    def __init__(
        self,
        sync_pair_id,
        **kwargs
    ):
        """Initialize a new sync operation."""
        self.sync_pair_id = sync_pair_id
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        result = {
            'id': self.id,
            'sync_pair_id': self.sync_pair_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'configuration': self.configuration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'records_processed': self.records_processed,
            'records_succeeded': self.records_succeeded,
            'records_failed': self.records_failed,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'retry_count': self.retry_count,
            'correlation_id': self.correlation_id
        }
        return result