"""
System Monitoring Module for TerraFusion SyncService.

This module provides system monitoring functionality to track CPU, memory,
disk usage, and other system metrics.
"""

import os
import time
import threading
import logging
import platform
from datetime import datetime
from typing import Dict, Any

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil module not available, using fallback metrics")

try:
    # Import database models
    from models import db, SystemMetrics
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    logging.warning("Database models not available for system monitoring")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    System monitoring component that tracks and records system metrics.
    
    This class provides methods to collect system metrics like CPU usage,
    memory usage, disk usage, and active connections. It can either
    return the current metrics or save them to a database.
    """
    
    def __init__(self, interval: int = 60, enable_db_storage: bool = True):
        """
        Initialize the system monitor.
        
        Args:
            interval: The interval in seconds to collect metrics (default: 60)
            enable_db_storage: Whether to store metrics in the database (default: True)
        """
        self.interval = interval
        self.enable_db_storage = enable_db_storage and DB_AVAILABLE
        self.running = False
        self.stop_event = threading.Event()
        self.thread = None
        self.error_count = 0
        self.operation_count = 0
        
        # Cache of the most recent metrics
        self.latest_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "active_connections": 0,
            "response_time": 0.0,
            "error_count": 0,
            "sync_operations_count": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def start(self) -> None:
        """Start the system monitoring process in a background thread."""
        if self.running:
            logger.warning("System monitor is already running")
            return
        
        self.running = True
        self.stop_event.clear()
        
        # Start a background thread to collect metrics
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        
        logger.info(f"System monitor started with interval of {self.interval} seconds")
    
    def stop(self) -> None:
        """Stop the system monitoring process."""
        if not self.running:
            logger.warning("System monitor is not running")
            return
        
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5.0)
        
        self.running = False
        logger.info("System monitor stopped")
    
    def _run(self) -> None:
        """
        Background process that collects system metrics at regular intervals.
        """
        try:
            while not self.stop_event.is_set():
                try:
                    # Collect and store metrics
                    metrics = self.get_system_metrics()
                    
                    # Update the latest metrics cache
                    self.latest_metrics = metrics
                    
                    # Store metrics in the database if enabled
                    if self.enable_db_storage:
                        self._store_metrics(metrics)
                    
                    # Sleep for the specified interval
                    for _ in range(self.interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {str(e)}")
                    # Sleep for a short interval and try again
                    time.sleep(5)
        except Exception as e:
            logger.error(f"System monitor thread error: {str(e)}")
            self.running = False
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get current system metrics.
        
        Returns:
            Dictionary containing system metrics
        """
        try:
            if not PSUTIL_AVAILABLE:
                # Fallback to dummy values if psutil is not available
                metrics = {
                    "cpu_usage": 0.0,
                    "memory_usage": 0.0,
                    "disk_usage": 0.0,
                    "active_connections": 0,
                    "response_time": self.latest_metrics.get("response_time", 0.0),
                    "error_count": self.error_count,
                    "sync_operations_count": self.operation_count,
                    "timestamp": datetime.utcnow().isoformat()
                }
                return metrics
            
            # Get CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Get disk usage
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent
            
            # Get active connections (approximate)
            # This uses the number of established connections as a proxy
            try:
                connections = len(psutil.net_connections(kind='inet'))
            except (psutil.AccessDenied, PermissionError):
                # Fallback if we don't have permission to get network connections
                connections = 0
                logger.warning("Permission denied when getting network connections")
            
            # Add the metrics to a dictionary
            metrics = {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_usage": disk_usage,
                "active_connections": connections,
                "response_time": self.latest_metrics.get("response_time", 0.0),
                "error_count": self.error_count,
                "sync_operations_count": self.operation_count,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return metrics
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            # Return the latest known metrics as a fallback
            return self.latest_metrics
    
    def _store_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Store system metrics in the database.
        
        Args:
            metrics: Dictionary containing system metrics
        """
        if not DB_AVAILABLE:
            return
        
        try:
            # Convert ISO timestamp string to datetime if needed
            timestamp = (datetime.fromisoformat(metrics["timestamp"]) 
                if isinstance(metrics["timestamp"], str) 
                else metrics["timestamp"])
            
            # Create a new SystemMetrics record
            metrics_record = SystemMetrics(
                timestamp=timestamp,
                cpu_usage=metrics["cpu_usage"],
                memory_usage=metrics["memory_usage"],
                disk_usage=metrics["disk_usage"],
                active_connections=metrics["active_connections"],
                response_time=metrics["response_time"],
                error_count=metrics["error_count"],
                sync_operations_count=metrics["sync_operations_count"]
            )
            
            # Add and commit to the database
            db.session.add(metrics_record)
            db.session.commit()
            
            logger.debug(f"Stored system metrics at {timestamp}")
        except Exception as e:
            logger.error(f"Error storing system metrics: {str(e)}")
    
    def record_error(self) -> None:
        """Record an error occurrence."""
        self.error_count += 1
    
    def record_operation(self) -> None:
        """Record a sync operation."""
        self.operation_count += 1
    
    def reset_counters(self) -> None:
        """Reset error and operation counters."""
        self.error_count = 0
        self.operation_count = 0
    
    def get_latest_metrics(self) -> Dict[str, Any]:
        """
        Get the most recently collected metrics.
        
        Returns:
            Dictionary containing the latest system metrics
        """
        return self.latest_metrics
    
    def update_response_time(self, response_time: float) -> None:
        """
        Update the average response time metric.
        
        Args:
            response_time: The response time in seconds to incorporate
        """
        # Simple moving average (more sophisticated approaches could be used)
        current = self.latest_metrics.get("response_time", 0.0)
        if current == 0.0:
            self.latest_metrics["response_time"] = response_time
        else:
            # Weight the new value at 10%
            self.latest_metrics["response_time"] = (current * 0.9) + (response_time * 0.1)


# Singleton instance for application-wide use
system_monitor = SystemMonitor()


def get_system_info() -> Dict[str, str]:
    """
    Get basic system information.
    
    Returns:
        Dictionary with system information
    """
    try:
        # Base system info that doesn't require psutil
        info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Add psutil-dependent metrics if available
        if PSUTIL_AVAILABLE:
            try:
                info["cpu_count"] = str(psutil.cpu_count(logical=True))
                info["physical_cpu_count"] = str(psutil.cpu_count(logical=False) or 1)
                info["total_memory"] = f"{psutil.virtual_memory().total / (1024**3):.2f} GB"
            except Exception as e:
                logger.warning(f"Error getting psutil system info: {str(e)}")
                # Provide fallback values
                info["cpu_count"] = "N/A"
                info["physical_cpu_count"] = "N/A"
                info["total_memory"] = "N/A"
        else:
            # Fallback values when psutil is not available
            info["cpu_count"] = "N/A"
            info["physical_cpu_count"] = "N/A"
            info["total_memory"] = "N/A"
        
        return info
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        return {"error": str(e)}


def get_process_info() -> Dict[str, Any]:
    """
    Get information about the current process.
    
    Returns:
        Dictionary with process information
    """
    # Base process info
    info = {
        "pid": os.getpid(),
        "cwd": os.getcwd(),
        "start_time": datetime.utcnow().isoformat()
    }
    
    # Add psutil-dependent metrics if available
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process(os.getpid())
            info.update({
                "memory_info": dict(process.memory_info()._asdict()),
                "cpu_percent": process.cpu_percent(interval=1.0),
                "num_threads": process.num_threads(),
                "start_time": datetime.fromtimestamp(process.create_time()).isoformat()
            })
        except Exception as e:
            logger.warning(f"Error getting psutil process info: {str(e)}")
    
    return info


if __name__ == "__main__":
    # Simple test to make sure the system monitor works
    monitor = SystemMonitor(interval=5, enable_db_storage=False)
    monitor.start()
    
    try:
        for _ in range(3):
            time.sleep(6)
            metrics = monitor.get_latest_metrics()
            print(f"Current metrics: {metrics}")
    finally:
        monitor.stop()