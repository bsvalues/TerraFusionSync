"""
Dashboard API endpoints for the SyncService.

This module provides API endpoints for the monitoring dashboard, exposing metrics,
sync status, and system resource information.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Path, HTTPException
from pydantic import BaseModel

from syncservice.monitoring.metrics import (
    get_metrics_as_dict,
    create_counter,
    create_gauge,
    create_histogram
)
from syncservice.monitoring.sync_tracker import (
    get_sync_operation,
    get_recent_sync_operations,
    get_active_sync_operations,
    get_failed_sync_operations,
    get_sync_summary,
    get_entity_type_summary,
    SyncStatus,
    SyncType
)
from syncservice.monitoring.system_monitoring import (
    get_system_metrics,
    is_monitoring_active,
    start_monitoring,
    stop_monitoring
)

logger = logging.getLogger(__name__)

# Configure router
router = APIRouter()


class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""
    
    cpu: Dict[str, float]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    process: Dict[str, Any]
    network: Dict[str, Any]
    monitoring_active: bool


class SyncMetricsResponse(BaseModel):
    """Response model for sync metrics."""
    
    operations_count: Dict[str, int]
    success_rate: float
    records_processed: int
    records_succeeded: int
    records_failed: int
    average_duration: float
    entity_metrics: Dict[str, Dict[str, Any]]


class SyncStatusSummaryResponse(BaseModel):
    """Response model for sync status summary."""
    
    status_counts: Dict[str, int]
    total_syncs: int
    active_syncs: List[Dict[str, Any]]
    recently_completed: List[Dict[str, Any]]
    recently_failed: List[Dict[str, Any]]
    success_rate: float


class DashboardSummaryResponse(BaseModel):
    """Response model for dashboard summary."""
    
    system_metrics: SystemMetricsResponse
    sync_metrics: SyncMetricsResponse
    sync_status: SyncStatusSummaryResponse


@router.get("/system", response_model=SystemMetricsResponse)
async def get_dashboard_system_metrics() -> Dict[str, Any]:
    """
    Get system metrics for the dashboard.
    
    Returns:
        System metrics
    """
    # Get system metrics
    metrics = get_system_metrics()
    
    # Organize metrics by category
    cpu_metrics = {
        'usage_percent': metrics.get('cpu_percent', 0),
        'user_percent': metrics.get('cpu_user_percent', 0),
        'system_percent': metrics.get('cpu_system_percent', 0),
        'idle_percent': metrics.get('cpu_idle_percent', 0)
    }
    
    memory_metrics = {
        'total_bytes': metrics.get('memory_total_bytes', 0),
        'available_bytes': metrics.get('memory_available_bytes', 0),
        'used_bytes': metrics.get('memory_used_bytes', 0),
        'usage_percent': metrics.get('memory_percent', 0),
        'total_gb': round(metrics.get('memory_total_bytes', 0) / (1024 ** 3), 2),
        'available_gb': round(metrics.get('memory_available_bytes', 0) / (1024 ** 3), 2),
        'used_gb': round(metrics.get('memory_used_bytes', 0) / (1024 ** 3), 2)
    }
    
    disk_metrics = {
        'total_bytes': metrics.get('disk_total_bytes', 0),
        'used_bytes': metrics.get('disk_used_bytes', 0),
        'free_bytes': metrics.get('disk_free_bytes', 0),
        'usage_percent': metrics.get('disk_percent', 0),
        'total_gb': round(metrics.get('disk_total_bytes', 0) / (1024 ** 3), 2),
        'used_gb': round(metrics.get('disk_used_bytes', 0) / (1024 ** 3), 2),
        'free_gb': round(metrics.get('disk_free_bytes', 0) / (1024 ** 3), 2)
    }
    
    process_metrics = {
        'cpu_percent': metrics.get('process_cpu_percent', 0),
        'memory_rss_bytes': metrics.get('process_memory_rss_bytes', 0),
        'memory_vms_bytes': metrics.get('process_memory_vms_bytes', 0),
        'memory_rss_mb': round(metrics.get('process_memory_rss_bytes', 0) / (1024 ** 2), 2),
        'memory_vms_mb': round(metrics.get('process_memory_vms_bytes', 0) / (1024 ** 2), 2),
        'threads': metrics.get('process_threads', 0),
        'open_files': metrics.get('process_open_files', 0),
        'connections': metrics.get('process_connections', 0)
    }
    
    network_metrics = {
        'bytes_sent': metrics.get('network_bytes_sent', 0),
        'bytes_recv': metrics.get('network_bytes_recv', 0),
        'packets_sent': metrics.get('network_packets_sent', 0),
        'packets_recv': metrics.get('network_packets_recv', 0),
        'mb_sent': round(metrics.get('network_bytes_sent', 0) / (1024 ** 2), 2),
        'mb_recv': round(metrics.get('network_bytes_recv', 0) / (1024 ** 2), 2)
    }
    
    return {
        'cpu': cpu_metrics,
        'memory': memory_metrics,
        'disk': disk_metrics,
        'process': process_metrics,
        'network': network_metrics,
        'monitoring_active': is_monitoring_active()
    }


@router.get("/sync", response_model=SyncMetricsResponse)
async def get_dashboard_sync_metrics() -> Dict[str, Any]:
    """
    Get sync metrics for the dashboard.
    
    Returns:
        Sync metrics
    """
    # Get metrics from registry
    metrics_dict = get_metrics_as_dict()
    
    # Extract sync operations count by type and status
    operations_count = {}
    if 'sync_operations_total' in metrics_dict:
        sync_ops = metrics_dict['sync_operations_total']
        for label, count in sync_ops.get('values', {}).items():
            if label != 'default':
                # Parse label values
                label_parts = label.split(',')
                operation_type = None
                status = None
                
                for part in label_parts:
                    if part.startswith('operation_type='):
                        operation_type = part.split('=')[1]
                    elif part.startswith('status='):
                        status = part.split('=')[1]
                
                if operation_type and status:
                    key = f"{operation_type}_{status}"
                    operations_count[key] = count
    
    # Calculate success rate
    total_completed = 0
    total_failed = 0
    
    for key, count in operations_count.items():
        if key.endswith('_completed'):
            total_completed += count
        elif key.endswith('_failed'):
            total_failed += count
    
    total = total_completed + total_failed
    success_rate = (total_completed / total) * 100 if total > 0 else 0
    
    # Get records processed, succeeded, failed
    records_processed = 0
    if 'records_processed_total' in metrics_dict:
        for count in metrics_dict['records_processed_total'].get('values', {}).values():
            records_processed += count
    
    records_succeeded = 0
    if 'records_succeeded_total' in metrics_dict:
        for count in metrics_dict['records_succeeded_total'].get('values', {}).values():
            records_succeeded += count
    
    records_failed = 0
    if 'records_failed_total' in metrics_dict:
        for count in metrics_dict['records_failed_total'].get('values', {}).values():
            records_failed += count
    
    # Calculate average duration
    duration_sum = 0
    duration_count = 0
    
    if 'sync_duration_seconds' in metrics_dict:
        for label, value in metrics_dict['sync_duration_seconds'].get('sums', {}).items():
            duration_sum += value
            duration_count += metrics_dict['sync_duration_seconds'].get('counts', {}).get(label, 0)
    
    average_duration = duration_sum / duration_count if duration_count > 0 else 0
    
    # Get entity type metrics
    entity_metrics = get_entity_type_summary()
    
    return {
        'operations_count': operations_count,
        'success_rate': round(success_rate, 2),
        'records_processed': records_processed,
        'records_succeeded': records_succeeded,
        'records_failed': records_failed,
        'average_duration': round(average_duration, 2),
        'entity_metrics': entity_metrics
    }


@router.get("/status", response_model=SyncStatusSummaryResponse)
async def get_dashboard_sync_status() -> Dict[str, Any]:
    """
    Get sync status summary for the dashboard.
    
    Returns:
        Sync status summary
    """
    return get_sync_summary()


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary() -> Dict[str, Any]:
    """
    Get a comprehensive dashboard summary.
    
    Returns:
        Dashboard summary including system metrics, sync metrics, and sync status
    """
    system_metrics = await get_dashboard_system_metrics()
    sync_metrics = await get_dashboard_sync_metrics()
    sync_status = await get_dashboard_sync_status()
    
    return {
        'system_metrics': system_metrics,
        'sync_metrics': sync_metrics,
        'sync_status': sync_status
    }


@router.get("/sync/{sync_id}")
async def get_dashboard_sync_details(sync_id: str = Path(..., description="ID of the sync operation")) -> Dict[str, Any]:
    """
    Get detailed information about a specific sync operation.
    
    Args:
        sync_id: ID of the sync operation
        
    Returns:
        Detailed sync operation information
    """
    sync_op = get_sync_operation(sync_id)
    
    if not sync_op:
        raise HTTPException(status_code=404, detail=f"Sync operation {sync_id} not found")
    
    return sync_op.to_dict()


@router.get("/recent")
async def get_dashboard_recent_syncs(
    limit: int = Query(10, description="Maximum number of sync operations to return"),
    offset: int = Query(0, description="Number of sync operations to skip"),
    sync_type: Optional[str] = Query(None, description="Filter by sync type"),
    source_system: Optional[str] = Query(None, description="Filter by source system"),
    target_system: Optional[str] = Query(None, description="Filter by target system"),
    status: Optional[str] = Query(None, description="Filter by status")
) -> List[Dict[str, Any]]:
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
    # Convert string filters to enum values if provided
    sync_type_enum = SyncType(sync_type) if sync_type else None
    status_enum = SyncStatus(status) if status else None
    
    # Get recent sync operations
    sync_ops = get_recent_sync_operations(
        limit=limit,
        offset=offset,
        sync_type=sync_type_enum,
        source_system=source_system,
        target_system=target_system,
        status=status_enum
    )
    
    # Convert to dictionaries
    return [sync_op.to_dict() for sync_op in sync_ops]


@router.get("/metrics")
async def get_dashboard_raw_metrics() -> Dict[str, Any]:
    """
    Get raw metrics for the dashboard.
    
    Returns:
        Raw metrics
    """
    return get_metrics_as_dict()


@router.post("/monitoring/start")
async def start_system_monitoring(
    interval: int = Query(60, description="Monitoring interval in seconds")
) -> Dict[str, Any]:
    """
    Start system monitoring.
    
    Args:
        interval: Monitoring interval in seconds
        
    Returns:
        Status message
    """
    if is_monitoring_active():
        return {
            'status': 'already_active',
            'message': 'System monitoring is already active'
        }
    
    start_monitoring(interval)
    
    return {
        'status': 'started',
        'message': f'System monitoring started with interval {interval} seconds'
    }


@router.post("/monitoring/stop")
async def stop_system_monitoring() -> Dict[str, Any]:
    """
    Stop system monitoring.
    
    Returns:
        Status message
    """
    if not is_monitoring_active():
        return {
            'status': 'not_active',
            'message': 'System monitoring is not active'
        }
    
    stop_monitoring()
    
    return {
        'status': 'stopped',
        'message': 'System monitoring stopped'
    }