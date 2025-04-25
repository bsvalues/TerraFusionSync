"""
Base models for the SyncService.

This module provides data models for representing sync operations, system state,
and configuration.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum, auto


class SyncStatus(Enum):
    """Enumeration of possible sync operation statuses."""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class OperationType(Enum):
    """Enumeration of possible sync operation types."""
    FULL = "full"           # Complete sync of all data
    INCREMENTAL = "incremental"  # Sync only changes since last sync
    DELTA = "delta"         # Sync only specific changes
    VALIDATION = "validation"    # Validate data without syncing
    REPAIR = "repair"       # Fix inconsistencies


class EntityStats:
    """Statistics for a single entity type in a sync operation."""
    
    def __init__(self):
        self.total = 0
        self.created = 0
        self.updated = 0
        self.deleted = 0
        self.skipped = 0
        self.failed = 0


class ValidationResult:
    """Result of a data validation operation."""
    
    def __init__(self):
        self.valid = True
        self.errors = []
        self.warnings = []


class SyncPair:
    """
    Configuration for a sync pair, defining source and target systems.
    """
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
        self.source_system = None  # Type: Dict[str, Any]
        self.target_system = None  # Type: Dict[str, Any]
        self.entities = None  # Type: List[Dict[str, Any]]
        self.mappings = None  # Type: List[Dict[str, Any]]
        self.active = True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "source_system": self.source_system,
            "target_system": self.target_system,
            "entities": self.entities,
            "mappings": self.mappings,
            "active": self.active
        }


class SyncOperationDetails:
    """
    Detailed information about a sync operation execution.
    """
    
    def __init__(self):
        self.start_time = None  # Type: datetime
        self.end_time = None  # Type: datetime
        self.entity_stats = None  # Type: Dict[str, EntityStats]
        self.logs = None  # Type: List[Dict[str, Any]]
        self.last_checkpoint = None  # Type: datetime
        self.next_checkpoint = None  # Type: datetime
        self.error = None
        self.metrics = None  # Type: Dict[str, Any]


class SyncOperation:
    """
    Representation of a sync operation, including configuration and results.
    """
    
    def __init__(self, id: int, sync_pair_id: str):
        self.id = id
        self.sync_pair_id = sync_pair_id
        self.details = None  # Type: SyncOperationDetails
        self.created_at = None  # Type: datetime
        self.scheduled_at = None  # Type: datetime
        self.completed_at = None  # Type: datetime
        self.status = SyncStatus.PENDING
        self.operation_type = OperationType.FULL
        self.user_id = None  # Type: str
        self.username = None  # Type: str
        self.priority = 0
        self.retry_count = None  # Type: str
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "sync_pair_id": self.sync_pair_id,
            "status": self.status.value if self.status else None,
            "operation_type": self.operation_type.value if self.operation_type else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "user_id": self.user_id,
            "username": self.username,
            "priority": self.priority,
            "retry_count": self.retry_count
        }