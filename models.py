"""
Models for TerraFusion SyncService database.

This module defines the database models for the SyncService application.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SyncPair(db.Model):
    """A pair of systems configured for synchronization."""
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    source_system = db.Column(db.String(50), nullable=False)
    target_system = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    config = db.Column(db.JSON)
    active = db.Column(db.Boolean, default=True)
    
    operations = db.relationship('SyncOperation', backref='sync_pair', lazy=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'config': self.config,
            'active': self.active
        }


class SyncOperation(db.Model):
    """A sync operation executed between systems."""
    
    id = db.Column(db.Integer, primary_key=True)
    sync_pair_id = db.Column(db.Integer, db.ForeignKey('sync_pair.id'), nullable=False)
    operation_type = db.Column(db.String(20), nullable=False)  # 'full', 'incremental'
    status = db.Column(db.String(20), nullable=False)  # 'pending', 'running', 'completed', 'failed'
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    total_records = db.Column(db.Integer, default=0)
    processed_records = db.Column(db.Integer, default=0)
    successful_records = db.Column(db.Integer, default=0)
    failed_records = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    metrics = db.Column(db.JSON)
    
    # Relationships
    audit_entries = db.relationship('AuditEntry', backref='operation', lazy=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'sync_pair_id': self.sync_pair_id,
            'operation_type': self.operation_type,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'error_message': self.error_message,
            'metrics': self.metrics
        }


class SystemMetrics(db.Model):
    """System performance metrics tracked over time."""
    
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
    operation_id = db.Column(db.Integer, db.ForeignKey('sync_operation.id'), nullable=True)
    
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