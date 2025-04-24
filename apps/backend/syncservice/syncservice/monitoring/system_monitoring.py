"""
System Monitoring module for TerraFusion SyncService.

This module provides utilities for monitoring system resource usage
and performance metrics.
"""
import os
import time
import logging
import platform
from typing import Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import psutil for system metrics
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    logger.warning("psutil not available, system monitoring will be limited")


class SystemMonitor:
    """
    Monitor system resources.
    
    This class provides utilities for tracking CPU, memory, disk, and network usage.
    It includes defensive programming to handle missing or unavailable metrics.
    """
    
    def __init__(self):
        """
        Initialize the system monitor.
        """
        self.start_time = time.time()
        self.last_cpu_times = None
        self.last_cpu_check_time = None
        
        # Try to get initial CPU measurements
        if HAS_PSUTIL:
            try:
                self.last_cpu_times = psutil.cpu_times()
                self.last_cpu_check_time = time.time()
            except Exception as e:
                logger.error(f"Error initializing CPU monitoring: {str(e)}")
    
    def get_uptime(self) -> int:
        """
        Get system uptime in seconds.
        
        Returns:
            int: Uptime in seconds
        """
        return int(time.time() - self.start_time)
    
    def get_memory_usage(self) -> float:
        """
        Get memory usage percentage.
        
        Returns:
            float: Memory usage percentage (0-100)
        """
        if not HAS_PSUTIL:
            return 0.0
        
        try:
            memory = psutil.virtual_memory()
            return memory.percent
        except Exception as e:
            logger.error(f"Error getting memory usage: {str(e)}")
            return 0.0
    
    def get_disk_usage(self) -> float:
        """
        Get disk usage percentage for the root filesystem.
        
        Returns:
            float: Disk usage percentage (0-100)
        """
        if not HAS_PSUTIL:
            return 0.0
        
        try:
            disk = psutil.disk_usage('/')
            return disk.percent
        except Exception as e:
            logger.error(f"Error getting disk usage: {str(e)}")
            return 0.0
    
    def get_cpu_usage(self) -> float:
        """
        Get CPU usage percentage.
        
        Returns:
            float: CPU usage percentage (0-100)
        """
        if not HAS_PSUTIL:
            return 0.0
        
        try:
            # Use psutil to get accurate CPU usage
            return psutil.cpu_percent(interval=0.1)
        except Exception as e:
            logger.error(f"Error getting CPU usage: {str(e)}")
            return 0.0
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get comprehensive system health information.
        
        Returns:
            Dictionary with system health metrics
        """
        health = {
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": self.get_uptime(),
            "cpu_usage": self.get_cpu_usage(),
            "memory_usage": self.get_memory_usage(),
            "disk_usage": self.get_disk_usage(),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor()
            },
            "errors": []
        }
        
        return health
    
    def get_as_json(self) -> str:
        """
        Get system health as a JSON string.
        
        Returns:
            JSON string representation of system health
        """
        import json
        return json.dumps(self.get_system_health(), indent=2)