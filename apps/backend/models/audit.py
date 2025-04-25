"""
Audit model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for audit entries, which
track all significant actions and events in the system.
"""

import json
from sqlalchemy import Column, Integer, String, JSON, DateTime, Text, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class AuditEntry(db.Model):
    """
    SQLAlchemy model for audit entries.
    
    Audit entries record all significant events and actions in the system
    for security, compliance, and troubleshooting purposes.
    """
    __tablename__ = 'audit_entries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Event metadata
    event_type = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=True)
    operation_id = Column(Integer, nullable=True)
    
    # Event description and severity
    description = Column(Text, nullable=False)
    severity = Column(String(32), nullable=False, default='info')
    
    # State changes
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    # User information
    user_id = Column(String(64), nullable=True)
    username = Column(String(128), nullable=True)
    
    # Timestamp and correlation
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    correlation_id = Column(String(64), nullable=True)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_audit_event_type', event_type),
        Index('idx_audit_resource', resource_type, resource_id),
        Index('idx_audit_timestamp', timestamp),
        Index('idx_audit_operation', operation_id),
    )
    
    def __init__(
        self,
        event_type,
        resource_type,
        description,
        **kwargs
    ):
        """Initialize a new audit entry."""
        self.event_type = event_type
        self.resource_type = resource_type
        self.description = description
        
        # Set other fields from kwargs if provided
        self.resource_id = kwargs.get('resource_id')
        self.operation_id = kwargs.get('operation_id')
        self.severity = kwargs.get('severity', 'info')
        self.previous_state = kwargs.get('previous_state')
        self.new_state = kwargs.get('new_state')
        self.user_id = kwargs.get('user_id')
        self.username = kwargs.get('username')
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.correlation_id = kwargs.get('correlation_id')
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'operation_id': self.operation_id,
            'description': self.description,
            'severity': self.severity,
            'previous_state': self.previous_state,
            'new_state': self.new_state,
            'user_id': self.user_id,
            'username': self.username,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'correlation_id': self.correlation_id
        }