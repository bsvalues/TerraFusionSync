"""
Sync tracking module for SyncService.

This module provides functionality for tracking sync operations and their performance.
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Union

try:
    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class SyncStatus(str, Enum):
    """Enum for sync operation status."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SyncType(str, Enum):
    """Enum for sync operation types."""
    FULL = "FULL"
    INCREMENTAL = "INCREMENTAL"


class SyncTracker:
    """
    Track and record sync operations.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize the sync tracker.
        
        Args:
            db_url: Database URL for sync operation storage
        """
        self.db_url = db_url
        self.engine = None
        self.async_session = None
        self.in_memory_operations = []
        self.active_operations = []
        self.max_in_memory_operations = 1000  # Limit to prevent memory issues
        
    async def setup(self):
        """
        Set up the sync tracker.
        """
        if self.db_url and DB_AVAILABLE:
            try:
                # Create async engine and session
                self.engine = create_async_engine(self.db_url)
                self.async_session = sessionmaker(
                    self.engine, class_=AsyncSession, expire_on_commit=False
                )
                
                # Create sync_operations table if it doesn't exist
                async with self.engine.begin() as conn:
                    await conn.run_sync(self._create_tables)
                    
                logger.info("Sync tracker database connection established")
            except Exception as e:
                logger.error(f"Failed to set up sync tracker database: {str(e)}", exc_info=True)
        else:
            logger.warning("No database URL provided or SQLAlchemy not available. Using in-memory sync operation storage.")
    
    def _create_tables(self, conn):
        """
        Create sync operation tables if they don't exist.
        """
        if not DB_AVAILABLE:
            return
            
        metadata = sa.MetaData()
        
        # Sync operations table
        sa.Table(
            "sync_operations",
            metadata,
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("sync_pair_id", sa.String(64), nullable=False, index=True),
            sa.Column("sync_type", sa.String(20), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, index=True),
            sa.Column("start_time", sa.DateTime, nullable=False, index=True),
            sa.Column("end_time", sa.DateTime, nullable=True),
            sa.Column("duration_seconds", sa.Float, nullable=True),
            sa.Column("entity_types", sa.JSON, nullable=True),
            sa.Column("records_processed", sa.Integer, nullable=True),
            sa.Column("records_succeeded", sa.Integer, nullable=True),
            sa.Column("records_failed", sa.Integer, nullable=True),
            sa.Column("error_message", sa.Text, nullable=True),
            sa.Column("parameters", sa.JSON, nullable=True),
            sa.Column("results", sa.JSON, nullable=True)
        )
        
        # Sync operation details table
        sa.Table(
            "sync_operation_details",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("operation_id", sa.String(64), nullable=False, index=True),
            sa.Column("entity_type", sa.String(64), nullable=False),
            sa.Column("timestamp", sa.DateTime, nullable=False),
            sa.Column("message", sa.Text, nullable=False),
            sa.Column("level", sa.String(20), nullable=False),
            sa.Column("data", sa.JSON, nullable=True)
        )
        
        metadata.create_all(conn)
    
    async def start_operation(
        self,
        operation_id: str,
        sync_pair_id: str,
        sync_type: SyncType,
        entity_types: List[str],
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Start tracking a sync operation.
        
        Args:
            operation_id: Unique ID for the operation
            sync_pair_id: ID of the sync pair
            sync_type: Type of sync operation
            entity_types: List of entity types to sync
            parameters: Optional parameters for the operation
            
        Returns:
            Dictionary representation of the operation
        """
        start_time = datetime.utcnow()
        
        operation = {
            "id": operation_id,
            "sync_pair_id": sync_pair_id,
            "sync_type": sync_type,
            "status": SyncStatus.RUNNING,
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration_seconds": None,
            "entity_types": entity_types,
            "records_processed": 0,
            "records_succeeded": 0,
            "records_failed": 0,
            "error_message": None,
            "parameters": parameters or {},
            "results": {}
        }
        
        # Add to active operations
        self.active_operations.append(operation)
        
        # Add to in-memory operations (with limit)
        self.in_memory_operations.append(operation)
        if len(self.in_memory_operations) > self.max_in_memory_operations:
            self.in_memory_operations = self.in_memory_operations[-self.max_in_memory_operations:]
        
        # Store in database if available
        if self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    # Create new operation record
                    stmt = sa.text(
                        """
                        INSERT INTO sync_operations 
                        (id, sync_pair_id, sync_type, status, start_time, entity_types, parameters)
                        VALUES 
                        (:id, :sync_pair_id, :sync_type, :status, :start_time, :entity_types, :parameters)
                        """
                    )
                    await session.execute(
                        stmt,
                        {
                            "id": operation_id,
                            "sync_pair_id": sync_pair_id,
                            "sync_type": sync_type,
                            "status": SyncStatus.RUNNING,
                            "start_time": start_time,
                            "entity_types": json.dumps(entity_types),
                            "parameters": json.dumps(parameters or {})
                        }
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to store sync operation in database: {str(e)}", exc_info=True)
        
        return operation
    
    async def update_operation(
        self,
        operation_id: str,
        status: Optional[SyncStatus] = None,
        records_processed: Optional[int] = None,
        records_succeeded: Optional[int] = None,
        records_failed: Optional[int] = None,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a sync operation.
        
        Args:
            operation_id: ID of the operation to update
            status: Optional new status
            records_processed: Optional number of records processed
            records_succeeded: Optional number of records succeeded
            records_failed: Optional number of records failed
            error_message: Optional error message
            results: Optional results data
            
        Returns:
            Updated operation or None if not found
        """
        # Update in active operations list
        operation = None
        for i, op in enumerate(self.active_operations):
            if op["id"] == operation_id:
                operation = op
                
                # Update fields
                if status is not None:
                    operation["status"] = status
                if records_processed is not None:
                    operation["records_processed"] = records_processed
                if records_succeeded is not None:
                    operation["records_succeeded"] = records_succeeded
                if records_failed is not None:
                    operation["records_failed"] = records_failed
                if error_message is not None:
                    operation["error_message"] = error_message
                if results is not None:
                    operation["results"] = results
                
                # If operation is complete, update end time and duration
                if status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
                    end_time = datetime.utcnow()
                    operation["end_time"] = end_time.isoformat()
                    
                    start_time = datetime.fromisoformat(operation["start_time"]) if isinstance(operation["start_time"], str) else operation["start_time"]
                    operation["duration_seconds"] = (end_time - start_time).total_seconds()
                    
                    # Remove from active operations if complete
                    self.active_operations.pop(i)
                
                break
        
        # Update in in-memory operations list
        for i, op in enumerate(self.in_memory_operations):
            if op["id"] == operation_id:
                self.in_memory_operations[i] = operation
                break
        
        # Update in database if available
        if operation and self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    # Prepare update statement
                    update_fields = []
                    params = {"id": operation_id}
                    
                    if status is not None:
                        update_fields.append("status = :status")
                        params["status"] = status
                    if records_processed is not None:
                        update_fields.append("records_processed = :records_processed")
                        params["records_processed"] = records_processed
                    if records_succeeded is not None:
                        update_fields.append("records_succeeded = :records_succeeded")
                        params["records_succeeded"] = records_succeeded
                    if records_failed is not None:
                        update_fields.append("records_failed = :records_failed")
                        params["records_failed"] = records_failed
                    if error_message is not None:
                        update_fields.append("error_message = :error_message")
                        params["error_message"] = error_message
                    if results is not None:
                        update_fields.append("results = :results")
                        params["results"] = json.dumps(results)
                    
                    # Add end time and duration if operation is complete
                    if status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELLED]:
                        end_time = datetime.utcnow()
                        update_fields.append("end_time = :end_time")
                        params["end_time"] = end_time
                        
                        # Calculate duration
                        stmt = sa.text("SELECT start_time FROM sync_operations WHERE id = :id")
                        result = await session.execute(stmt, {"id": operation_id})
                        row = result.fetchone()
                        if row and row.start_time:
                            duration = (end_time - row.start_time).total_seconds()
                            update_fields.append("duration_seconds = :duration")
                            params["duration"] = duration
                    
                    # Execute update if we have fields to update
                    if update_fields:
                        stmt = sa.text(
                            f"UPDATE sync_operations SET {', '.join(update_fields)} WHERE id = :id"
                        )
                        await session.execute(stmt, params)
                        await session.commit()
            except Exception as e:
                logger.error(f"Failed to update sync operation in database: {str(e)}", exc_info=True)
        
        return operation
    
    async def complete_operation(
        self,
        operation_id: str,
        success: bool,
        records_processed: Optional[int] = None,
        records_succeeded: Optional[int] = None,
        records_failed: Optional[int] = None,
        error_message: Optional[str] = None,
        results: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Complete a sync operation.
        
        Args:
            operation_id: ID of the operation to complete
            success: Whether the operation was successful
            records_processed: Optional number of records processed
            records_succeeded: Optional number of records succeeded
            records_failed: Optional number of records failed
            error_message: Optional error message
            results: Optional results data
            
        Returns:
            Updated operation or None if not found
        """
        status = SyncStatus.COMPLETED if success else SyncStatus.FAILED
        
        return await self.update_operation(
            operation_id=operation_id,
            status=status,
            records_processed=records_processed,
            records_succeeded=records_succeeded,
            records_failed=records_failed,
            error_message=error_message,
            results=results
        )
    
    async def log_operation_detail(
        self,
        operation_id: str,
        entity_type: str,
        message: str,
        level: str = "INFO",
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Log a detail for a sync operation.
        
        Args:
            operation_id: ID of the operation
            entity_type: Type of entity (e.g., "property", "owner")
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
            data: Optional data to include with the log
        """
        timestamp = datetime.utcnow()
        
        # Store in database if available
        if self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    # Create new detail record
                    stmt = sa.text(
                        """
                        INSERT INTO sync_operation_details 
                        (operation_id, entity_type, timestamp, message, level, data)
                        VALUES 
                        (:operation_id, :entity_type, :timestamp, :message, :level, :data)
                        """
                    )
                    await session.execute(
                        stmt,
                        {
                            "operation_id": operation_id,
                            "entity_type": entity_type,
                            "timestamp": timestamp,
                            "message": message,
                            "level": level,
                            "data": json.dumps(data or {})
                        }
                    )
                    await session.commit()
            except Exception as e:
                logger.error(f"Failed to log operation detail in database: {str(e)}", exc_info=True)
    
    async def get_operations(
        self,
        sync_pair_id: Optional[str] = None,
        status: Optional[Union[SyncStatus, List[SyncStatus]]] = None,
        start_time_from: Optional[datetime] = None,
        start_time_to: Optional[datetime] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get sync operations matching the specified criteria.
        
        Args:
            sync_pair_id: Optional sync pair ID to filter by
            status: Optional status or list of statuses to filter by
            start_time_from: Optional minimum start time
            start_time_to: Optional maximum start time
            limit: Maximum number of operations to return
            offset: Offset for pagination
            
        Returns:
            List of operations
        """
        # If database is available, query from there
        if self.async_session and DB_AVAILABLE:
            try:
                async with self.async_session() as session:
                    query = "SELECT * FROM sync_operations WHERE 1=1"
                    params = {}
                    
                    if sync_pair_id:
                        query += " AND sync_pair_id = :sync_pair_id"
                        params["sync_pair_id"] = sync_pair_id
                    
                    if status:
                        if isinstance(status, list):
                            placeholders = [f":status_{i}" for i in range(len(status))]
                            query += f" AND status IN ({', '.join(placeholders)})"
                            for i, s in enumerate(status):
                                params[f"status_{i}"] = s
                        else:
                            query += " AND status = :status"
                            params["status"] = status
                    
                    if start_time_from:
                        query += " AND start_time >= :start_time_from"
                        params["start_time_from"] = start_time_from
                    
                    if start_time_to:
                        query += " AND start_time <= :start_time_to"
                        params["start_time_to"] = start_time_to
                    
                    query += " ORDER BY start_time DESC LIMIT :limit OFFSET :offset"
                    params["limit"] = limit
                    params["offset"] = offset
                    
                    result = await session.execute(sa.text(query), params)
                    
                    operations = []
                    for row in result:
                        operations.append({
                            "id": row.id,
                            "sync_pair_id": row.sync_pair_id,
                            "sync_type": row.sync_type,
                            "status": row.status,
                            "start_time": row.start_time.isoformat(),
                            "end_time": row.end_time.isoformat() if row.end_time else None,
                            "duration_seconds": row.duration_seconds,
                            "entity_types": json.loads(row.entity_types) if isinstance(row.entity_types, str) else (row.entity_types or []),
                            "records_processed": row.records_processed,
                            "records_succeeded": row.records_succeeded,
                            "records_failed": row.records_failed,
                            "error_message": row.error_message,
                            "parameters": json.loads(row.parameters) if isinstance(row.parameters, str) else (row.parameters or {}),
                            "results": json.loads(row.results) if isinstance(row.results, str) else (row.results or {})
                        })
                    
                    return operations
            except Exception as e:
                logger.error(f"Failed to query operations from database: {str(e)}", exc_info=True)
        
        # Fall back to in-memory operations
        filtered_operations = []
        
        for op in self.in_memory_operations:
            # Apply sync_pair_id filter
            if sync_pair_id and op["sync_pair_id"] != sync_pair_id:
                continue
            
            # Apply status filter
            if status:
                if isinstance(status, list):
                    if op["status"] not in status:
                        continue
                elif op["status"] != status:
                    continue
            
            # Apply start_time filters
            op_start_time = datetime.fromisoformat(op["start_time"]) if isinstance(op["start_time"], str) else op["start_time"]
            
            if start_time_from and op_start_time < start_time_from:
                continue
            
            if start_time_to and op_start_time > start_time_to:
                continue
            
            filtered_operations.append(op)
        
        # Sort by start_time (descending) and apply pagination
        filtered_operations.sort(key=lambda x: datetime.fromisoformat(x["start_time"]) if isinstance(x["start_time"], str) else x["start_time"], reverse=True)
        paginated_operations = filtered_operations[offset:offset + limit]
        
        return paginated_operations
    
    async def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get currently active sync operations.
        
        Returns:
            List of active operations
        """
        return self.active_operations
    
    async def calculate_sync_metrics(
        self,
        sync_pair_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate sync metrics for the specified time period.
        
        Args:
            sync_pair_id: Optional sync pair ID to filter by
            days: Number of days to include in the metrics
            
        Returns:
            Dictionary of sync metrics
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get completed operations in the time range
        operations = await self.get_operations(
            sync_pair_id=sync_pair_id,
            status=[SyncStatus.COMPLETED, SyncStatus.FAILED],
            start_time_from=start_time,
            start_time_to=end_time,
            limit=1000,  # Large limit to include all operations
            offset=0
        )
        
        # Calculate metrics
        total_operations = len(operations)
        full_syncs = 0
        incremental_syncs = 0
        total_records_processed = 0
        total_records_succeeded = 0
        total_records_failed = 0
        total_duration_seconds = 0
        successful_operations = 0
        
        # Track entity-specific stats
        entity_stats = {}
        
        for op in operations:
            # Count by sync type
            if op["sync_type"] == SyncType.FULL:
                full_syncs += 1
            elif op["sync_type"] == SyncType.INCREMENTAL:
                incremental_syncs += 1
            
            # Count successful operations
            if op["status"] == SyncStatus.COMPLETED:
                successful_operations += 1
            
            # Sum up record counts
            records_processed = op.get("records_processed", 0) or 0
            records_succeeded = op.get("records_succeeded", 0) or 0
            records_failed = op.get("records_failed", 0) or 0
            
            total_records_processed += records_processed
            total_records_succeeded += records_succeeded
            total_records_failed += records_failed
            
            # Sum up duration
            duration = op.get("duration_seconds", 0) or 0
            if duration > 0:
                total_duration_seconds += duration
            
            # Track entity-specific stats from results
            results = op.get("results", {}) or {}
            for entity_type, stats in results.items():
                if entity_type not in entity_stats:
                    entity_stats[entity_type] = {"processed": 0, "succeeded": 0, "failed": 0}
                
                entity_stats[entity_type]["processed"] += stats.get("processed", 0) or 0
                entity_stats[entity_type]["succeeded"] += stats.get("succeeded", 0) or 0
                entity_stats[entity_type]["failed"] += stats.get("failed", 0) or 0
        
        # Calculate success rate and average duration
        success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
        avg_duration_seconds = (total_duration_seconds / total_operations) if total_operations > 0 else 0
        
        # Compile metrics
        metrics = {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_operations": total_operations,
            "full_syncs": full_syncs,
            "incremental_syncs": incremental_syncs,
            "total_records_processed": total_records_processed,
            "total_records_succeeded": total_records_succeeded,
            "total_records_failed": total_records_failed,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration_seconds,
            "entity_stats": entity_stats
        }
        
        return metrics