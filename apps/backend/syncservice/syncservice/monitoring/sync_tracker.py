"""
Sync operation tracking for SyncService.

This module provides utilities for tracking and reporting on sync operations,
including status, progress, and performance metrics.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import threading
import uuid

from syncservice.monitoring.metrics import create_counter, create_gauge, create_histogram, MetricTimer

logger = logging.getLogger(__name__)

# Directory for storing sync status data
_sync_status_dir = 'data/sync_status'

# Lock for thread-safe status updates
_status_lock = threading.Lock()

# In-memory storage for recent sync operations
_recent_syncs = {}

# Maximum number of recent sync operations to store in memory
MAX_RECENT_SYNCS = 100

# Default retention period for sync status records (in days)
DEFAULT_RETENTION_DAYS = 30


class SyncStatus(str, Enum):
    """Enum representing sync operation status."""
    
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


class SyncType(str, Enum):
    """Enum representing sync operation type."""
    
    FULL = 'full'
    INCREMENTAL = 'incremental'
    DELTA = 'delta'
    VALIDATION = 'validation'


class SyncOperation:
    """Class representing a sync operation."""
    
    def __init__(
        self,
        sync_id: str,
        sync_type: SyncType,
        source_system: str,
        target_system: str,
        entity_types: Optional[List[str]] = None,
        initiated_by: Optional[str] = None,
        batch_size: Optional[int] = None,
        description: Optional[str] = None
    ):
        """
        Initialize a sync operation.
        
        Args:
            sync_id: Unique identifier for this sync operation
            sync_type: Type of sync operation
            source_system: Source system ID
            target_system: Target system ID
            entity_types: List of entity types to sync
            initiated_by: User or system that initiated the sync
            batch_size: Batch size for processing records
            description: Description of the sync operation
        """
        self.sync_id = sync_id
        self.sync_type = sync_type
        self.source_system = source_system
        self.target_system = target_system
        self.entity_types = entity_types or []
        self.initiated_by = initiated_by
        self.batch_size = batch_size
        self.description = description
        
        # Status information
        self.status = SyncStatus.PENDING
        self.status_message = 'Sync operation created'
        self.error_message = None
        
        # Timing information
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
        
        # Progress information
        self.progress_percent = 0
        self.total_records = 0
        self.processed_records = 0
        self.succeeded_records = 0
        self.failed_records = 0
        
        # Entity-specific progress
        self.entity_progress = {}
        
        # Detailed error information
        self.errors = []
    
    def start(self) -> None:
        """Mark the sync operation as started."""
        with _status_lock:
            self.status = SyncStatus.RUNNING
            self.status_message = 'Sync operation in progress'
            self.started_at = datetime.utcnow()
            self._update_metrics()
    
    def complete(self) -> None:
        """Mark the sync operation as completed."""
        with _status_lock:
            self.status = SyncStatus.COMPLETED
            self.status_message = 'Sync operation completed'
            self.completed_at = datetime.utcnow()
            self.progress_percent = 100
            self._update_metrics()
            
            # Record duration in histogram
            if self.started_at:
                duration = (self.completed_at - self.started_at).total_seconds()
                histogram = create_histogram(
                    'sync_duration_seconds',
                    'Duration of sync operations in seconds',
                    [0.01, 0.1, 0.5, 1, 5, 10, 30, 60, 300, 600, 1800, 3600],
                    ['operation_type', 'source_system', 'target_system']
                )
                histogram.observe(
                    duration,
                    operation_type=self.sync_type,
                    source_system=self.source_system,
                    target_system=self.target_system
                )
    
    def fail(self, error_message: str) -> None:
        """
        Mark the sync operation as failed.
        
        Args:
            error_message: Error message explaining the failure
        """
        with _status_lock:
            self.status = SyncStatus.FAILED
            self.status_message = 'Sync operation failed'
            self.error_message = error_message
            self.completed_at = datetime.utcnow()
            self._update_metrics()
            
            # Record error in counter
            counter = create_counter(
                'sync_failures_total',
                'Total number of sync failures',
                ['operation_type', 'source_system', 'target_system']
            )
            counter.inc(
                1,
                operation_type=self.sync_type,
                source_system=self.source_system,
                target_system=self.target_system
            )
    
    def cancel(self) -> None:
        """Mark the sync operation as cancelled."""
        with _status_lock:
            self.status = SyncStatus.CANCELLED
            self.status_message = 'Sync operation cancelled'
            self.completed_at = datetime.utcnow()
            self._update_metrics()
    
    def update_progress(
        self,
        processed: Optional[int] = None,
        succeeded: Optional[int] = None,
        failed: Optional[int] = None,
        total: Optional[int] = None,
        entity_type: Optional[str] = None
    ) -> None:
        """
        Update the progress of the sync operation.
        
        Args:
            processed: Number of records processed
            succeeded: Number of records successfully processed
            failed: Number of records that failed processing
            total: Total number of records to process
            entity_type: Entity type being processed
        """
        with _status_lock:
            if total is not None:
                self.total_records = total
            
            if processed is not None:
                self.processed_records += processed
            
            if succeeded is not None:
                self.succeeded_records += succeeded
            
            if failed is not None:
                self.failed_records += failed
            
            # Update entity-specific progress
            if entity_type is not None:
                if entity_type not in self.entity_progress:
                    self.entity_progress[entity_type] = {
                        'total': 0,
                        'processed': 0,
                        'succeeded': 0,
                        'failed': 0
                    }
                
                entity_progress = self.entity_progress[entity_type]
                
                if total is not None:
                    entity_progress['total'] = total
                
                if processed is not None:
                    entity_progress['processed'] += processed
                
                if succeeded is not None:
                    entity_progress['succeeded'] += succeeded
                
                if failed is not None:
                    entity_progress['failed'] += failed
            
            # Calculate overall progress percentage
            if self.total_records > 0:
                self.progress_percent = min(
                    int((self.processed_records / self.total_records) * 100),
                    99  # Cap at 99% until explicitly completed
                )
            
            self._update_metrics()
    
    def add_error(self, error_message: str, entity_type: Optional[str] = None, record_id: Optional[str] = None) -> None:
        """
        Add an error to the sync operation.
        
        Args:
            error_message: Error message
            entity_type: Entity type that encountered the error
            record_id: ID of the record that encountered the error
        """
        with _status_lock:
            error = {
                'timestamp': datetime.utcnow().isoformat(),
                'message': error_message
            }
            
            if entity_type:
                error['entity_type'] = entity_type
            
            if record_id:
                error['record_id'] = record_id
            
            self.errors.append(error)
            
            # Update failed record counter
            if entity_type:
                counter = create_counter(
                    'records_failed_total',
                    'Total number of records that failed processing',
                    ['operation_type', 'source_system', 'target_system', 'entity_type']
                )
                counter.inc(
                    1,
                    operation_type=self.sync_type,
                    source_system=self.source_system,
                    target_system=self.target_system,
                    entity_type=entity_type
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the sync operation to a dictionary.
        
        Returns:
            Dictionary representation of the sync operation
        """
        with _status_lock:
            return {
                'sync_id': self.sync_id,
                'sync_type': self.sync_type,
                'source_system': self.source_system,
                'target_system': self.target_system,
                'entity_types': self.entity_types,
                'initiated_by': self.initiated_by,
                'batch_size': self.batch_size,
                'description': self.description,
                'status': self.status,
                'status_message': self.status_message,
                'error_message': self.error_message,
                'created_at': self.created_at.isoformat(),
                'started_at': self.started_at.isoformat() if self.started_at else None,
                'completed_at': self.completed_at.isoformat() if self.completed_at else None,
                'duration_seconds': (self.completed_at - self.started_at).total_seconds() if self.completed_at and self.started_at else None,
                'progress_percent': self.progress_percent,
                'total_records': self.total_records,
                'processed_records': self.processed_records,
                'succeeded_records': self.succeeded_records,
                'failed_records': self.failed_records,
                'entity_progress': self.entity_progress,
                'errors': self.errors[:10]  # Limit to first 10 errors
            }
    
    def _update_metrics(self) -> None:
        """Update metrics for this sync operation."""
        # Update sync operations counter
        counter = create_counter(
            'sync_operations_total',
            'Total number of sync operations',
            ['operation_type', 'source_system', 'target_system', 'status']
        )
        counter.inc(
            0,  # Don't increment, just ensure it exists
            operation_type=self.sync_type,
            source_system=self.source_system,
            target_system=self.target_system,
            status=self.status
        )
        
        # Update active syncs gauge
        gauge = create_gauge(
            'active_syncs',
            'Number of active sync operations',
            ['operation_type', 'source_system', 'target_system']
        )
        
        if self.status == SyncStatus.RUNNING:
            gauge.inc(
                0,  # Don't increment, just ensure it exists
                operation_type=self.sync_type,
                source_system=self.source_system,
                target_system=self.target_system
            )
        
        # Update records processed counter
        counter = create_counter(
            'records_processed_total',
            'Total number of records processed',
            ['operation_type', 'source_system', 'target_system']
        )
        counter.inc(
            0,  # Don't increment, just ensure it exists
            operation_type=self.sync_type,
            source_system=self.source_system,
            target_system=self.target_system
        )
        
        # Update records succeeded counter
        counter = create_counter(
            'records_succeeded_total',
            'Total number of records successfully processed',
            ['operation_type', 'source_system', 'target_system']
        )
        counter.inc(
            0,  # Don't increment, just ensure it exists
            operation_type=self.sync_type,
            source_system=self.source_system,
            target_system=self.target_system
        )


