"""
Models for TerraFusion SyncService database.

This module defines the base database models for the SyncService application.
Note: The core sync models have been moved to apps/backend/models/
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask_sqlalchemy import SQLAlchemy

# Create a single SQLAlchemy instance to be used throughout the application
db = SQLAlchemy()


class SystemMetrics(db.Model):
    """System performance metrics tracked over time."""
    
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    active_connections = db.Column(db.Integer)
    response_time = db.Column(db.Float)
    error_count = db.Column(db.Integer)
    sync_operations_count = db.Column(db.Integer)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'active_connections': self.active_connections,
            'response_time': self.response_time,
            'error_count': self.error_count,
            'sync_operations_count': self.sync_operations_count
        }


class AuditEntry(db.Model):
    """
    Audit trail entry for tracking all system events and changes.
    This model is used for compliance, security, and debugging purposes.
    """
    
    __tablename__ = 'audit_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Who performed the action
    user_id = db.Column(db.String(100))  # Usually from authentication system
    username = db.Column(db.String(100))
    
    # What action was performed
    event_type = db.Column(db.String(50), nullable=False)  # 'sync_started', 'sync_completed', 'config_changed', etc.
    resource_type = db.Column(db.String(50), nullable=False)  # 'sync_pair', 'operation', 'system_config', etc.
    resource_id = db.Column(db.String(100))  # ID of the resource if applicable
    
    # Linked to a sync operation (if applicable)
    operation_id = db.Column(db.Integer, db.ForeignKey('sync_operations.id'), nullable=True)
    
    # Details of the action
    description = db.Column(db.Text, nullable=False)
    previous_state = db.Column(db.JSON, nullable=True)  # For tracking changes
    new_state = db.Column(db.JSON, nullable=True)  # For tracking changes
    
    # Additional metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(250))
    correlation_id = db.Column(db.String(100))  # For tracing across services
    
    # Severity of the event
    severity = db.Column(db.String(20), default='info')  # 'info', 'warning', 'error', 'critical'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'username': self.username,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'operation_id': self.operation_id,
            'description': self.description,
            'previous_state': self.previous_state,
            'new_state': self.new_state,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'correlation_id': self.correlation_id,
            'severity': self.severity
        }