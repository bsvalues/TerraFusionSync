"""
TerraFusion SyncService - Sync Models

This module provides database models for sync operations and pairs.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship

from apps.backend.database import get_shared_db

db = get_shared_db()

class SyncPair(db.Model):
    """
    Model representing a sync pair between source and target systems.
    
    A sync pair defines the connection between two systems and how data
    should flow between them.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    
    # Source configuration
    source_type = Column(String(50), nullable=False)
    source_config = Column(Text, nullable=False)  # JSON encoded configuration
    
    # Target configuration
    target_type = Column(String(50), nullable=False)
    target_config = Column(Text, nullable=False)  # JSON encoded configuration
    
    # Sync settings
    sync_frequency = Column(String(50), nullable=True)  # e.g., 'daily', 'hourly', etc.
    sync_schedule = Column(String(100), nullable=True)  # cron expression or similar
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    created_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_by = relationship("User", foreign_keys=[created_by_id])
    
    # Relationship with operations
    operations = relationship("SyncOperation", back_populates="sync_pair", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SyncPair {self.name}>"
    
    @property
    def last_operation(self):
        """Get the most recent sync operation for this pair."""
        if not self.operations:
            return None
        return sorted(self.operations, key=lambda op: op.created_at, reverse=True)[0]
    
    @property
    def success_rate(self):
        """Calculate the success rate of operations."""
        if not self.operations:
            return 0
        
        successful = len([op for op in self.operations if op.status == 'completed'])
        return round((successful / len(self.operations)) * 100, 2)

class SyncOperation(db.Model):
    """
    Model representing a sync operation execution.
    
    An operation is a specific execution of a sync pair, with start/end times,
    status, and results.
    """
    __tablename__ = 'sync_operations'
    
    id = Column(Integer, primary_key=True)
    sync_pair_id = Column(Integer, ForeignKey('sync_pairs.id'), nullable=False)
    
    # Operation details
    status = Column(String(50), default='pending')  # pending, running, completed, failed, cancelled
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    # Result statistics
    items_processed = Column(Integer, default=0)
    items_succeeded = Column(Integer, default=0)
    items_failed = Column(Integer, default=0)
    
    # Operation logs and data
    log = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)  # JSON encoded summary
    error_message = Column(Text, nullable=True)
    
    # Relations
    sync_pair = relationship("SyncPair", back_populates="operations")
    initiated_by_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    initiated_by = relationship("User")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SyncOperation {self.id} ({self.status})>"
    
    @property
    def duration_seconds(self):
        """Calculate the duration of the operation in seconds."""
        if not self.end_time:
            return None
        
        return (self.end_time - self.start_time).total_seconds()
    
    @property
    def success_rate(self):
        """Calculate the success rate of the operation."""
        if self.items_processed == 0:
            return 0
        
        return round((self.items_succeeded / self.items_processed) * 100, 2)

class AuditEntry(db.Model):
    """
    Model for audit trail entries.
    
    Records all significant system actions for compliance and debugging.
    """
    __tablename__ = 'audit_entries'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Event metadata
    event_type = Column(String(50), nullable=False)  # e.g., 'sync_started', 'user_login', etc.
    severity = Column(String(20), default='info')  # info, warning, error, critical
    
    # Resource details
    resource_type = Column(String(50), nullable=True)  # e.g., 'sync_pair', 'user', etc.
    resource_id = Column(String(50), nullable=True)
    operation_id = Column(Integer, nullable=True)
    
    # Event details
    description = Column(Text, nullable=False)
    previous_state = Column(Text, nullable=True)  # JSON encoded state before
    new_state = Column(Text, nullable=True)  # JSON encoded state after
    
    # User details
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    # Additional data
    additional_data = Column(Text, nullable=True)  # JSON encoded additional data
    correlation_id = Column(String(50), nullable=True)  # For grouping related events
    
    # Relations
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditEntry {self.id} - {self.event_type}>"

class SystemMetrics(db.Model):
    """
    Model for system metrics.
    
    Stores performance metrics for monitoring and alerting.
    """
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # System metrics
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    
    # Application metrics
    api_requests = Column(Integer, nullable=True)
    active_syncs = Column(Integer, nullable=True)
    active_users = Column(Integer, nullable=True)
    
    # Service health
    syncservice_health = Column(String(20), nullable=True)  # healthy, degraded, unhealthy
    api_gateway_health = Column(String(20), nullable=True)  # healthy, degraded, unhealthy
    database_health = Column(String(20), nullable=True)  # healthy, degraded, unhealthy
    
    # Performance metrics
    average_response_time = Column(Float, nullable=True)
    error_rate = Column(Float, nullable=True)
    
    # Collected metrics data
    raw_metrics = Column(Text, nullable=True)  # JSON encoded raw metrics
    
    def __repr__(self):
        return f"<SystemMetrics {self.id} - {self.timestamp}>"