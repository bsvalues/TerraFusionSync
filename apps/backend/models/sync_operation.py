"""
SyncOperation model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for sync operations, which
represent individual data synchronization tasks.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, ForeignKey, Index
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
    
    # Reference to the sync pair
    sync_pair_id = Column(String(64), ForeignKey('sync_pairs.id'), nullable=False)
    
    # Operation type and status
    operation_type = Column(String(32), nullable=False, default='full_sync')
    status = Column(String(32), nullable=False, default='pending')
    
    # Operation configuration
    configuration = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Results and statistics
    result = Column(JSON, nullable=True)
    records_processed = Column(Integer, nullable=True)
    records_succeeded = Column(Integer, nullable=True)
    records_failed = Column(Integer, nullable=True)
    
    # Error details
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    
    # Correlation ID for tracking related operations
    correlation_id = Column(String(64), nullable=True)
    
    # Create indexes for common queries
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
        
        # Set other fields from kwargs if provided
        self.operation_type = kwargs.get('operation_type', 'full_sync')
        self.status = kwargs.get('status', 'pending')
        self.configuration = kwargs.get('configuration')
        self.created_at = kwargs.get('created_at', datetime.utcnow())
        self.scheduled_at = kwargs.get('scheduled_at')
        self.started_at = kwargs.get('started_at')
        self.completed_at = kwargs.get('completed_at')
        self.result = kwargs.get('result')
        self.records_processed = kwargs.get('records_processed')
        self.records_succeeded = kwargs.get('records_succeeded')
        self.records_failed = kwargs.get('records_failed')
        self.error_message = kwargs.get('error_message')
        self.error_details = kwargs.get('error_details')
        self.retry_count = kwargs.get('retry_count', 0)
        self.correlation_id = kwargs.get('correlation_id')
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'sync_pair_id': self.sync_pair_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'configuration': self.configuration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'records_processed': self.records_processed,
            'records_succeeded': self.records_succeeded,
            'records_failed': self.records_failed,
            'error_message': self.error_message,
            'error_details': self.error_details,
            'retry_count': self.retry_count,
            'correlation_id': self.correlation_id
        }