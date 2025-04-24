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
                    
                    # Log some metrics at INFO level (safely accessing the dictionary)
                    logger.info(
                        f"System health: CPU {metrics.get('cpu_percent', 0)}%, "
                        f"Memory {metrics.get('memory_percent', 0)}%, "
                        f"Disk {metrics.get('disk_percent', 0)}%"
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
        try:
            # Initialize with basic timestamp
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "OK"
            }
            
            # CPU info
            try:
                cpu_percent = psutil.cpu_percent(interval=1)
                metrics["cpu_count"] = psutil.cpu_count()
                metrics["cpu_percent"] = cpu_percent
            except Exception as e:
                logger.warning(f"Error getting CPU metrics: {str(e)}")
                metrics["cpu_percent"] = 0
                metrics["cpu_error"] = str(e)
            
            # Memory info
            try:
                mem = psutil.virtual_memory()
                metrics["memory_total"] = mem.total
                metrics["memory_available"] = mem.available
                metrics["memory_used"] = mem.used
                metrics["memory_percent"] = mem.percent
            except Exception as e:
                logger.warning(f"Error getting memory metrics: {str(e)}")
                metrics["memory_percent"] = 0
                metrics["memory_error"] = str(e)
            
            # Disk info
            try:
                disk = psutil.disk_usage('/')
                metrics["disk_total"] = disk.total
                metrics["disk_used"] = disk.used
                metrics["disk_free"] = disk.free
                metrics["disk_percent"] = disk.percent
            except Exception as e:
                logger.warning(f"Error getting disk metrics: {str(e)}")
                metrics["disk_percent"] = 0
                metrics["disk_error"] = str(e)
            
            # Process info
            try:
                process = psutil.Process(os.getpid())
                process_mem = process.memory_info()
                metrics["process_memory_rss"] = process_mem.rss
                metrics["process_memory_vms"] = process_mem.vms
                metrics["process_cpu_percent"] = process.cpu_percent(interval=None)
                metrics["process_threads"] = len(process.threads())
                metrics["process_connections"] = len(process.connections(kind='all'))
            except Exception as e:
                logger.warning(f"Error getting process metrics: {str(e)}")
                metrics["process_error"] = str(e)
            
            # System boot time
            try:
                metrics["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            except Exception as e:
                logger.warning(f"Error getting boot time: {str(e)}")
                metrics["boot_time_error"] = str(e)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Unexpected error in get_system_health_sync: {str(e)}", exc_info=True)
            # Return minimal system health info on error
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "ERROR",
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
        
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Async wrapper for get_system_health_sync.
        
        Returns:
            Dictionary with system health metrics
        """
        try:
            # First check if we have valid cached metrics that are recent
            if isinstance(self.last_metrics, dict) and self.last_metrics:
                try:
                    # Safely get the timestamp and compare with current time
                    timestamp = self.last_metrics.get("timestamp")
                    if timestamp and time.time() - self._get_timestamp_seconds(timestamp) < 10:
                        # Return cached metrics if they're recent (within 10 seconds)
                        logger.debug("Using cached system metrics")
                        return self.last_metrics
                except Exception as cache_error:
                    logger.warning(f"Error checking cached metrics: {str(cache_error)}")
                    # Continue to get fresh metrics
                
            # Get fresh metrics
            logger.debug("Getting fresh system metrics")
            return self.get_system_health_sync()
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}", exc_info=True)
            # Return minimal system health info on error
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "ERROR",
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
        
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