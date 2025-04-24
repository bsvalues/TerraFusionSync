"""
Metrics collection for SyncService.

This module provides functionality for collecting and storing metrics.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collect and store metrics for the SyncService.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the metrics collector.
        
        Args:
            db_url: Database URL for metrics storage
        """
        self.db_url = db_url
        self.engine = None
        self.async_session = None
        self.in_memory_metrics = []
        self.max_in_memory_metrics = 10000  # Limit to prevent memory issues
        
    async def setup(self):
        """
        Set up the metrics collector.
        """
        if self.db_url and DB_AVAILABLE:
            try:
                # Create async engine and session
                self.engine = create_async_engine(self.db_url)
                self.async_session = sessionmaker(
                    self.engine, class_=AsyncSession, expire_on_commit=False
                )
                
                # Create metrics table if it doesn't exist
                async with self.engine.begin() as conn:
                    await conn.run_sync(self._create_tables)
                    
                logger.info("Metrics database connection established")
            except Exception as e:
                logger.error(f"Failed to set up metrics database: {str(e)}", exc_info=True)
        else:
            logger.warning("No database URL provided or SQLAlchemy not available. Using in-memory metrics storage.")
    
    def _create_tables(self, conn):
        """
        Create metrics tables if they don't exist.
        """
        if not DB_AVAILABLE:
            return
            
        metadata = sa.MetaData()
        
        # Metrics table
        sa.Table(
            "metrics",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String(255), nullable=False, index=True),
            sa.Column("value", sa.Float, nullable=False),
            sa.Column("tags", sa.JSON, nullable=True),
            sa.Column("timestamp", sa.DateTime, nullable=False, index=True)
        )
        
        metadata.create_all(conn)
    
    async def record_metric(self, name: str, value: Union[int, float], tags: Optional[Dict[str, str]] = None):
        """
        Record a metric.
        
        Args:
            name: Metric name
            value: Metric value
            tags: Optional tags for the metric
        """
        timestamp = datetime.utcnow()
        
        metric = {
            "name": name,
            "value": float(value),
            "tags": tags or {},
            "timestamp": timestamp.isoformat()
        }
        
        # Add to in-memory storage (with limit)
        self.in_memory_metrics.append(metric)
        if len(self.in_memory_metrics) > self.max_in_memory_metrics:
            self.in_memory_metrics = self.in_memory_metrics[-self.max_in_memory_metrics:]
        
        # Store in database if available
        if self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    # Create new metric record
                    stmt = sa.text(
                        "INSERT INTO metrics (name, value, tags, timestamp) VALUES (:name, :value, :tags, :timestamp)"
                    )
                    await session.execute(
                        stmt,
                        {
                            "name": name,
                            "value": value,
                            "tags": json.dumps(tags or {}),
                            "timestamp": timestamp
                        }
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to store metric in database: {str(e)}", exc_info=True)
    
    async def get_metrics(
        self,
        metric_name_prefix: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get metrics matching the specified criteria.
        
        Args:
            metric_name_prefix: Optional prefix to filter metrics by name
            start_time: Optional start time for time range filtering
            end_time: Optional end time for time range filtering
            limit: Maximum number of metrics to return
            
        Returns:
            List of metrics
        """
        # Default end time to now if not specified
        if end_time is None:
            end_time = datetime.utcnow()
            
        # Default start time to 1 hour ago if not specified
        if start_time is None:
            start_time = end_time - timedelta(hours=1)
        
        # If database is available, query from there
        if self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    query = "SELECT name, value, tags, timestamp FROM metrics WHERE timestamp BETWEEN :start_time AND :end_time"
                    params = {"start_time": start_time, "end_time": end_time}
                    
                    if metric_name_prefix:
                        query += " AND name LIKE :name_prefix"
                        params["name_prefix"] = f"{metric_name_prefix}%"
                        
                    query += " ORDER BY timestamp DESC LIMIT :limit"
                    params["limit"] = limit
                    
                    result = await session.execute(sa.text(query), params)
                    
                    metrics = []
                    for row in result:
                        metrics.append({
                            "name": row.name,
                            "value": row.value,
                            "tags": json.loads(row.tags) if isinstance(row.tags, str) else (row.tags or {}),
                            "timestamp": row.timestamp.isoformat() if hasattr(row.timestamp, 'isoformat') else row.timestamp
                        })
                    
                    return metrics
            except Exception as e:
                logger.error(f"Failed to query metrics from database: {str(e)}", exc_info=True)
        
        # Fall back to in-memory metrics
        filtered_metrics = []
        for metric in self.in_memory_metrics:
            # Parse timestamp for comparison
            metric_time = datetime.fromisoformat(metric["timestamp"]) if isinstance(metric["timestamp"], str) else metric["timestamp"]
            
            # Apply time range filter
            if metric_time < start_time or metric_time > end_time:
                continue
                
            # Apply name prefix filter
            if metric_name_prefix and not metric["name"].startswith(metric_name_prefix):
                continue
                
            filtered_metrics.append(metric)
            
            # Respect limit
            if len(filtered_metrics) >= limit:
                break
                
        return filtered_metrics