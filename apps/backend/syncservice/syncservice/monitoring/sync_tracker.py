"""
Sync operation tracking for SyncService.

This module provides utilities for tracking sync operations, their status,
and providing insights about sync performance and results.
"""

import os
import json
import uuid
import logging
import threading
import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Thread lock for sync tracker operations
_sync_tracker_lock = threading.RLock()

# Directory for sync status persistence
SYNC_STATUS_DIR = os.environ.get('SYNC_STATUS_DIR', os.path.join('data', 'sync_status'))

# Ensure sync status directory exists
os.makedirs(SYNC_STATUS_DIR, exist_ok=True)


class SyncStatus(str, Enum):
    """Enumeration of sync operation statuses."""
    
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class SyncType(str, Enum):
    """Enumeration of sync operation types."""
    
    FULL = "full"
    INCREMENTAL = "incremental"


class SyncOperation:
    """
    Class representing a sync operation.
    
    Attributes:
        sync_id: Unique identifier for the sync operation
        sync_type: Type of sync operation (full or incremental)
        source_system: Source system name
        target_system: Target system name
        entity_types: List of entity types to sync
        filter_criteria: Optional filter criteria
        status: Current status of the sync operation
        started_at: Timestamp when the sync operation started
        completed_at: Timestamp when the sync operation completed (if applicable)
        duration_seconds: Duration of the sync operation in seconds (if applicable)
        total_records: Total number of records to sync
        processed_records: Number of records processed so far
        succeeded_records: Number of records successfully synced
        failed_records: Number of records that failed to sync
        error_message: Error message if the sync operation failed
        progress_percent: Current progress percentage
    """
    
    def __init__(
        self,
        sync_id: Optional[str] = None,
        sync_type: SyncType = SyncType.FULL,
        source_system: str = '',
        target_system: str = '',
        entity_types: Optional[List[str]] = None,
        filter_criteria: Optional[Dict[str, Any]] = None,
        status: SyncStatus = SyncStatus.PENDING,
        started_at: Optional[datetime.datetime] = None,
        completed_at: Optional[datetime.datetime] = None,
        duration_seconds: Optional[float] = None,
        total_records: int = 0,
        processed_records: int = 0,
        succeeded_records: int = 0,
        failed_records: int = 0,
        error_message: Optional[str] = None,
        progress_percent: float = 0.0
    ):
        """Initialize a sync operation."""
        self.sync_id = sync_id or str(uuid.uuid4())
        self.sync_type = sync_type
        self.source_system = source_system
        self.target_system = target_system
        self.entity_types = entity_types or []
        self.filter_criteria = filter_criteria or {}
        self.status = status
        self.started_at = started_at or datetime.datetime.now()
        self.completed_at = completed_at
        self.duration_seconds = duration_seconds
        self.total_records = total_records
        self.processed_records = processed_records
        self.succeeded_records = succeeded_records
        self.failed_records = failed_records
        self.error_message = error_message
        self.progress_percent = progress_percent
    
    def start(self) -> None:
        """Mark the sync operation as started."""
        self.status = SyncStatus.RUNNING
        self.started_at = datetime.datetime.now()
        self.completed_at = None
        self.duration_seconds = None
        self.progress_percent = 0.0
    
    def complete(self) -> None:
        """Mark the sync operation as completed."""
        self.status = SyncStatus.COMPLETED
        self.completed_at = datetime.datetime.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        self.progress_percent = 100.0
    
    def fail(self, error_message: str) -> None:
        """
        Mark the sync operation as failed.
        
        Args:
            error_message: Error message describing the failure
        """
        self.status = SyncStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.datetime.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def cancel(self) -> None:
        """Mark the sync operation as canceled."""
        self.status = SyncStatus.CANCELED
        self.completed_at = datetime.datetime.now()
        self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def update_progress(self, processed_records: int, succeeded_records: int,
                       failed_records: int, total_records: Optional[int] = None) -> None:
        """
        Update the progress of the sync operation.
        
        Args:
            processed_records: Number of records processed so far
            succeeded_records: Number of records successfully synced
            failed_records: Number of records that failed to sync
            total_records: Optional update to the total number of records
        """
        self.processed_records = processed_records
        self.succeeded_records = succeeded_records
        self.failed_records = failed_records
        
        if total_records is not None:
            self.total_records = total_records
        
        if self.total_records > 0:
            self.progress_percent = (self.processed_records / self.total_records) * 100
        else:
            self.progress_percent = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sync operation to a dictionary.
        
        Returns:
            Dictionary representation of the sync operation
        """
        return {
            'sync_id': self.sync_id,
            'sync_type': self.sync_type,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'entity_types': self.entity_types,
            'filter_criteria': self.filter_criteria,
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'succeeded_records': self.succeeded_records,
            'failed_records': self.failed_records,
            'error_message': self.error_message,
            'progress_percent': self.progress_percent
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SyncOperation':
        """
        Create a sync operation from a dictionary.
        
        Args:
            data: Dictionary representation of the sync operation
            
        Returns:
            SyncOperation instance
        """
        # Convert string timestamps to datetime objects
        started_at = None
        if data.get('started_at'):
            started_at = datetime.datetime.fromisoformat(data['started_at'])
        
        completed_at = None
        if data.get('completed_at'):
            completed_at = datetime.datetime.fromisoformat(data['completed_at'])
        
        # Convert string enum values to enum objects
        sync_type = data.get('sync_type')
        if isinstance(sync_type, str):
            sync_type = SyncType(sync_type)
        
        status = data.get('status')
        if isinstance(status, str):
            status = SyncStatus(status)
        
        return cls(
            sync_id=data.get('sync_id'),
            sync_type=sync_type,
            source_system=data.get('source_system', ''),
            target_system=data.get('target_system', ''),
            entity_types=data.get('entity_types', []),
            filter_criteria=data.get('filter_criteria', {}),
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=data.get('duration_seconds'),
            total_records=data.get('total_records', 0),
            processed_records=data.get('processed_records', 0),
            succeeded_records=data.get('succeeded_records', 0),
            failed_records=data.get('failed_records', 0),
            error_message=data.get('error_message'),
            progress_percent=data.get('progress_percent', 0.0)
        )


# Sync operations storage
_sync_operations: Dict[str, SyncOperation] = {}


def create_sync_operation(
    sync_type: SyncType,
    source_system: str,
    target_system: str,
    entity_types: List[str],
    filter_criteria: Optional[Dict[str, Any]] = None,
    total_records: int = 0
) -> SyncOperation:
    """
    Create a new sync operation.
    
    Args:
        sync_type: Type of sync operation
        source_system: Source system name
        target_system: Target system name
        entity_types: List of entity types to sync
        filter_criteria: Optional filter criteria
        total_records: Initial estimate of total records to sync
        
    Returns:
        Newly created SyncOperation
    """
    with _sync_tracker_lock:
        sync_op = SyncOperation(
            sync_type=sync_type,
            source_system=source_system,
            target_system=target_system,
            entity_types=entity_types,
            filter_criteria=filter_criteria,
            total_records=total_records,
            status=SyncStatus.PENDING
        )
        
        _sync_operations[sync_op.sync_id] = sync_op
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def start_sync_operation(sync_id: str) -> Optional[SyncOperation]:
    """
    Start a sync operation.
    
    Args:
        sync_id: ID of the sync operation to start
        
    Returns:
        Updated SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        if sync_id not in _sync_operations:
            return None
        
        sync_op = _sync_operations[sync_id]
        sync_op.start()
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def complete_sync_operation(sync_id: str) -> Optional[SyncOperation]:
    """
    Mark a sync operation as completed.
    
    Args:
        sync_id: ID of the sync operation to complete
        
    Returns:
        Updated SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        if sync_id not in _sync_operations:
            return None
        
        sync_op = _sync_operations[sync_id]
        sync_op.complete()
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def fail_sync_operation(sync_id: str, error_message: str) -> Optional[SyncOperation]:
    """
    Mark a sync operation as failed.
    
    Args:
        sync_id: ID of the sync operation to fail
        error_message: Error message describing the failure
        
    Returns:
        Updated SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        if sync_id not in _sync_operations:
            return None
        
        sync_op = _sync_operations[sync_id]
        sync_op.fail(error_message)
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def cancel_sync_operation(sync_id: str) -> Optional[SyncOperation]:
    """
    Mark a sync operation as canceled.
    
    Args:
        sync_id: ID of the sync operation to cancel
        
    Returns:
        Updated SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        if sync_id not in _sync_operations:
            return None
        
        sync_op = _sync_operations[sync_id]
        sync_op.cancel()
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def update_sync_progress(
    sync_id: str,
    processed_records: int,
    succeeded_records: int,
    failed_records: int,
    total_records: Optional[int] = None
) -> Optional[SyncOperation]:
    """
    Update the progress of a sync operation.
    
    Args:
        sync_id: ID of the sync operation to update
        processed_records: Number of records processed so far
        succeeded_records: Number of records successfully synced
        failed_records: Number of records that failed to sync
        total_records: Optional update to the total number of records
        
    Returns:
        Updated SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        if sync_id not in _sync_operations:
            return None
        
        sync_op = _sync_operations[sync_id]
        sync_op.update_progress(
            processed_records=processed_records,
            succeeded_records=succeeded_records,
            failed_records=failed_records,
            total_records=total_records
        )
        
        # Save to disk
        save_sync_operation(sync_op)
        
        return sync_op


