"""
System monitoring module for SyncService.

This module provides system resource monitoring capabilities.
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any, Optional

import psutil

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
        self.running = False
        self.monitoring_task = None
        self.last_metrics = {}
        
    async def start(self):
        """
        Start the system monitoring loop.
        """
        if self.running:
            logger.warning("System monitor is already running")
            return
            
        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"System monitor started with interval {self.interval}s")
        
    async def stop(self):
        """
        Stop the system monitoring loop.
        """
        if not self.running:
            logger.warning("System monitor is not running")
            return
            
        self.running = False
        if self.monitoring_task:
            try:
                self.monitoring_task.cancel()
                await asyncio.wait_for(self.monitoring_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for monitoring task to cancel")
            except asyncio.CancelledError:
                pass
                
        logger.info("System monitor stopped")
        
    async def _monitoring_loop(self):
        """
        Background task to periodically collect system metrics.
        """
        try:
            while self.running:
                try:
                    # Get the current health metrics
                    metrics = self.get_system_health_sync()
                    
                    # Store the latest metrics
                    self.last_metrics = metrics
                    
                    # Log some metrics at INFO level
                    logger.info(
                        f"System health: CPU {metrics['cpu_percent']}%, "
                        f"Memory {metrics['memory_percent']}%, "
                        f"Disk {metrics['disk_percent']}%"
                    )
                    
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {str(e)}", exc_info=True)
                    
                # Wait for the next collection interval
                await asyncio.sleep(self.interval)
                
        except asyncio.CancelledError:
            logger.info("Monitoring task cancelled")
            raise
            
    def get_system_health_sync(self) -> Dict[str, Any]:
        """
        Get current system health information.
        
        Returns:
            Dictionary with system health metrics
        """
        cpu_percent = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get process information
        process = psutil.Process(os.getpid())
        process_mem = process.memory_info()
        
        # Build metrics dictionary
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": cpu_percent,
            "memory_total": mem.total,
            "memory_available": mem.available,
            "memory_used": mem.used,
            "memory_percent": mem.percent,
            "disk_total": disk.total,
            "disk_used": disk.used,
            "disk_free": disk.free,
            "disk_percent": disk.percent,
            "process_memory_rss": process_mem.rss,
            "process_memory_vms": process_mem.vms,
            "process_cpu_percent": process.cpu_percent(interval=None),
            "process_threads": len(process.threads()),
            "process_connections": len(process.connections(kind='all')),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        return metrics
        
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Async wrapper for get_system_health_sync.
        
        Returns:
            Dictionary with system health metrics
        """
        if self.last_metrics and time.time() - self._get_timestamp_seconds(self.last_metrics.get("timestamp")) < 10:
            # Return cached metrics if they're recent (within 10 seconds)
            return self.last_metrics
            
        # Get fresh metrics
        return self.get_system_health_sync()
        
    def _get_timestamp_seconds(self, timestamp: Optional[str]) -> float:
        """
        Parse ISO timestamp into seconds since epoch.
        
        Args:
            timestamp: ISO format timestamp string
            
        Returns:
            Seconds since epoch or 0 if parsing fails
        """
        if not timestamp:
            return 0
            
        try:
            dt = datetime.fromisoformat(timestamp)
            return dt.timestamp()
        except (ValueError, TypeError):
            return 0