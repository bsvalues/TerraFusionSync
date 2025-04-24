"""
Metrics collector for the SyncService.

This module is responsible for collecting, storing, and retrieving metrics related to
the SyncService operations and performance.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Component responsible for collecting, storing, and retrieving metrics.
    
    This component collects various metrics related to system performance and
    synchronization operations.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize the Metrics Collector.
        
        Args:
            db_session: Database session for storing metrics
        """
        self.db_session = db_session
        self.memory_metrics = {}  # For in-memory storage when db is not available
    
    async def record_sync_duration(
        self,
        sync_type: str,
        entity_type: str,
        duration_ms: float,
        record_count: int,
        operation_id: str
    ):
        """
        Record the duration of a synchronization operation.
        
        Args:
            sync_type: Type of sync operation (full, incremental)
            entity_type: Type of entity being synchronized
            duration_ms: Duration in milliseconds
            record_count: Number of records processed
            operation_id: ID of the sync operation
        """
        metric_name = f"sync_duration.{sync_type}.{entity_type}"
        timestamp = datetime.utcnow()
        
        metric_data = {
            "value": duration_ms,
            "unit": "ms",
            "count": record_count,
            "operation_id": operation_id,
            "timestamp": timestamp
        }
        
        logger.debug(f"Recording sync duration: {metric_name} = {duration_ms}ms "
                     f"for {record_count} records")
        
        try:
            if self.db_session:
                # Store in database
                from ..models.database import SystemMetric
                
                metric = SystemMetric(
                    metric_name=metric_name,
                    metric_value=duration_ms,
                    metric_unit="ms",
                    collection_time=timestamp
                )
                
                self.db_session.add(metric)
                await self.db_session.commit()
            else:
                # Store in memory
                if metric_name not in self.memory_metrics:
                    self.memory_metrics[metric_name] = []
                
                self.memory_metrics[metric_name].append(metric_data)
                
                # Limit the size of in-memory storage
                if len(self.memory_metrics[metric_name]) > 1000:
                    self.memory_metrics[metric_name] = self.memory_metrics[metric_name][-1000:]
        
        except Exception as e:
            logger.error(f"Error recording sync duration metric: {str(e)}")
    
    async def record_api_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float
    ):
        """
        Record metrics for an API request.
        
        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        metric_name = f"api_request.{method}.{endpoint}.{status_code}"
        timestamp = datetime.utcnow()
        
        metric_data = {
            "value": duration_ms,
            "unit": "ms",
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "timestamp": timestamp
        }
        
        logger.debug(f"Recording API request: {metric_name} = {duration_ms}ms")
        
        try:
            if self.db_session:
                # Store in database
                from ..models.database import SystemMetric
                
                metric = SystemMetric(
                    metric_name=metric_name,
                    metric_value=duration_ms,
                    metric_unit="ms",
                    collection_time=timestamp
                )
                
                self.db_session.add(metric)
                await self.db_session.commit()
            else:
                # Store in memory
                if metric_name not in self.memory_metrics:
                    self.memory_metrics[metric_name] = []
                
                self.memory_metrics[metric_name].append(metric_data)
                
                # Limit the size of in-memory storage
                if len(self.memory_metrics[metric_name]) > 1000:
                    self.memory_metrics[metric_name] = self.memory_metrics[metric_name][-1000:]
        
        except Exception as e:
            logger.error(f"Error recording API request metric: {str(e)}")
    
    async def record_system_metric(
        self,
        name: str,
        value: float,
        unit: str = ""
    ):
        """
        Record a system metric.
        
        Args:
            name: Name of the metric
            value: Metric value
            unit: Unit of measurement
        """
        metric_name = f"system.{name}"
        timestamp = datetime.utcnow()
        
        metric_data = {
            "value": value,
            "unit": unit,
            "timestamp": timestamp
        }
        
        logger.debug(f"Recording system metric: {metric_name} = {value}{unit}")
        
        try:
            if self.db_session:
                # Store in database
                from ..models.database import SystemMetric
                
                metric = SystemMetric(
                    metric_name=metric_name,
                    metric_value=value,
                    metric_unit=unit,
                    collection_time=timestamp
                )
                
                self.db_session.add(metric)
                await self.db_session.commit()
            else:
                # Store in memory
                if metric_name not in self.memory_metrics:
                    self.memory_metrics[metric_name] = []
                
                self.memory_metrics[metric_name].append(metric_data)
                
                # Limit the size of in-memory storage
                if len(self.memory_metrics[metric_name]) > 1000:
                    self.memory_metrics[metric_name] = self.memory_metrics[metric_name][-1000:]
        
        except Exception as e:
            logger.error(f"Error recording system metric: {str(e)}")
    
    async def get_metrics(
        self,
        metric_name_prefix: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get metrics matching a prefix within a time range.
        
        Args:
            metric_name_prefix: Prefix to match metric names
            start_time: Start of time range
            end_time: End of time range
            limit: Maximum number of metrics to return
            
        Returns:
            List of metrics
        """
        if end_time is None:
            end_time = datetime.utcnow()
        
        if start_time is None:
            start_time = end_time - timedelta(hours=1)
        
        logger.debug(f"Getting metrics with prefix {metric_name_prefix} from {start_time} to {end_time}")
        
        try:
            if self.db_session:
                # Query from database
                from ..models.database import SystemMetric
                from sqlalchemy import select
                
                query = (
                    select(SystemMetric)
                    .where(SystemMetric.metric_name.startswith(metric_name_prefix))
                    .where(SystemMetric.collection_time >= start_time)
                    .where(SystemMetric.collection_time <= end_time)
                    .order_by(SystemMetric.collection_time.desc())
                    .limit(limit)
                )
                
                result = await self.db_session.execute(query)
                metrics = result.scalars().all()
                
                return [
                    {
                        "name": metric.metric_name,
                        "value": metric.metric_value,
                        "unit": metric.metric_unit,
                        "timestamp": metric.collection_time.isoformat()
                    }
                    for metric in metrics
                ]
            else:
                # Get from memory
                result = []
                
                for name, metrics in self.memory_metrics.items():
                    if name.startswith(metric_name_prefix):
                        for metric in metrics:
                            timestamp = metric["timestamp"]
                            if start_time <= timestamp <= end_time:
                                result.append({
                                    "name": name,
                                    "value": metric["value"],
                                    "unit": metric.get("unit", ""),
                                    "timestamp": timestamp.isoformat()
                                })
                
                # Sort by timestamp, newest first
                result.sort(key=lambda x: x["timestamp"], reverse=True)
                
                # Limit the results
                return result[:limit]
        
        except Exception as e:
            logger.error(f"Error getting metrics: {str(e)}")
            return []
    
    async def get_sync_performance_metrics(
        self,
        sync_type: Optional[str] = None,
        entity_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get performance metrics for synchronization operations.
        
        Args:
            sync_type: Optional filter by sync type
            entity_type: Optional filter by entity type
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary of performance metrics
        """
        # Determine the metric name prefix
        prefix = "sync_duration"
        if sync_type:
            prefix = f"{prefix}.{sync_type}"
            if entity_type:
                prefix = f"{prefix}.{entity_type}"
        
        # Get raw metrics
        raw_metrics = await self.get_metrics(
            metric_name_prefix=prefix,
            start_time=start_time,
            end_time=end_time,
            limit=1000
        )
        
        # Process metrics into summary statistics
        if not raw_metrics:
            return {
                "count": 0,
                "total_duration_ms": 0,
                "avg_duration_ms": 0,
                "min_duration_ms": 0,
                "max_duration_ms": 0,
                "total_records": 0,
                "avg_records_per_second": 0
            }
        
        count = len(raw_metrics)
        total_duration_ms = sum(m["value"] for m in raw_metrics)
        avg_duration_ms = total_duration_ms / count
        min_duration_ms = min(m["value"] for m in raw_metrics)
        max_duration_ms = max(m["value"] for m in raw_metrics)
        
        # Calculate records processed if available
        total_records = 0
        for m in raw_metrics:
            if "count" in m:
                total_records += m["count"]
        
        # Calculate average records per second
        avg_records_per_second = 0
        if total_duration_ms > 0:
            avg_records_per_second = (total_records * 1000) / total_duration_ms
        
        return {
            "count": count,
            "total_duration_ms": total_duration_ms,
            "avg_duration_ms": avg_duration_ms,
            "min_duration_ms": min_duration_ms,
            "max_duration_ms": max_duration_ms,
            "total_records": total_records,
            "avg_records_per_second": avg_records_per_second
        }
    
    async def calculate_api_response_times(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate API response time statistics.
        
        Args:
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary mapping endpoints to response time statistics
        """
        # Get raw metrics
        raw_metrics = await self.get_metrics(
            metric_name_prefix="api_request",
            start_time=start_time,
            end_time=end_time,
            limit=10000
        )
        
        # Group by endpoint
        endpoint_metrics = {}
        for metric in raw_metrics:
            parts = metric["name"].split('.')
            if len(parts) >= 4:
                method = parts[1]
                endpoint = parts[2]
                status = parts[3]
                
                key = f"{method} {endpoint}"
                
                if key not in endpoint_metrics:
                    endpoint_metrics[key] = {
                        "count": 0,
                        "total_ms": 0,
                        "success_count": 0,
                        "error_count": 0,
                        "values": []
                    }
                
                endpoint_metrics[key]["count"] += 1
                endpoint_metrics[key]["total_ms"] += metric["value"]
                endpoint_metrics[key]["values"].append(metric["value"])
                
                if status.startswith('2'):
                    endpoint_metrics[key]["success_count"] += 1
                else:
                    endpoint_metrics[key]["error_count"] += 1
        
        # Calculate statistics for each endpoint
        result = {}
        for endpoint, data in endpoint_metrics.items():
            values = data["values"]
            count = data["count"]
            
            if count == 0:
                continue
            
            avg_ms = data["total_ms"] / count
            min_ms = min(values) if values else 0
            max_ms = max(values) if values else 0
            
            # Calculate 95th percentile
            if values:
                values.sort()
                idx = int(count * 0.95)
                p95_ms = values[idx] if idx < count else values[-1]
            else:
                p95_ms = 0
            
            error_rate = (data["error_count"] / count) * 100 if count > 0 else 0
            
            result[endpoint] = {
                "count": count,
                "avg_ms": avg_ms,
                "min_ms": min_ms,
                "max_ms": max_ms,
                "p95_ms": p95_ms,
                "error_rate": error_rate
            }
        
        return result


# Create a performance timing context manager
class TimingContext:
    """Context manager for measuring execution time of a block of code."""
    
    def __init__(self, metrics_collector, metric_type, **kwargs):
        """
        Initialize the timing context.
        
        Args:
            metrics_collector: Metrics collector to record timing
            metric_type: Type of metric to record
            **kwargs: Additional parameters for the metric
        """
        self.metrics_collector = metrics_collector
        self.metric_type = metric_type
        self.kwargs = kwargs
        self.start_time = None
    
    async def __aenter__(self):
        """Start timing when entering the context."""
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Record timing when exiting the context."""
        if self.start_time is None:
            return
        
        duration_ms = (time.time() - self.start_time) * 1000
        
        if self.metric_type == "sync":
            await self.metrics_collector.record_sync_duration(
                sync_type=self.kwargs.get("sync_type", "unknown"),
                entity_type=self.kwargs.get("entity_type", "unknown"),
                duration_ms=duration_ms,
                record_count=self.kwargs.get("record_count", 0),
                operation_id=self.kwargs.get("operation_id", "unknown")
            )
        elif self.metric_type == "api":
            await self.metrics_collector.record_api_request(
                endpoint=self.kwargs.get("endpoint", "unknown"),
                method=self.kwargs.get("method", "unknown"),
                status_code=self.kwargs.get("status_code", 0),
                duration_ms=duration_ms
            )
        elif self.metric_type == "system":
            await self.metrics_collector.record_system_metric(
                name=self.kwargs.get("name", "unknown"),
                value=duration_ms,
                unit="ms"
            )