def get_sync_operation(sync_id: str) -> Optional[SyncOperation]:
    """
    Get a sync operation by ID.
    
    Args:
        sync_id: ID of the sync operation to get
        
    Returns:
        SyncOperation or None if not found
    """
    with _sync_tracker_lock:
        return _sync_operations.get(sync_id)


def get_all_sync_operations() -> List[SyncOperation]:
    """
    Get all sync operations.
    
    Returns:
        List of all SyncOperation instances
    """
    with _sync_tracker_lock:
        return list(_sync_operations.values())


def get_active_sync_operations() -> List[SyncOperation]:
    """
    Get active (running) sync operations.
    
    Returns:
        List of active SyncOperation instances
    """
    with _sync_tracker_lock:
        return [
            op for op in _sync_operations.values()
            if op.status == SyncStatus.RUNNING
        ]


def get_failed_sync_operations() -> List[SyncOperation]:
    """
    Get failed sync operations.
    
    Returns:
        List of failed SyncOperation instances
    """
    with _sync_tracker_lock:
        return [
            op for op in _sync_operations.values()
            if op.status == SyncStatus.FAILED
        ]


def get_recent_sync_operations(
    limit: int = 10,
    offset: int = 0,
    sync_type: Optional[SyncType] = None,
    source_system: Optional[str] = None,
    target_system: Optional[str] = None,
    status: Optional[SyncStatus] = None
) -> List[SyncOperation]:
    """
    Get recent sync operations with optional filtering.
    
    Args:
        limit: Maximum number of sync operations to return
        offset: Number of sync operations to skip
        sync_type: Filter by sync type
        source_system: Filter by source system
        target_system: Filter by target system
        status: Filter by status
        
    Returns:
        List of SyncOperation instances matching the filters
    """
    with _sync_tracker_lock:
        # Filter sync operations
        filtered_ops = _sync_operations.values()
        
        if sync_type:
            filtered_ops = [op for op in filtered_ops if op.sync_type == sync_type]
        
        if source_system:
            filtered_ops = [op for op in filtered_ops if op.source_system == source_system]
        
        if target_system:
            filtered_ops = [op for op in filtered_ops if op.target_system == target_system]
        
        if status:
            filtered_ops = [op for op in filtered_ops if op.status == status]
        
        # Sort by started_at (newest first)
        sorted_ops = sorted(
            filtered_ops,
            key=lambda op: op.started_at if op.started_at else datetime.datetime.min,
            reverse=True
        )
        
        # Apply pagination
        return sorted_ops[offset:offset + limit]


