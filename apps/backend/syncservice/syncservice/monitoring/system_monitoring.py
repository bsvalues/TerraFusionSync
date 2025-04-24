"""
System monitoring module for SyncService.

This module provides system resource monitoring capabilities.
"""

import asyncio
import logging
import os
import platform
import psutil
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Monitor system resources and provide health information.
    """
    
    def __init__(self, interval: int = 60):
        """
        Initialize the system monitor.
        
        Args:
            interval: Monitoring interval in seconds
        """
        self.interval = interval
        self.monitoring_task = None
        self.is_running = False
        self._last_health_check = None
        
    async def start(self):
        """
        Start the system monitoring loop.
        """
        if self.is_running:
            logger.warning("System monitor is already running")
            return
            
        self.is_running = True
        logger.info(f"Starting system monitor with {self.interval}s interval")
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        
    async def stop(self):
        """
        Stop the system monitoring loop.
        """
        if not self.is_running:
            logger.warning("System monitor is not running")
            return
            
        self.is_running = False
        logger.info("Stopping system monitor")
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                logger.info("System monitoring loop cancelled")
            
    async def _monitoring_loop(self):
        """
        Background task to periodically collect system metrics.
        """
        while self.is_running:
            try:
                health_data = self.get_system_health_sync()
                # In a real implementation, this would save metrics to a metrics store
                self._last_health_check = health_data
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {str(e)}", exc_info=True)
                
            # Wait for next interval
            await asyncio.sleep(self.interval)
    
    def get_system_health_sync(self) -> Dict[str, Any]:
        """
        Get current system health information.
        
        Returns:
            Dictionary with system health metrics
        """
        # Get CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
        
        # Get memory metrics
        virtual_memory = psutil.virtual_memory()
        memory_total = virtual_memory.total
        memory_available = virtual_memory.available
        memory_used = virtual_memory.used
        memory_percent = virtual_memory.percent
        
        # Get disk metrics
        disk_info = {}
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt':
                if 'cdrom' in part.opts or part.fstype == '':
                    continue
            
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_info[part.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            except PermissionError:
                continue
        
        # Get process metrics
        current_process = psutil.Process()
        process_info = {
            "cpu_percent": current_process.cpu_percent(),
            "memory_rss": current_process.memory_info().rss,
            "memory_vms": current_process.memory_info().vms,
            "num_threads": current_process.num_threads()
        }
        
        # Compile system health data
        health_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "percent": cpu_percent,
                "per_cpu": cpu_per_core
            },
            "memory": {
                "total": memory_total,
                "available": memory_available,
                "used": memory_used,
                "percent": memory_percent
            },
            "disk": disk_info,
            "process": process_info
        }
        
        return health_data
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Async wrapper for get_system_health_sync.
        
        Returns:
            Dictionary with system health metrics
        """
        # If we have recent data, return it
        if self._last_health_check:
            return self._last_health_check
            
        # Otherwise, get fresh data
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_system_health_sync)