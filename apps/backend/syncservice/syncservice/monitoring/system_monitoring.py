"""
System monitoring module for the SyncService.

This module is responsible for monitoring system resources and performance,
including CPU, memory, and disk usage.
"""

import logging
import time
import asyncio
import os
import psutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable

from .metrics import MetricsCollector

logger = logging.getLogger(__name__)


class SystemMonitor:
    """
    Component responsible for monitoring system resources and performance.
    
    This component collects metrics related to system resources such as CPU usage,
    memory usage, and disk I/O.
    """
    
    def __init__(self, metrics_collector: MetricsCollector, interval_seconds: int = 60):
        """
        Initialize the System Monitor.
        
        Args:
            metrics_collector: Metrics collector for storing system metrics
            interval_seconds: Interval in seconds between monitoring checks
        """
        self.metrics_collector = metrics_collector
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.monitor_task = None
    
    async def start(self):
        """Start the system monitoring process."""
        if self.is_running:
            logger.warning("System monitor is already running")
            return
        
        logger.info(f"Starting system monitor with {self.interval_seconds}s interval")
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop(self):
        """Stop the system monitoring process."""
        if not self.is_running:
            logger.warning("System monitor is not running")
            return
        
        logger.info("Stopping system monitor")
        self.is_running = False
        
        if self.monitor_task:
            try:
                self.monitor_task.cancel()
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            
            self.monitor_task = None
    
    async def _monitoring_loop(self):
        """Main monitoring loop that collects metrics at regular intervals."""
        try:
            while self.is_running:
                await self._collect_system_metrics()
                await asyncio.sleep(self.interval_seconds)
        except asyncio.CancelledError:
            logger.info("System monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in system monitoring loop: {str(e)}")
            self.is_running = False
    
    async def _collect_system_metrics(self):
        """Collect and record system metrics."""
        try:
            # CPU usage metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            await self.metrics_collector.record_system_metric(
                name="cpu.percent", value=cpu_percent, unit="%")
            
            per_cpu = psutil.cpu_percent(interval=1, percpu=True)
            for i, percent in enumerate(per_cpu):
                await self.metrics_collector.record_system_metric(
                    name=f"cpu.{i}.percent", value=percent, unit="%")
            
            # Memory usage metrics
            memory = psutil.virtual_memory()
            await self.metrics_collector.record_system_metric(
                name="memory.total", value=memory.total, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="memory.available", value=memory.available, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="memory.used", value=memory.used, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="memory.percent", value=memory.percent, unit="%")
            
            # Swap memory metrics
            swap = psutil.swap_memory()
            await self.metrics_collector.record_system_metric(
                name="swap.total", value=swap.total, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="swap.used", value=swap.used, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="swap.percent", value=swap.percent, unit="%")
            
            # Disk usage metrics
            for disk in psutil.disk_partitions():
                if not disk.mountpoint or not os.access(disk.mountpoint, os.R_OK):
                    continue
                
                usage = psutil.disk_usage(disk.mountpoint)
                name_prefix = f"disk.{disk.device.replace('/', '_')}"
                
                await self.metrics_collector.record_system_metric(
                    name=f"{name_prefix}.total", value=usage.total, unit="bytes")
                await self.metrics_collector.record_system_metric(
                    name=f"{name_prefix}.used", value=usage.used, unit="bytes")
                await self.metrics_collector.record_system_metric(
                    name=f"{name_prefix}.percent", value=usage.percent, unit="%")
            
            # Disk I/O metrics
            disk_io = psutil.disk_io_counters()
            if disk_io:
                await self.metrics_collector.record_system_metric(
                    name="disk.read_bytes", value=disk_io.read_bytes, unit="bytes")
                await self.metrics_collector.record_system_metric(
                    name="disk.write_bytes", value=disk_io.write_bytes, unit="bytes")
                await self.metrics_collector.record_system_metric(
                    name="disk.read_count", value=disk_io.read_count, unit="operations")
                await self.metrics_collector.record_system_metric(
                    name="disk.write_count", value=disk_io.write_count, unit="operations")
            
            # Network I/O metrics
            net_io = psutil.net_io_counters()
            await self.metrics_collector.record_system_metric(
                name="network.bytes_sent", value=net_io.bytes_sent, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="network.bytes_recv", value=net_io.bytes_recv, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="network.packets_sent", value=net_io.packets_sent, unit="packets")
            await self.metrics_collector.record_system_metric(
                name="network.packets_recv", value=net_io.packets_recv, unit="packets")
            
            # Process metrics for the current process
            process = psutil.Process()
            
            # CPU usage for this process
            process_cpu = process.cpu_percent(interval=1)
            await self.metrics_collector.record_system_metric(
                name="process.cpu.percent", value=process_cpu, unit="%")
            
            # Memory usage for this process
            process_memory = process.memory_info()
            await self.metrics_collector.record_system_metric(
                name="process.memory.rss", value=process_memory.rss, unit="bytes")
            await self.metrics_collector.record_system_metric(
                name="process.memory.vms", value=process_memory.vms, unit="bytes")
            
            # Open files count
            try:
                open_files = len(process.open_files())
                await self.metrics_collector.record_system_metric(
                    name="process.open_files", value=open_files, unit="files")
            except Exception:
                pass
            
            # Thread count
            num_threads = process.num_threads()
            await self.metrics_collector.record_system_metric(
                name="process.num_threads", value=num_threads, unit="threads")
            
            logger.debug("Collected system metrics successfully")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {str(e)}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """
        Get the current system health status.
        
        Returns:
            Dictionary containing system health metrics
        """
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk_usage = {}
            for disk in psutil.disk_partitions():
                if not disk.mountpoint or not os.access(disk.mountpoint, os.R_OK):
                    continue
                
                usage = psutil.disk_usage(disk.mountpoint)
                disk_usage[disk.mountpoint] = {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent
                }
            
            # Process info
            process = psutil.Process()
            process_cpu = process.cpu_percent(interval=0.1)
            process_memory = process.memory_info()
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "cpu": {
                    "percent": cpu_percent,
                    "per_cpu": psutil.cpu_percent(interval=0.1, percpu=True)
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": disk_usage,
                "process": {
                    "cpu_percent": process_cpu,
                    "memory_rss": process_memory.rss,
                    "memory_vms": process_memory.vms,
                    "num_threads": process.num_threads()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def generate_resource_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate a resource usage report for a specific time period.
        
        Args:
            start_time: Start of the reporting period
            end_time: End of the reporting period
            
        Returns:
            Dictionary containing resource usage statistics
        """
        # Get CPU metrics
        cpu_metrics = await self.metrics_collector.get_metrics(
            metric_name_prefix="system.cpu.percent",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Get memory metrics
        memory_metrics = await self.metrics_collector.get_metrics(
            metric_name_prefix="system.memory.percent",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Get disk metrics
        disk_metrics = await self.metrics_collector.get_metrics(
            metric_name_prefix="system.disk",
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Process CPU metrics
        avg_cpu = 0
        max_cpu = 0
        min_cpu = 100
        
        if cpu_metrics:
            cpu_values = [m["value"] for m in cpu_metrics]
            avg_cpu = sum(cpu_values) / len(cpu_values)
            max_cpu = max(cpu_values)
            min_cpu = min(cpu_values)
        
        # Process memory metrics
        avg_memory = 0
        max_memory = 0
        min_memory = 100
        
        if memory_metrics:
            memory_values = [m["value"] for m in memory_metrics]
            avg_memory = sum(memory_values) / len(memory_values)
            max_memory = max(memory_values)
            min_memory = min(memory_values)
        
        # Process disk metrics
        disk_stats = {}
        
        for metric in disk_metrics:
            # Extract disk name from metric name
            parts = metric["name"].split('.')
            if len(parts) >= 4 and parts[-1] == "percent":
                disk_name = parts[2]
                
                if disk_name not in disk_stats:
                    disk_stats[disk_name] = {
                        "values": [],
                        "avg": 0,
                        "max": 0,
                        "min": 100
                    }
                
                disk_stats[disk_name]["values"].append(metric["value"])
        
        # Calculate disk statistics
        for disk_name, stats in disk_stats.items():
            values = stats["values"]
            if values:
                stats["avg"] = sum(values) / len(values)
                stats["max"] = max(values)
                stats["min"] = min(values)
            
            # Remove the raw values from the result
            del stats["values"]
        
        return {
            "start_time": start_time.isoformat() if start_time else None,
            "end_time": end_time.isoformat() if end_time else None,
            "cpu": {
                "average_percent": avg_cpu,
                "max_percent": max_cpu,
                "min_percent": min_cpu,
                "sample_count": len(cpu_metrics)
            },
            "memory": {
                "average_percent": avg_memory,
                "max_percent": max_memory,
                "min_percent": min_memory,
                "sample_count": len(memory_metrics)
            },
            "disk": disk_stats
        }