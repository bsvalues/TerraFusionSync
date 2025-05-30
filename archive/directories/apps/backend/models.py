"""
Data models for the TerraFusion SyncService platform.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
import json

# Define a reference to the db that will be initialized later
# This avoids circular imports
db = None

def init_models(app_db):
    """
    Initialize the models with the database instance.
    
    Args:
        app_db: The SQLAlchemy database instance
    """
    global db
    db = app_db

# Audit Trail model
class AuditEntry(db.Model):
    """
    Audit entry for tracking system events, user actions, and changes.
    """
    __tablename__ = 'audit_entries'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True, index=True) 
    resource_id = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=False)
    severity = Column(String(16), default='info', index=True)
    user_id = Column(String(64), nullable=True, index=True)
    username = Column(String(128), nullable=True, index=True)
    ip_address = Column(String(64), nullable=True)
    operation_id = Column(Integer, nullable=True, index=True)
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'severity': self.severity,
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'operation_id': self.operation_id,
            'previous_state': self.previous_state,
            'new_state': self.new_state
        }

# Sync Pair model
class SyncPair(db.Model):
    """
    Represents a configured sync pair between source and target systems.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    source_type = Column(String(64), nullable=False)
    source_config = Column(JSON, nullable=False)
    target_type = Column(String(64), nullable=False)
    target_config = Column(JSON, nullable=False)
    sync_schedule = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(128), nullable=True)
    
    # Relationships
    operations = relationship("SyncOperation", back_populates="sync_pair")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'source_type': self.source_type,
            'source_config': self.source_config,
            'target_type': self.target_type,
            'target_config': self.target_config,
            'sync_schedule': self.sync_schedule,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'created_by': self.created_by
        }

# Sync Operation model
class SyncOperation(db.Model):
    """
    Represents a sync operation between source and target systems.
    """
    __tablename__ = 'sync_operations'
    
    id = Column(Integer, primary_key=True)
    sync_pair_id = Column(Integer, ForeignKey('sync_pairs.id'), nullable=False, index=True)
    status = Column(String(32), default='pending', index=True)
    sync_type = Column(String(32), default='full', index=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    total_records = Column(Integer, default=0)
    processed_records = Column(Integer, default=0)
    successful_records = Column(Integer, default=0)
    failed_records = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_by = Column(String(128), nullable=True)
    
    # Relationships
    sync_pair = relationship("SyncPair", back_populates="operations")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'sync_pair_id': self.sync_pair_id,
            'status': self.status,
            'sync_type': self.sync_type,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'successful_records': self.successful_records,
            'failed_records': self.failed_records,
            'error_message': self.error_message,
            'created_by': self.created_by
        }

# System Metrics model
class SystemMetrics(db.Model):
    """
    Stores system metrics data for monitoring.
    """
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    service = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, index=True)
    cpu_usage = Column(Float, nullable=False)
    memory_usage = Column(Float, nullable=False)
    disk_usage = Column(Float, nullable=False)
    active_connections = Column(Integer, default=0)
    response_time = Column(Float, nullable=True)
    error_count = Column(Integer, default=0)
    sync_operations_count = Column(Integer, default=0)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'service': self.service,
            'status': self.status,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'active_connections': self.active_connections,
            'response_time': self.response_time,
            'error_count': self.error_count,
            'sync_operations_count': self.sync_operations_count
        }


# User Onboarding model
class UserOnboarding(db.Model):
    """
    Tracks user onboarding progress and tutorial completion.
    This enables personalized, role-based onboarding experiences.
    """
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), nullable=False, index=True)
    username = Column(String(128), nullable=False, index=True)
    role = Column(String(64), nullable=False, index=True)
    onboarding_started = Column(DateTime, default=datetime.utcnow)
    onboarding_completed = Column(DateTime, nullable=True)
    current_step = Column(Integer, default=1)
    completed_steps = Column(JSON, default=lambda: json.dumps([]))
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    dismissed = Column(Boolean, default=False)
    tutorial_config = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'onboarding_started': self.onboarding_started.isoformat() if self.onboarding_started else None,
            'onboarding_completed': self.onboarding_completed.isoformat() if self.onboarding_completed else None,
            'current_step': self.current_step,
            'completed_steps': json.loads(self.completed_steps) if isinstance(self.completed_steps, str) else self.completed_steps,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'dismissed': self.dismissed,
            'tutorial_config': self.tutorial_config
        }
    
    def mark_step_completed(self, step_number: int) -> None:
        """Mark a step as completed and update the current step if needed."""
        completed = json.loads(self.completed_steps) if isinstance(self.completed_steps, str) else self.completed_steps or []
        if step_number not in completed:
            completed.append(step_number)
            self.completed_steps = json.dumps(completed)
        
        # Move to the next step if we just completed the current one
        if self.current_step == step_number:
            self.current_step = step_number + 1
        
        self.last_activity = datetime.utcnow()
    
    def is_step_completed(self, step_number: int) -> bool:
        """Check if a specific step has been completed."""
        completed = json.loads(self.completed_steps) if isinstance(self.completed_steps, str) else self.completed_steps or []
        return step_number in completed
    
    def complete_onboarding(self) -> None:
        """Mark the onboarding process as completed."""
        self.onboarding_completed = datetime.utcnow()
        self.dismissed = True