def create_sync_operation(
    sync_type: SyncType,
    source_system: str,
    target_system: str,
    entity_types: Optional[List[str]] = None,
    initiated_by: Optional[str] = None,
    batch_size: Optional[int] = None,
    description: Optional[str] = None
) -> SyncOperation:
    """
    Create a new sync operation.
    
    Args:
        sync_type: Type of sync operation
        source_system: Source system ID
        target_system: Target system ID
        entity_types: List of entity types to sync
        initiated_by: User or system that initiated the sync
        batch_size: Batch size for processing records
        description: Description of the sync operation
        
    Returns:
        Newly created sync operation
    """
    # Generate a unique ID
    sync_id = str(uuid.uuid4())
    
    # Create sync operation
    sync_op = SyncOperation(
        sync_id=sync_id,
        sync_type=sync_type,
        source_system=source_system,
        target_system=target_system,
        entity_types=entity_types,
        initiated_by=initiated_by,
        batch_size=batch_size,
        description=description
    )
    
    # Store in memory
    with _status_lock:
        _recent_syncs[sync_id] = sync_op
        
        # Remove oldest syncs if we're over the limit
        if len(_recent_syncs) > MAX_RECENT_SYNCS:
            oldest_sync_id = min(
                _recent_syncs.keys(),
                key=lambda k: _recent_syncs[k].created_at
            )
            del _recent_syncs[oldest_sync_id]
    
    # Store to disk
    store_sync_status(sync_op)
    
    # Increment sync operations counter
    counter = create_counter(
        'sync_operations_total',
        'Total number of sync operations',
        ['operation_type', 'source_system', 'target_system', 'status']
    )
    counter.inc(
        1,
        operation_type=sync_type,
        source_system=source_system,
        target_system=target_system,
        status=SyncStatus.PENDING
    )
    
    return sync_op


