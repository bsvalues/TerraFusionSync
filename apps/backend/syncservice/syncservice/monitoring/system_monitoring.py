"""
System resource monitoring for SyncService.

This module provides utilities for monitoring system resources like CPU, memory,
and disk usage, as well as collecting and reporting application metrics.
"""

import os
import time
import threading
import logging
from typing import Dict, Any, Optional

import psutil

from syncservice.monitoring.metrics import (
    update_gauge,
    create_gauge,
    get_gauge_value,
)

logger = logging.getLogger(__name__)

# Monitoring thread and control
_monitoring_thread = None
_monitoring_active = False
_monitoring_interval = 60  # in seconds

# Default monitoring interval in seconds
DEFAULT_MONITORING_INTERVAL = 60


def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system resource metrics.
    
    Returns:
        Dictionary of system metrics
    """
    metrics = {}
    
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_times_percent = psutil.cpu_times_percent(interval=None)
        
        metrics.update({
            'cpu_percent': cpu_percent,
            'cpu_user_percent': cpu_times_percent.user,
            'cpu_system_percent': cpu_times_percent.system,
            'cpu_idle_percent': cpu_times_percent.idle
        })
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        metrics.update({
            'memory_total_bytes': memory.total,
            'memory_available_bytes': memory.available,
            'memory_used_bytes': memory.used,
            'memory_percent': memory.percent
        })
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        metrics.update({
            'disk_total_bytes': disk.total,
            'disk_used_bytes': disk.used,
            'disk_free_bytes': disk.free,
            'disk_percent': disk.percent
        })
        
        # Process metrics
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        metrics.update({
            'process_cpu_percent': process.cpu_percent(interval=None),
            'process_memory_rss_bytes': process_memory.rss,  # Resident Set Size
            'process_memory_vms_bytes': process_memory.vms,  # Virtual Memory Size
            'process_threads': len(process.threads()),
            'process_open_files': len(process.open_files()),
            'process_connections': len(process.connections())
        })
        
        # Network metrics
        net_io = psutil.net_io_counters()
        
        metrics.update({
            'network_bytes_sent': net_io.bytes_sent,
            'network_bytes_recv': net_io.bytes_recv,
            'network_packets_sent': net_io.packets_sent,
            'network_packets_recv': net_io.packets_recv
        })
        
    except Exception as e:
        logger.error(f"Error collecting system metrics: {str(e)}")
    
    return metrics


def update_system_metrics() -> None:
    """
    Update system metrics in the metrics registry.
    """
    try:
        metrics = get_system_metrics()
        
        for metric_name, value in metrics.items():
            metric_exists = get_gauge_value(metric_name) is not None
            
            if not metric_exists:
                create_gauge(
                    name=metric_name,
                    description=f"System metric: {metric_name}",
                    initial_value=value
                )
            else:
                update_gauge(
                    name=metric_name,
                    value=value
                )
    except Exception as e:
        logger.error(f"Error updating system metrics: {str(e)}")


def monitoring_thread_func(interval: int) -> None:
    """
    Thread function for system monitoring.
    
    Args:
        interval: Monitoring interval in seconds
    """
    global _monitoring_active
    
    logger.info(f"Starting system monitoring with interval {interval} seconds")
    
    while _monitoring_active:
        try:
            # Update system metrics
            update_system_metrics()
            
            # Sleep for the specified interval
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Error in monitoring thread: {str(e)}")
            # Sleep for a shorter interval if an error occurs
            time.sleep(5)
    
    logger.info("System monitoring stopped")


def start_monitoring(interval: int = DEFAULT_MONITORING_INTERVAL) -> None:
    """
    Start system monitoring.
    
    Args:
        interval: Monitoring interval in seconds
    """
    global _monitoring_thread, _monitoring_active, _monitoring_interval
    
    if _monitoring_active:
        logger.info("System monitoring is already active")
        return
    
    _monitoring_interval = interval
    _monitoring_active = True
    
    # Create and start the monitoring thread
    _monitoring_thread = threading.Thread(
        target=monitoring_thread_func,
        args=(interval,),
        daemon=True
    )
    _monitoring_thread.start()


def stop_monitoring() -> None:
    """Stop system monitoring."""
    global _monitoring_active, _monitoring_thread
    
    if not _monitoring_active:
        logger.info("System monitoring is not active")
        return
    
    logger.info("Stopping system monitoring")
    _monitoring_active = False
    
    # Wait for the thread to terminate
    if _monitoring_thread and _monitoring_thread.is_alive():
        _monitoring_thread.join(timeout=5)
    
    _monitoring_thread = None


def is_monitoring_active() -> bool:
    """
    Check if system monitoring is active.
    
    Returns:
        True if monitoring is active, False otherwise
    """
    global _monitoring_active
    return _monitoring_active