def get_sync_summary() -> Dict[str, Any]:
    """
    Get a summary of sync operations.
    
    Returns:
        Dictionary with sync status summary information
    """
    with _sync_tracker_lock:
        all_ops = list(_sync_operations.values())
        active_ops = get_active_sync_operations()
        failed_ops = get_failed_sync_operations()
        
        # Count sync operations by status
        status_counts = {}
        for status in SyncStatus:
            status_counts[status] = len([op for op in all_ops if op.status == status])
        
        # Calculate overall success rate
        completed_ops = [op for op in all_ops if op.status == SyncStatus.COMPLETED]
        total_completed_or_failed = len(completed_ops) + len(failed_ops)
        success_rate = 0.0
        if total_completed_or_failed > 0:
            success_rate = (len(completed_ops) / total_completed_or_failed) * 100
        
        # Get recently completed sync operations
        recently_completed = [
            op.to_dict() for op in get_recent_sync_operations(
                limit=5,
                status=SyncStatus.COMPLETED
            )
        ]
        
        # Get recently failed sync operations
        recently_failed = [
            op.to_dict() for op in get_recent_sync_operations(
                limit=5,
                status=SyncStatus.FAILED
            )
        ]
        
        return {
            'status_counts': status_counts,
            'total_syncs': len(all_ops),
            'active_syncs': [op.to_dict() for op in active_ops],
            'recently_completed': recently_completed,
            'recently_failed': recently_failed,
            'success_rate': round(success_rate, 2)
        }