def get_sync_operation(sync_id: str) -> Optional[SyncOperation]:
    """
    Get a sync operation by ID.
    
    Args:
        sync_id: ID of the sync operation
        
    Returns:
        Sync operation if found, None otherwise
    """
    with _status_lock:
        if sync_id in _recent_syncs:
            return _recent_syncs[sync_id]
    
    # Try to load from disk
    sync_op = load_sync_status(sync_id)
    
    if sync_op:
        # Add to recent syncs
        with _status_lock:
            _recent_syncs[sync_id] = sync_op
            
            # Remove oldest syncs if we're over the limit
            if len(_recent_syncs) > MAX_RECENT_SYNCS:
                oldest_sync_id = min(
                    _recent_syncs.keys(),
                    key=lambda k: _recent_syncs[k].created_at
                )
                del _recent_syncs[oldest_sync_id]
    
    return sync_op


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
        List of sync operations matching the filters
    """
    with _status_lock:
        # Apply filters
        filtered_syncs = []
        for sync_op in _recent_syncs.values():
            if sync_type and sync_op.sync_type != sync_type:
                continue
            
            if source_system and sync_op.source_system != source_system:
                continue
            
            if target_system and sync_op.target_system != target_system:
                continue
            
            if status and sync_op.status != status:
                continue
            
            filtered_syncs.append(sync_op)
        
        # Sort by created_at (newest first)
        filtered_syncs.sort(key=lambda s: s.created_at, reverse=True)
        
        # Apply offset and limit
        return filtered_syncs[offset:offset + limit]


def get_active_sync_operations() -> List[SyncOperation]:
    """
    Get active (running) sync operations.
    
    Returns:
        List of active sync operations
    """
    return get_recent_sync_operations(status=SyncStatus.RUNNING)


def get_failed_sync_operations(limit: int = 10) -> List[SyncOperation]:
    """
    Get recent failed sync operations.
    
    Args:
        limit: Maximum number of sync operations to return
        
    Returns:
        List of failed sync operations
    """
    return get_recent_sync_operations(status=SyncStatus.FAILED, limit=limit)


def store_sync_status(sync_op: SyncOperation) -> None:
    """
    Store sync operation status to disk.
    
    Args:
        sync_op: Sync operation to store
    """
    # Create directory if it doesn't exist
    os.makedirs(_sync_status_dir, exist_ok=True)
    
    # Serialize to JSON
    sync_dict = sync_op.to_dict()
    sync_json = json.dumps(sync_dict, indent=2)
    
    # Write to file
    file_path = os.path.join(_sync_status_dir, f'{sync_op.sync_id}.json')
    with open(file_path, 'w') as f:
        f.write(sync_json)
    
    logger.debug(f"Sync status stored to {file_path}")


def load_sync_status(sync_id: str) -> Optional[SyncOperation]:
    """
    Load sync operation status from disk.
    
    Args:
        sync_id: ID of the sync operation
        
    Returns:
        Sync operation if found, None otherwise
    """
    file_path = os.path.join(_sync_status_dir, f'{sync_id}.json')
    
    if not os.path.exists(file_path):
        return None
    
    try:
        # Load from file
        with open(file_path, 'r') as f:
            sync_dict = json.loads(f.read())
        
        # Create sync operation
        sync_op = SyncOperation(
            sync_id=sync_dict['sync_id'],
            sync_type=sync_dict['sync_type'],
            source_system=sync_dict['source_system'],
            target_system=sync_dict['target_system'],
            entity_types=sync_dict.get('entity_types', []),
            initiated_by=sync_dict.get('initiated_by'),
            batch_size=sync_dict.get('batch_size'),
            description=sync_dict.get('description')
        )
        
        # Set status information
        sync_op.status = sync_dict['status']
        sync_op.status_message = sync_dict.get('status_message', '')
        sync_op.error_message = sync_dict.get('error_message')
        
        # Set timing information
        sync_op.created_at = datetime.fromisoformat(sync_dict['created_at'])
        
        if sync_dict.get('started_at'):
            sync_op.started_at = datetime.fromisoformat(sync_dict['started_at'])
        
        if sync_dict.get('completed_at'):
            sync_op.completed_at = datetime.fromisoformat(sync_dict['completed_at'])
        
        # Set progress information
        sync_op.progress_percent = sync_dict.get('progress_percent', 0)
        sync_op.total_records = sync_dict.get('total_records', 0)
        sync_op.processed_records = sync_dict.get('processed_records', 0)
        sync_op.succeeded_records = sync_dict.get('succeeded_records', 0)
        sync_op.failed_records = sync_dict.get('failed_records', 0)
        
        # Set entity progress
        sync_op.entity_progress = sync_dict.get('entity_progress', {})
        
        # Set errors
        sync_op.errors = sync_dict.get('errors', [])
        
        return sync_op
    except Exception as e:
        logger.error(f"Failed to load sync status from {file_path}: {str(e)}")
        return None


def load_recent_sync_operations(limit: int = MAX_RECENT_SYNCS) -> None:
    """
    Load recent sync operations from disk.
    
    Args:
        limit: Maximum number of sync operations to load
    """
    if not os.path.exists(_sync_status_dir):
        return
    
    # Get all status files
    status_files = []
    for filename in os.listdir(_sync_status_dir):
        if not filename.endswith('.json'):
            continue
        
        file_path = os.path.join(_sync_status_dir, filename)
        mtime = os.path.getmtime(file_path)
        
        status_files.append((file_path, mtime))
    
    # Sort by modification time (newest first)
    status_files.sort(key=lambda x: x[1], reverse=True)
    
    # Load the most recent ones
    for file_path, _ in status_files[:limit]:
        try:
            sync_id = os.path.basename(file_path).replace('.json', '')
            sync_op = load_sync_status(sync_id)
            
            if sync_op:
                with _status_lock:
                    _recent_syncs[sync_op.sync_id] = sync_op
        except Exception as e:
            logger.error(f"Failed to load sync operation from {file_path}: {str(e)}")


def cleanup_old_sync_status(retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    """
    Clean up old sync status files.
    
    Args:
        retention_days: Number of days to retain sync status files
    """
    if not os.path.exists(_sync_status_dir):
        return
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Delete old files
    for filename in os.listdir(_sync_status_dir):
        if not filename.endswith('.json'):
            continue
        
        file_path = os.path.join(_sync_status_dir, filename)
        mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if mtime < cutoff_date:
            try:
                os.remove(file_path)
                logger.debug(f"Deleted old sync status file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete old sync status file {file_path}: {str(e)}")


def get_sync_summary() -> Dict[str, Any]:
    """
    Get a summary of recent sync operations.
    
    Returns:
        Dictionary containing sync summary information
    """
    with _status_lock:
        # Count operations by status
        status_counts = {status.value: 0 for status in SyncStatus}
        for sync_op in _recent_syncs.values():
            status_counts[sync_op.status] += 1
        
        # Get active syncs
        active_syncs = [
            sync_op.to_dict()
            for sync_op in _recent_syncs.values()
            if sync_op.status == SyncStatus.RUNNING
        ]
        
        # Get recently completed syncs
        completed_syncs = [
            sync_op.to_dict()
            for sync_op in sorted(
                [s for s in _recent_syncs.values() if s.status == SyncStatus.COMPLETED],
                key=lambda s: s.completed_at or datetime.min,
                reverse=True
            )[:5]
        ]
        
        # Get recently failed syncs
        failed_syncs = [
            sync_op.to_dict()
            for sync_op in sorted(
                [s for s in _recent_syncs.values() if s.status == SyncStatus.FAILED],
                key=lambda s: s.completed_at or datetime.min,
                reverse=True
            )[:5]
        ]
        
        # Calculate success rate
        total_syncs = sum(
            1 for s in _recent_syncs.values()
            if s.status in (SyncStatus.COMPLETED, SyncStatus.FAILED)
        )
        
        success_rate = (
            (status_counts[SyncStatus.COMPLETED] / total_syncs) * 100
            if total_syncs > 0 else 0
        )
        
        return {
            'status_counts': status_counts,
            'total_syncs': len(_recent_syncs),
            'active_syncs': active_syncs,
            'recently_completed': completed_syncs,
            'recently_failed': failed_syncs,
            'success_rate': round(success_rate, 2)
        }


def get_entity_type_summary() -> Dict[str, Dict[str, Any]]:
    """
    Get a summary of metrics by entity type.
    
    Returns:
        Dictionary mapping entity types to summary information
    """
    with _status_lock:
        entity_types: Set[str] = set()
        
        # Collect all entity types
        for sync_op in _recent_syncs.values():
            entity_types.update(sync_op.entity_progress.keys())
        
        # Build summary by entity type
        entity_summary = {}
        
        for entity_type in entity_types:
            total_records = 0
            succeeded_records = 0
            failed_records = 0
            
            # Collect metrics across all sync operations
            for sync_op in _recent_syncs.values():
                if entity_type in sync_op.entity_progress:
                    progress = sync_op.entity_progress[entity_type]
                    total_records += progress.get('total', 0)
                    succeeded_records += progress.get('succeeded', 0)
                    failed_records += progress.get('failed', 0)
            
            # Calculate success rate
            processed_records = succeeded_records + failed_records
            success_rate = (
                (succeeded_records / processed_records) * 100
                if processed_records > 0 else 0
            )
            
            entity_summary[entity_type] = {
                'total_records': total_records,
                'succeeded_records': succeeded_records,
                'failed_records': failed_records,
                'success_rate': round(success_rate, 2)
            }
        
        return entity_summary


# Load recent sync operations on module import
try:
    load_recent_sync_operations()
except Exception as e:
    logger.error(f"Failed to load recent sync operations: {str(e)}")