"""
Sync tracker module for the SyncService.

This module is responsible for tracking and monitoring synchronization operations,
providing insights into their progress, performance, and status.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set

from ..models.base import SyncStatus, SyncOperation, SyncOperationDetails, EntityStats

logger = logging.getLogger(__name__)


class SyncTracker:
    """
    Component responsible for tracking synchronization operations.
    
    This component monitors sync operations, their progress, and performance,
    providing insights and alerting on issues.
    """
    
    def __init__(self, db_session=None):
        """
        Initialize the Sync Tracker.
        
        Args:
            db_session: Database session for storing and retrieving sync operations
        """
        self.db_session = db_session
        self.active_operations = {}  # In-memory tracking of active operations
    
    async def register_operation(self, operation: SyncOperation) -> str:
        """
        Register a new sync operation for tracking.
        
        Args:
            operation: Sync operation to register
            
        Returns:
            ID of the registered operation
        """
        operation_id = operation.id
        
        logger.info(f"Registering sync operation {operation_id} "
                  f"({operation.sync_type.value}) for pair {operation.sync_pair_id}")
        
        try:
            if self.db_session:
                # Store in database
                from ..models.database import SyncOperationRecord
                
                record = SyncOperationRecord(
                    id=operation.id,
                    sync_pair_id=operation.sync_pair_id,
                    sync_type=operation.sync_type,
                    entity_types=operation.entity_types,
                    status=operation.status,
                    start_time=operation.start_time,
                    end_time=operation.end_time,
                    details=operation.details.dict() if operation.details else None,
                    error=operation.error
                )
                
                self.db_session.add(record)
                await self.db_session.commit()
            
            # Store in memory
            self.active_operations[operation_id] = operation
            
            return operation_id
            
        except Exception as e:
            logger.error(f"Error registering sync operation: {str(e)}")
            # Store only in memory if database fails
            self.active_operations[operation_id] = operation
            return operation_id
    
    async def update_operation(
        self,
        operation_id: str,
        status: Optional[SyncStatus] = None,
        end_time: Optional[datetime] = None,
        details: Optional[SyncOperationDetails] = None,
        error: Optional[str] = None
    ) -> bool:
        """
        Update the status and details of a sync operation.
        
        Args:
            operation_id: ID of the operation to update
            status: New status of the operation
            end_time: End time of the operation
            details: Updated operation details
            error: Error message if the operation failed
            
        Returns:
            True if update was successful, False otherwise
        """
        logger.info(f"Updating sync operation {operation_id}")
        
        # Check if operation exists in memory
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return False
        
        operation = self.active_operations[operation_id]
        
        # Update fields
        if status is not None:
            operation.status = status
        
        if end_time is not None:
            operation.end_time = end_time
        
        if details is not None:
            operation.details = details
        
        if error is not None:
            operation.error = error
        
        # If operation is complete, remove from active operations
        if status in [SyncStatus.COMPLETED, SyncStatus.FAILED, SyncStatus.CANCELED]:
            # Ensure end_time is set
            if operation.end_time is None:
                operation.end_time = datetime.utcnow()
        
        try:
            if self.db_session:
                # Update in database
                from ..models.database import SyncOperationRecord
                from sqlalchemy import select
                
                query = select(SyncOperationRecord).where(
                    SyncOperationRecord.id == operation_id
                )
                
                result = await self.db_session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    # Update fields
                    if status is not None:
                        record.status = status
                    
                    if end_time is not None:
                        record.end_time = end_time
                    
                    if details is not None:
                        record.details = details.dict()
                    
                    if error is not None:
                        record.error = error
                    
                    await self.db_session.commit()
                else:
                    logger.warning(f"Operation {operation_id} not found in database")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating sync operation: {str(e)}")
            return False
    
    async def get_operation(self, operation_id: str) -> Optional[SyncOperation]:
        """
        Get details of a specific sync operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Sync operation details if found, None otherwise
        """
        # Check memory first
        if operation_id in self.active_operations:
            return self.active_operations[operation_id]
        
        # Check database if available
        if self.db_session:
            try:
                from ..models.database import SyncOperationRecord
                from sqlalchemy import select
                
                query = select(SyncOperationRecord).where(
                    SyncOperationRecord.id == operation_id
                )
                
                result = await self.db_session.execute(query)
                record = result.scalar_one_or_none()
                
                if record:
                    # Convert database record to SyncOperation
                    details = None
                    if record.details:
                        details = SyncOperationDetails(**record.details)
                    
                    return SyncOperation(
                        id=record.id,
                        sync_pair_id=record.sync_pair_id,
                        sync_type=record.sync_type,
                        entity_types=record.entity_types,
                        status=record.status,
                        start_time=record.start_time,
                        end_time=record.end_time,
                        details=details,
                        error=record.error
                    )
            
            except Exception as e:
                logger.error(f"Error retrieving sync operation: {str(e)}")
        
        return None
    
    async def get_operations(
        self,
        sync_pair_id: Optional[str] = None,
        status: Optional[SyncStatus] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[SyncOperation]:
        """
        Get a list of sync operations with optional filtering.
        
        Args:
            sync_pair_id: Filter by sync pair ID
            status: Filter by operation status
            limit: Maximum number of operations to return
            offset: Offset for pagination
            
        Returns:
            List of sync operations
        """
        # Start with active operations
        operations = list(self.active_operations.values())
        
        # Apply filters to in-memory operations
        if sync_pair_id:
            operations = [op for op in operations if op.sync_pair_id == sync_pair_id]
        
        if status:
            operations = [op for op in operations if op.status == status]
        
        # Check database if available
        if self.db_session:
            try:
                from ..models.database import SyncOperationRecord
                from sqlalchemy import select
                
                # Build query
                query = select(SyncOperationRecord)
                
                if sync_pair_id:
                    query = query.where(SyncOperationRecord.sync_pair_id == sync_pair_id)
                
                if status:
                    query = query.where(SyncOperationRecord.status == status)
                
                # Order by start_time descending (newest first)
                query = query.order_by(SyncOperationRecord.start_time.desc())
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                # Execute query
                result = await self.db_session.execute(query)
                records = result.scalars().all()
                
                # Convert records to SyncOperation objects
                db_operations = []
                for record in records:
                    details = None
                    if record.details:
                        details = SyncOperationDetails(**record.details)
                    
                    op = SyncOperation(
                        id=record.id,
                        sync_pair_id=record.sync_pair_id,
                        sync_type=record.sync_type,
                        entity_types=record.entity_types,
                        status=record.status,
                        start_time=record.start_time,
                        end_time=record.end_time,
                        details=details,
                        error=record.error
                    )
                    
                    # Add to results if not already in active operations
                    if op.id not in self.active_operations:
                        db_operations.append(op)
                
                # Combine results
                operations.extend(db_operations)
                
                # Sort by start_time descending
                operations.sort(key=lambda op: op.start_time, reverse=True)
                
                # Apply pagination to combined results
                operations = operations[offset:offset + limit]
                
            except Exception as e:
                logger.error(f"Error retrieving sync operations: {str(e)}")
        
        return operations
    
    async def get_active_operations(self) -> List[SyncOperation]:
        """
        Get a list of currently active sync operations.
        
        Returns:
            List of active sync operations
        """
        # Get operations with status IN_PROGRESS
        return await self.get_operations(status=SyncStatus.IN_PROGRESS)
    
    async def track_entity_progress(
        self,
        operation_id: str,
        entity_type: str,
        processed: int = 0,
        succeeded: int = 0,
        failed: int = 0
    ) -> bool:
        """
        Update the progress for a specific entity type in a sync operation.
        
        Args:
            operation_id: ID of the sync operation
            entity_type: Type of entity being tracked
            processed: Number of records processed
            succeeded: Number of records successfully synced
            failed: Number of records that failed to sync
            
        Returns:
            True if update was successful, False otherwise
        """
        logger.debug(f"Tracking entity progress for {operation_id}: {entity_type} - "
                   f"processed: {processed}, succeeded: {succeeded}, failed: {failed}")
        
        # Check if operation exists
        if operation_id not in self.active_operations:
            logger.warning(f"Operation {operation_id} not found in active operations")
            return False
        
        operation = self.active_operations[operation_id]
        
        # Initialize details if not present
        if operation.details is None:
            operation.details = SyncOperationDetails(
                records_processed=0,
                records_succeeded=0,
                records_failed=0,
                entities={}
            )
        
        # Initialize entity stats if not present
        if entity_type not in operation.details.entities:
            operation.details.entities[entity_type] = {
                "processed": 0,
                "succeeded": 0,
                "failed": 0
            }
        
        # Update stats
        operation.details.entities[entity_type]["processed"] += processed
        operation.details.entities[entity_type]["succeeded"] += succeeded
        operation.details.entities[entity_type]["failed"] += failed
        
        # Update overall stats
        operation.details.records_processed += processed
        operation.details.records_succeeded += succeeded
        operation.details.records_failed += failed
        
        # Update operation in storage
        return await self.update_operation(
            operation_id=operation_id,
            details=operation.details
        )
    
    async def calculate_sync_metrics(
        self,
        sync_pair_id: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Calculate metrics for sync operations over a period of time.
        
        Args:
            sync_pair_id: Optional filter by sync pair ID
            days: Number of days to include in the metrics
            
        Returns:
            Dictionary of sync metrics
        """
        # Calculate date range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Get completed operations in the time range
        operations = []
        
        if self.db_session:
            try:
                from ..models.database import SyncOperationRecord
                from sqlalchemy import select
                
                # Build query
                query = select(SyncOperationRecord).where(
                    SyncOperationRecord.status == SyncStatus.COMPLETED
                ).where(
                    SyncOperationRecord.start_time >= start_time
                ).where(
                    SyncOperationRecord.start_time <= end_time
                )
                
                if sync_pair_id:
                    query = query.where(SyncOperationRecord.sync_pair_id == sync_pair_id)
                
                # Execute query
                result = await self.db_session.execute(query)
                records = result.scalars().all()
                
                # Convert to SyncOperation objects
                for record in records:
                    details = None
                    if record.details:
                        details = SyncOperationDetails(**record.details)
                    
                    op = SyncOperation(
                        id=record.id,
                        sync_pair_id=record.sync_pair_id,
                        sync_type=record.sync_type,
                        entity_types=record.entity_types,
                        status=record.status,
                        start_time=record.start_time,
                        end_time=record.end_time,
                        details=details,
                        error=record.error
                    )
                    
                    operations.append(op)
                
            except Exception as e:
                logger.error(f"Error calculating sync metrics: {str(e)}")
        
        # Add active operations if they match the criteria
        for op in self.active_operations.values():
            if op.status == SyncStatus.COMPLETED and start_time <= op.start_time <= end_time:
                if sync_pair_id is None or op.sync_pair_id == sync_pair_id:
                    if op.id not in [o.id for o in operations]:
                        operations.append(op)
        
        # Calculate metrics
        if not operations:
            return {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_operations": 0,
                "total_records_processed": 0,
                "total_records_succeeded": 0,
                "total_records_failed": 0,
                "success_rate": 0,
                "avg_duration_seconds": 0,
                "entity_stats": {}
            }
        
        # Count operations by type
        total_operations = len(operations)
        full_syncs = sum(1 for op in operations if op.sync_type.value == "full")
        incremental_syncs = total_operations - full_syncs
        
        # Calculate record stats
        total_processed = 0
        total_succeeded = 0
        total_failed = 0
        entity_stats = {}
        
        for op in operations:
            if op.details:
                total_processed += op.details.records_processed
                total_succeeded += op.details.records_succeeded
                total_failed += op.details.records_failed
                
                # Aggregate by entity type
                for entity_type, stats in op.details.entities.items():
                    if entity_type not in entity_stats:
                        entity_stats[entity_type] = {
                            "processed": 0,
                            "succeeded": 0,
                            "failed": 0
                        }
                    
                    entity_stats[entity_type]["processed"] += stats["processed"]
                    entity_stats[entity_type]["succeeded"] += stats["succeeded"]
                    entity_stats[entity_type]["failed"] += stats["failed"]
        
        # Calculate success rate
        success_rate = 0
        if total_processed > 0:
            success_rate = (total_succeeded / total_processed) * 100
        
        # Calculate average duration
        durations = []
        for op in operations:
            if op.end_time and op.start_time:
                duration = (op.end_time - op.start_time).total_seconds()
                durations.append(duration)
        
        avg_duration = 0
        if durations:
            avg_duration = sum(durations) / len(durations)
        
        return {
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "total_operations": total_operations,
            "full_syncs": full_syncs,
            "incremental_syncs": incremental_syncs,
            "total_records_processed": total_processed,
            "total_records_succeeded": total_succeeded,
            "total_records_failed": total_failed,
            "success_rate": success_rate,
            "avg_duration_seconds": avg_duration,
            "entity_stats": entity_stats
        }
    
    async def detect_stalled_operations(self, max_duration_minutes: int = 60) -> List[str]:
        """
        Detect operations that have been running for longer than expected.
        
        Args:
            max_duration_minutes: Maximum expected duration in minutes
            
        Returns:
            List of operation IDs that appear to be stalled
        """
        stalled_ops = []
        now = datetime.utcnow()
        threshold = timedelta(minutes=max_duration_minutes)
        
        # Check active operations
        for op_id, operation in self.active_operations.items():
            if operation.status == SyncStatus.IN_PROGRESS:
                duration = now - operation.start_time
                if duration > threshold:
                    stalled_ops.append(op_id)
                    logger.warning(f"Detected stalled operation: {op_id}, "
                                 f"running for {duration.total_seconds() / 60:.2f} minutes")
        
        return stalled_ops