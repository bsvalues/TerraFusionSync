"""
Monitoring module for SyncService.

This module provides utilities for monitoring and tracking the SyncService
operations, including system metrics, sync status, and performance analytics.
"""

from syncservice.monitoring.metrics import (
    create_counter, increment_counter, get_counter_value,
    create_gauge, update_gauge, get_gauge_value,
    create_histogram, observe_histogram, get_histogram_buckets,
    get_metrics_as_dict, save_metrics_to_disk, load_metrics_from_disk
)

from syncservice.monitoring.sync_tracker import (
    SyncStatus, SyncType, SyncOperation,
    create_sync_operation, start_sync_operation, complete_sync_operation,
    fail_sync_operation, cancel_sync_operation, update_sync_progress,
    get_sync_operation, get_all_sync_operations, get_active_sync_operations,
    get_failed_sync_operations, get_recent_sync_operations,
    get_sync_summary, get_entity_type_summary,
    save_sync_operation, load_sync_operations_from_disk
)

from syncservice.monitoring.system_monitoring import (
    get_system_metrics, update_system_metrics,
    start_monitoring, stop_monitoring, is_monitoring_active
)

__all__ = [
    # Metrics
    'create_counter', 'increment_counter', 'get_counter_value',
    'create_gauge', 'update_gauge', 'get_gauge_value',
    'create_histogram', 'observe_histogram', 'get_histogram_buckets',
    'get_metrics_as_dict', 'save_metrics_to_disk', 'load_metrics_from_disk',
    
    # Sync tracker
    'SyncStatus', 'SyncType', 'SyncOperation',
    'create_sync_operation', 'start_sync_operation', 'complete_sync_operation',
    'fail_sync_operation', 'cancel_sync_operation', 'update_sync_progress',
    'get_sync_operation', 'get_all_sync_operations', 'get_active_sync_operations',
    'get_failed_sync_operations', 'get_recent_sync_operations',
    'get_sync_summary', 'get_entity_type_summary',
    'save_sync_operation', 'load_sync_operations_from_disk',
    
    # System monitoring
    'get_system_metrics', 'update_system_metrics',
    'start_monitoring', 'stop_monitoring', 'is_monitoring_active'
]