def get_entity_type_summary() -> Dict[str, Dict[str, Any]]:
    """
    Get a summary of sync operations by entity type.
    
    Returns:
        Dictionary mapping entity type to summary metrics
    """
    with _sync_tracker_lock:
        # Collect all entity types
        entity_types = set()
        for op in _sync_operations.values():
            entity_types.update(op.entity_types)
        
        # Initialize entity type metrics
        entity_metrics = {}
        for entity_type in entity_types:
            entity_metrics[entity_type] = {
                'total_records': 0,
                'succeeded_records': 0,
                'failed_records': 0,
                'success_rate': 0.0
            }
        
        # Aggregate metrics by entity type
        for op in _sync_operations.values():
            if op.status not in (SyncStatus.COMPLETED, SyncStatus.FAILED):
                continue
            
            # Distribute records evenly across entity types
            if not op.entity_types:
                continue
            
            entity_count = len(op.entity_types)
            for entity_type in op.entity_types:
                # Add entity's share of records
                entity_metrics[entity_type]['total_records'] += op.total_records // entity_count
                entity_metrics[entity_type]['succeeded_records'] += op.succeeded_records // entity_count
                entity_metrics[entity_type]['failed_records'] += op.failed_records // entity_count
        
        # Calculate success rate for each entity type
        for entity_type, metrics in entity_metrics.items():
            total = metrics['succeeded_records'] + metrics['failed_records']
            if total > 0:
                metrics['success_rate'] = round((metrics['succeeded_records'] / total) * 100, 2)
        
        return entity_metrics


def save_sync_operation(sync_op: SyncOperation) -> None:
    """
    Save a sync operation to disk.
    
    Args:
        sync_op: SyncOperation to save
    """
    try:
        sync_file = os.path.join(SYNC_STATUS_DIR, f"{sync_op.sync_id}.json")
        
        with open(sync_file, 'w') as f:
            json.dump(sync_op.to_dict(), f, indent=2)
            
        logger.debug(f"Sync operation {sync_op.sync_id} saved to {sync_file}")
    except Exception as e:
        logger.error(f"Error saving sync operation {sync_op.sync_id} to disk: {str(e)}")


def load_sync_operations_from_disk() -> None:
    """Load all sync operations from disk."""
    global _sync_operations
    
    try:
        # Clear existing sync operations
        with _sync_tracker_lock:
            _sync_operations.clear()
        
        # Load each sync operation file
        for filename in os.listdir(SYNC_STATUS_DIR):
            if not filename.endswith('.json'):
                continue
            
            sync_file = os.path.join(SYNC_STATUS_DIR, filename)
            
            try:
                with open(sync_file, 'r') as f:
                    sync_data = json.load(f)
                
                sync_op = SyncOperation.from_dict(sync_data)
                
                with _sync_tracker_lock:
                    _sync_operations[sync_op.sync_id] = sync_op
                
                logger.debug(f"Loaded sync operation {sync_op.sync_id} from {sync_file}")
            except Exception as e:
                logger.error(f"Error loading sync operation from {sync_file}: {str(e)}")
        
        logger.info(f"Loaded {len(_sync_operations)} sync operations from disk")
    except Exception as e:
        logger.error(f"Error loading sync operations from disk: {str(e)}")


# Initialize by loading sync operations from disk
load_sync_operations_from_disk()