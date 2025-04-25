"""
Base models for the SyncService.

This module defines the core data models used throughout the SyncService.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass


class SyncType(str, Enum):
    """Type of synchronization operation."""
    FULL = "full"
    INCREMENTAL = "incremental"
    DELTA = "delta"


class SyncStatus(str, Enum):
    """Status of a sync operation."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class RetryStrategy:
    """Strategy for retrying failed operations."""
    should_retry: bool
    delay_seconds: int
    max_attempts: int
    retry_subset: bool = False
    batch_size_reduction: float = 1.0


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[Dict[str, Any]] = None
    warnings: List[Dict[str, Any]] = None


@dataclass
class SourceRecord:
    """Record from a source system."""
    id: str
    entity_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    last_modified: datetime = None


@dataclass
class TransformedRecord:
    """Record after transformation."""
    source_id: str
    entity_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    validation_result: ValidationResult = None


@dataclass
class TargetRecord:
    """Record in the target system."""
    id: str
    source_id: str
    entity_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None
    last_modified: datetime = None


@dataclass
class EntityStats:
    """Statistics about entity processing."""
    entity_type: str
    total_count: int = 0
    processed_count: int = 0
    success_count: int = 0
    error_count: int = 0
    skipped_count: int = 0


@dataclass
class SyncOperationDetails:
    """Detailed information about a sync operation."""
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    records_skipped: int = 0
    entity_stats: Dict[str, EntityStats] = None
    error_details: List[Dict[str, Any]] = None
    start_time: datetime = None
    end_time: datetime = None
    duration_seconds: float = 0
    metadata: Dict[str, Any] = None


@dataclass
class SyncOperation:
    """A synchronization operation."""
    id: Union[int, str]
    sync_pair_id: Union[int, str]
    operation_type: SyncType
    status: SyncStatus = SyncStatus.QUEUED
    details: SyncOperationDetails = None
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    
    # For self-healing orchestrator
    source_system: str = None
    target_system: str = None
    retry_count: int = 0
    last_error: str = None