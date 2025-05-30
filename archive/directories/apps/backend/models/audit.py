"""
TerraFusion SyncService model for Audit Entries.

This module defines the AuditEntry model, representing system audit trail entries
for tracking changes and actions in the system.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class AuditEntry(Base):
    """
    AuditEntry model representing an audit trail entry.
    
    An AuditEntry tracks actions and changes in the system, including who
    performed the action, what changed, and when it occurred.
    """
    __tablename__ = 'audit_entries'
    
    id = Column(Integer, primary_key=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # sync_started, sync_completed, config_changed, etc.
    severity = Column(String(20), nullable=False, default="info")  # info, warning, error, critical
    resource_type = Column(String(50), nullable=False)  # sync_pair, operation, system_config, etc.
    resource_id = Column(String(255), nullable=True)
    operation_id = Column(Integer, ForeignKey('sync_operations.id'), nullable=True)
    
    # Event description
    description = Column(Text, nullable=False)
    
    # State tracking
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    # Actor information
    user_id = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)  # Support IPv6 addresses
    user_agent = Column(String(512), nullable=True)  # Browser/client information
    
    # Tracing information
    correlation_id = Column(String(255), nullable=True)
    
    # Metadata
    timestamp = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<AuditEntry {self.id}: {self.event_type} ({self.severity}) - {self.resource_type}>"
    
    def to_dict(self):
        """
        Convert the AuditEntry to a dictionary representation.
        
        Returns:
            Dictionary representation of the AuditEntry
        """
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "operation_id": self.operation_id,
            "description": self.description,
            "previous_state": self.previous_state,
            "new_state": self.new_state,
            "user_id": self.user_id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def create(cls, event_type, resource_type, description, **kwargs):
        """
        Create a new AuditEntry instance.
        
        Args:
            event_type: Type of event (e.g., 'sync_started', 'sync_completed', 'config_changed')
            resource_type: Type of resource (e.g., 'sync_pair', 'operation', 'system_config')
            description: Human-readable description of the event
            **kwargs: Additional fields to set on the audit entry
            
        Returns:
            New AuditEntry instance
        """
        entry = cls(
            event_type=event_type,
            resource_type=resource_type,
            description=description,
            severity=kwargs.get("severity", "info")
        )
        
        # Set optional fields
        for field in [
            "resource_id", "operation_id", "previous_state", "new_state",
            "user_id", "username", "ip_address", "user_agent", "correlation_id"
        ]:
            if field in kwargs:
                setattr(entry, field, kwargs[field])
        
        return entry