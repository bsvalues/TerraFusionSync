"""
TerraFusion SyncService model for SyncOperations.

This module defines the SyncOperation model, representing an execution of a sync
operation between systems.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func
from .base import Base


class SyncOperation(Base):
    """
    SyncOperation model representing a sync operation execution.
    
    A SyncOperation tracks the execution of a sync between a source and target
    system, including timestamps, status, and results.
    """
    __tablename__ = 'sync_operations'
    
    id = Column(Integer, primary_key=True)
    sync_pair_id = Column(Integer, ForeignKey('sync_pairs.id'), nullable=False)
    
    # Operation type and execution details
    operation_type = Column(String(50), nullable=False)  # full, incremental, delta
    status = Column(String(50), nullable=False)  # pending, running, completed, failed
    
    # Source system configuration snapshot
    source_config = Column(JSON, nullable=True)
    
    # Target system configuration snapshot
    target_config = Column(JSON, nullable=True)
    
    # Field mapping configuration snapshot
    field_mappings = Column(JSON, nullable=True)
    
    # Execution details
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Result statistics
    processed_records = Column(Integer, nullable=True)
    successful_records = Column(Integer, nullable=True)
    failed_records = Column(Integer, nullable=True)
    
    # Detailed information
    error_message = Column(Text, nullable=True)
    execution_log = Column(JSON, nullable=True)
    metrics = Column(JSON, nullable=True)
    
    # Orchestration information
    triggered_by = Column(String(255), nullable=True)  # user ID, system, scheduler
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SyncOperation {self.id}: {self.operation_type} operation for sync_pair {self.sync_pair_id} ({self.status})>"
    
    @property
    def duration_seconds(self):
        """
        Calculate the duration of the operation in seconds.
        
        Returns:
            Duration in seconds, or None if operation hasn't completed
        """
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self):
        """
        Convert the SyncOperation to a dictionary representation.
        
        Returns:
            Dictionary representation of the SyncOperation
        """
        return {
            "id": self.id,
            "sync_pair_id": self.sync_pair_id,
            "operation_type": self.operation_type,
            "status": self.status,
            "source_config": self.source_config,
            "target_config": self.target_config,
            "field_mappings": self.field_mappings,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "processed_records": self.processed_records,
            "successful_records": self.successful_records,
            "failed_records": self.failed_records,
            "error_message": self.error_message,
            "execution_log": self.execution_log,
            "metrics": self.metrics,
            "triggered_by": self.triggered_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def create_from_sync_pair(cls, sync_pair, operation_type, triggered_by=None):
        """
        Create a new SyncOperation instance from a SyncPair.
        
        Args:
            sync_pair: SyncPair instance to use for configuration
            operation_type: Type of operation (full, incremental, delta)
            triggered_by: Who or what triggered the operation
            
        Returns:
            New SyncOperation instance
        """
        operation = cls(
            sync_pair_id=sync_pair.id,
            operation_type=operation_type,
            status="pending",
            source_config=sync_pair.source_system,
            target_config=sync_pair.target_system,
            field_mappings=sync_pair.mappings,
            triggered_by=triggered_by
        )
        
        return operation
    
    def start(self):
        """
        Mark the operation as started.
        """
        self.status = "running"
        self.started_at = datetime.utcnow()
    
    def complete(self, processed=0, successful=0, failed=0, metrics=None):
        """
        Mark the operation as completed.
        
        Args:
            processed: Number of records processed
            successful: Number of records successfully synced
            failed: Number of records that failed
            metrics: Optional metrics dictionary
        """
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        self.processed_records = processed
        self.successful_records = successful
        self.failed_records = failed
        
        if metrics:
            self.metrics = metrics
    
    def fail(self, error_message, processed=0, successful=0, failed=0):
        """
        Mark the operation as failed.
        
        Args:
            error_message: Error message explaining the failure
            processed: Number of records processed before failure
            successful: Number of records successfully synced before failure
            failed: Number of records that failed
        """
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
        self.processed_records = processed
        self.successful_records = successful
        self.failed_records = failed
    
    def log_event(self, event_type, message, details=None):
        """
        Log an event during execution.
        
        Args:
            event_type: Type of event (info, warning, error)
            message: Event message
            details: Optional details dictionary
        """
        if not self.execution_log:
            self.execution_log = []
        
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "message": message
        }
        
        if details:
            event["details"] = details
        
        if isinstance(self.execution_log, str):
            execution_log = json.loads(self.execution_log)
            execution_log.append(event)
            self.execution_log = execution_log
        else:
            self.execution_log.append(event)