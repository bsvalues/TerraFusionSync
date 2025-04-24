"""
System resource monitoring for SyncService.

This module provides utilities for monitoring system resources like CPU, memory,
and disk usage, as well as collecting and reporting application metrics.
"""

import logging
import threading
import time
import psutil
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple

from syncservice.monitoring.metrics import create_gauge, store_metrics

logger = logging.getLogger(__name__)

# Default interval for system monitoring (in seconds)
DEFAULT_MONITORING_INTERVAL = 60

# Flag to control monitoring thread
_monitoring_active = False

# Lock for thread synchronization
_monitoring_lock = threading.Lock()

# Monitoring thread
_monitoring_thread = None


def get_system_metrics() -> Dict[str, Any]:
    """
    Get current system resource metrics.
    
    Returns:
        Dictionary of system metrics
    """
    metrics = {}
    
    try:
        # CPU metrics
        metrics['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        metrics['cpu_user_percent'] = cpu_times.user
        metrics['cpu_system_percent'] = cpu_times.system
        metrics['cpu_idle_percent'] = cpu_times.idle
        
        # Memory metrics
        memory = psutil.virtual_memory()
        metrics['memory_total_bytes'] = memory.total
        metrics['memory_available_bytes'] = memory.available
        metrics['memory_used_bytes'] = memory.used
        metrics['memory_percent'] = memory.percent
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        metrics['disk_total_bytes'] = disk.total
        metrics['disk_used_bytes'] = disk.used
        metrics['disk_free_bytes'] = disk.free
        metrics['disk_percent'] = disk.percent
        
        # Process metrics for current process
        process = psutil.Process(os.getpid())
        metrics['process_cpu_percent'] = process.cpu_percent(interval=0.1)
        metrics['process_memory_rss_bytes'] = process.memory_info().rss
        metrics['process_memory_vms_bytes'] = process.memory_info().vms
        metrics['process_threads'] = process.num_threads()
        metrics['process_open_files'] = len(process.open_files())
        metrics['process_connections'] = len(process.connections())
        
        # Network metrics
        net_io = psutil.net_io_counters()
        metrics['network_bytes_sent'] = net_io.bytes_sent
        metrics['network_bytes_recv'] = net_io.bytes_recv
        metrics['network_packets_sent'] = net_io.packets_sent
        metrics['network_packets_recv'] = net_io.packets_recv
        
        return metrics
    except Exception as e:
        logger.error(f"Failed to get system metrics: {str(e)}")
        return {}


def update_system_metrics() -> None:
    """
    Update system metrics in the metrics registry.
    """
    try:
        # Get system metrics
        metrics = get_system_metrics()
        
        # Update CPU metrics
        if 'cpu_percent' in metrics:
            gauge = create_gauge('system_cpu_usage_percent', 'CPU usage as a percentage')
            gauge.set(metrics['cpu_percent'])
        
        if 'cpu_user_percent' in metrics:
            gauge = create_gauge('system_cpu_user_percent', 'CPU user time as a percentage')
            gauge.set(metrics['cpu_user_percent'])
        
        if 'cpu_system_percent' in metrics:
            gauge = create_gauge('system_cpu_system_percent', 'CPU system time as a percentage')
            gauge.set(metrics['cpu_system_percent'])
        
        if 'cpu_idle_percent' in metrics:
            gauge = create_gauge('system_cpu_idle_percent', 'CPU idle time as a percentage')
            gauge.set(metrics['cpu_idle_percent'])
        
        # Update memory metrics
        if 'memory_total_bytes' in metrics:
            gauge = create_gauge('system_memory_total_bytes', 'Total system memory in bytes')
            gauge.set(metrics['memory_total_bytes'])
        
        if 'memory_available_bytes' in metrics:
            gauge = create_gauge('system_memory_available_bytes', 'Available system memory in bytes')
            gauge.set(metrics['memory_available_bytes'])
        
        if 'memory_used_bytes' in metrics:
            gauge = create_gauge('system_memory_used_bytes', 'Used system memory in bytes')
            gauge.set(metrics['memory_used_bytes'])
        
        if 'memory_percent' in metrics:
            gauge = create_gauge('system_memory_usage_percent', 'Memory usage as a percentage')
            gauge.set(metrics['memory_percent'])
        
        # Update disk metrics
        if 'disk_total_bytes' in metrics:
            gauge = create_gauge('system_disk_total_bytes', 'Total disk space in bytes')
            gauge.set(metrics['disk_total_bytes'])
        
        if 'disk_used_bytes' in metrics:
            gauge = create_gauge('system_disk_used_bytes', 'Used disk space in bytes')
            gauge.set(metrics['disk_used_bytes'])
        
        if 'disk_free_bytes' in metrics:
            gauge = create_gauge('system_disk_free_bytes', 'Free disk space in bytes')
            gauge.set(metrics['disk_free_bytes'])
        
        if 'disk_percent' in metrics:
            gauge = create_gauge('system_disk_usage_percent', 'Disk usage as a percentage')
            gauge.set(metrics['disk_percent'])
        
        # Update process metrics
        if 'process_cpu_percent' in metrics:
            gauge = create_gauge('process_cpu_usage_percent', 'Process CPU usage as a percentage')
            gauge.set(metrics['process_cpu_percent'])
        
        if 'process_memory_rss_bytes' in metrics:
            gauge = create_gauge('process_memory_rss_bytes', 'Process resident set size in bytes')
            gauge.set(metrics['process_memory_rss_bytes'])
        
        if 'process_memory_vms_bytes' in metrics:
            gauge = create_gauge('process_memory_vms_bytes', 'Process virtual memory size in bytes')
            gauge.set(metrics['process_memory_vms_bytes'])
        
        if 'process_threads' in metrics:
            gauge = create_gauge('process_threads', 'Number of threads in the process')
            gauge.set(metrics['process_threads'])
        
        if 'process_open_files' in metrics:
            gauge = create_gauge('process_open_files', 'Number of open files by the process')
            gauge.set(metrics['process_open_files'])
        
        if 'process_connections' in metrics:
            gauge = create_gauge('process_connections', 'Number of network connections by the process')
            gauge.set(metrics['process_connections'])
        
        # Update network metrics
        if 'network_bytes_sent' in metrics:
            gauge = create_gauge('network_bytes_sent', 'Number of bytes sent over the network')
            gauge.set(metrics['network_bytes_sent'])
        
        if 'network_bytes_recv' in metrics:
            gauge = create_gauge('network_bytes_recv', 'Number of bytes received over the network')
            gauge.set(metrics['network_bytes_recv'])
        
        if 'network_packets_sent' in metrics:
            gauge = create_gauge('network_packets_sent', 'Number of packets sent over the network')
            gauge.set(metrics['network_packets_sent'])
        
        if 'network_packets_recv' in metrics:
            gauge = create_gauge('network_packets_recv', 'Number of packets received over the network')
            gauge.set(metrics['network_packets_recv'])
        
        # Store metrics periodically
        store_metrics()
        
    except Exception as e:
        logger.error(f"Failed to update system metrics: {str(e)}")


def monitoring_thread_func(interval: int) -> None:
    """
    Thread function for system monitoring.
    
    Args:
        interval: Monitoring interval in seconds
    """
    global _monitoring_active
    
    logger.info(f"Starting system monitoring thread with interval {interval} seconds")
    
    last_metrics_store = datetime.utcnow()
    
    while _monitoring_active:
        try:
            # Update system metrics
            update_system_metrics()
            
            # Store metrics every hour
            now = datetime.utcnow()
            if now - last_metrics_store > timedelta(hours=1):
                store_metrics()
                last_metrics_store = now
            
            # Sleep for the specified interval
            time.sleep(interval)
        except Exception as e:
            logger.error(f"Error in monitoring thread: {str(e)}")
            time.sleep(interval)


def start_monitoring(interval: int = DEFAULT_MONITORING_INTERVAL) -> None:
    """
    Start system monitoring.
    
    Args:
        interval: Monitoring interval in seconds
    """
    global _monitoring_active, _monitoring_thread
    
    with _monitoring_lock:
        if _monitoring_active:
            logger.info("System monitoring is already active")
            return
        
        _monitoring_active = True
        
        # Start monitoring thread
        _monitoring_thread = threading.Thread(
            target=monitoring_thread_func,
            args=(interval,),
            daemon=True
        )
        _monitoring_thread.start()
        
        logger.info("System monitoring started")


def stop_monitoring() -> None:
    """Stop system monitoring."""
    global _monitoring_active, _monitoring_thread
    
    with _monitoring_lock:
        if not _monitoring_active:
            logger.info("System monitoring is not active")
            return
        
        _monitoring_active = False
        
        # Wait for monitoring thread to stop
        if _monitoring_thread and _monitoring_thread.is_alive():
            _monitoring_thread.join(timeout=5)
        
        _monitoring_thread = None
        
        logger.info("System monitoring stopped")


def is_monitoring_active() -> bool:
    """
    Check if system monitoring is active.
    
    Returns:
        True if monitoring is active, False otherwise
    """
    with _monitoring_lock:
        return _monitoring_active


# Start monitoring on module import
try:
    start_monitoring()
except Exception as e:
    logger.error(f"Failed to start system monitoring: {str(e)}")