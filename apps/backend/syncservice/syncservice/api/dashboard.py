"""
Dashboard API for the SyncService.

This module defines the API endpoints for the monitoring dashboard.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..monitoring.metrics import MetricsCollector
from ..monitoring.system_monitoring import SystemMonitor
from ..monitoring.sync_tracker import SyncTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# Function to get metrics as dictionary for API response
def get_metrics_as_dict(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert metrics to a dictionary format for API response.
    
    Args:
        metrics: List of metric objects
        
    Returns:
        Dictionary mapping metric names to values
    """
    result = {}
    for metric in metrics:
        name = metric.get('name', '')
        value = metric.get('value', 0)
        result[name] = value
    return result


# Dependency to get the metrics collector
async def get_metrics_collector():
    """Dependency to get the metrics collector instance."""
    # This would normally retrieve the collector from a dependency container
    # For now, returning None as a placeholder
    return None


# Dependency to get the system monitor
async def get_system_monitor():
    """Dependency to get the system monitor instance."""
    # This would normally retrieve the monitor from a dependency container
    # For now, returning None as a placeholder
    return None


# Dependency to get the sync tracker
async def get_sync_tracker():
    """Dependency to get the sync tracker instance."""
    # This would normally retrieve the tracker from a dependency container
    # For now, returning None as a placeholder
    return None


@router.get("/metrics")
async def get_dashboard_metrics(
    metric_type: Optional[str] = Query(None),
    hours: int = Query(1, gt=0, le=72),
    metrics_collector: Optional[MetricsCollector] = Depends(get_metrics_collector)
):
    """
    Get metrics for the dashboard.
    
    Args:
        metric_type: Type of metrics to retrieve (system, api, sync)
        hours: Number of hours of data to retrieve
        metrics_collector: Metrics collector instance from dependency
        
    Returns:
        Dictionary of metrics
    """
    if metrics_collector is None:
        # Return placeholder data for development
        return {
            "system": {
                "cpu_percent": 25.4,
                "memory_percent": 42.7,
                "disk_percent": 12.3
            },
            "api": {
                "request_count": 1245,
                "avg_response_time_ms": 32.5,
                "error_rate": 0.8
            },
            "sync": {
                "operations_count": 24,
                "records_processed": 256789,
                "success_rate": 98.5
            }
        }
    
    # Real implementation would use the metrics collector
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    if metric_type == "system":
        metrics = await metrics_collector.get_metrics(
            metric_name_prefix="system.",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        return get_metrics_as_dict(metrics)
    
    elif metric_type == "api":
        metrics = await metrics_collector.get_metrics(
            metric_name_prefix="api_request.",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        return get_metrics_as_dict(metrics)
    
    elif metric_type == "sync":
        metrics = await metrics_collector.get_metrics(
            metric_name_prefix="sync_duration.",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        return get_metrics_as_dict(metrics)
    
    else:
        # Return all metrics types
        return {
            "system": get_metrics_as_dict(await metrics_collector.get_metrics(
                metric_name_prefix="system.",
                start_time=start_time,
                end_time=end_time,
                limit=500
            )),
            "api": get_metrics_as_dict(await metrics_collector.get_metrics(
                metric_name_prefix="api_request.",
                start_time=start_time,
                end_time=end_time,
                limit=500
            )),
            "sync": get_metrics_as_dict(await metrics_collector.get_metrics(
                metric_name_prefix="sync_duration.",
                start_time=start_time,
                end_time=end_time,
                limit=500
            ))
        }


@router.get("/system-health")
async def get_dashboard_system_health(
    system_monitor: Optional[SystemMonitor] = Depends(get_system_monitor)
):
    """
    Get system health information for the dashboard.
    
    Args:
        system_monitor: System monitor instance from dependency
        
    Returns:
        Dictionary of system health metrics
    """
    if system_monitor is None:
        # Return placeholder data for development
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": 25.4,
                "per_cpu": [22.1, 27.8, 24.5, 27.2]
            },
            "memory": {
                "total": 16_000_000_000,
                "available": 9_200_000_000,
                "used": 6_800_000_000,
                "percent": 42.5
            },
            "disk": {
                "/": {
                    "total": 100_000_000_000,
                    "used": 12_300_000_000,
                    "free": 87_700_000_000,
                    "percent": 12.3
                }
            },
            "process": {
                "cpu_percent": 3.2,
                "memory_rss": 512_000_000,
                "memory_vms": 1_024_000_000,
                "num_threads": 8
            }
        }
    
    # Real implementation would use the system monitor
    return await system_monitor.get_system_health()


@router.get("/sync-performance")
async def get_dashboard_sync_performance(
    sync_tracker: Optional[SyncTracker] = Depends(get_sync_tracker),
    days: int = Query(7, gt=0, le=30)
):
    """
    Get sync performance metrics for the dashboard.
    
    Args:
        sync_tracker: Sync tracker instance from dependency
        days: Number of days of data to include
        
    Returns:
        Dictionary of sync performance metrics
    """
    if sync_tracker is None:
        # Return placeholder data for development
        return {
            "start_time": (datetime.utcnow() - timedelta(days=days)).isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_operations": 24,
            "full_syncs": 8,
            "incremental_syncs": 16,
            "total_records_processed": 256_789,
            "total_records_succeeded": 252_938,
            "total_records_failed": 3_851,
            "success_rate": 98.5,
            "avg_duration_seconds": 502,
            "entity_stats": {
                "property": {
                    "processed": 98_456,
                    "succeeded": 97_123,
                    "failed": 1_333
                },
                "owner": {
                    "processed": 45_678,
                    "succeeded": 44_982,
                    "failed": 696
                },
                "assessment": {
                    "processed": 112_655,
                    "succeeded": 110_833,
                    "failed": 1_822
                }
            }
        }
    
    # Real implementation would use the sync tracker
    return await sync_tracker.calculate_sync_metrics(days=days)