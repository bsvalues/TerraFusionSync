"""
Sync API endpoints for the SyncService.

This module provides API endpoints for triggering and managing sync operations
between source and target systems.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Path, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from syncservice.monitoring.sync_tracker import (
    SyncStatus, SyncType, SyncOperation,
    create_sync_operation, start_sync_operation, complete_sync_operation,
    fail_sync_operation, cancel_sync_operation, update_sync_progress,
    get_sync_operation, get_all_sync_operations, get_active_sync_operations
)

from syncservice.monitoring.metrics import (
    create_counter, increment_counter, create_gauge, update_gauge,
    create_histogram, observe_histogram
)

logger = logging.getLogger(__name__)

# Configure router
router = APIRouter()


# Request and response models
class FullSyncRequest(BaseModel):
    """Request model for full sync operations."""
    
    source_system: str = Field(..., description="Source system name")
    target_system: str = Field(..., description="Target system name")
    entity_types: List[str] = Field(..., description="List of entity types to sync")
    filter_criteria: Optional[Dict[str, Any]] = Field(
        None, description="Optional filter criteria for the sync operation"
    )


class IncrementalSyncRequest(BaseModel):
    """Request model for incremental sync operations."""
    
    source_system: str = Field(..., description="Source system name")
    target_system: str = Field(..., description="Target system name")
    entity_types: List[str] = Field(..., description="List of entity types to sync")
    since: Optional[datetime] = Field(
        None, description="Sync changes since this timestamp (defaults to 24 hours ago)"
    )
    filter_criteria: Optional[Dict[str, Any]] = Field(
        None, description="Optional filter criteria for the sync operation"
    )


class SyncResponse(BaseModel):
    """Response model for sync operations."""
    
    sync_id: str = Field(..., description="Unique identifier for the sync operation")
    status: str = Field(..., description="Current status of the sync operation")
    message: str = Field(..., description="Message describing the sync operation")


class SyncStatusResponse(BaseModel):
    """Response model for sync status."""
    
    sync_id: str = Field(..., description="Unique identifier for the sync operation")
    sync_type: str = Field(..., description="Type of sync operation")
    source_system: str = Field(..., description="Source system name")
    target_system: str = Field(..., description="Target system name")
    entity_types: List[str] = Field(..., description="List of entity types being synced")
    status: str = Field(..., description="Current status of the sync operation")
    started_at: Optional[datetime] = Field(None, description="Timestamp when the sync operation started")
    completed_at: Optional[datetime] = Field(None, description="Timestamp when the sync operation completed")
    duration_seconds: Optional[float] = Field(None, description="Duration of the sync operation in seconds")
    total_records: int = Field(..., description="Total number of records to sync")
    processed_records: int = Field(..., description="Number of records processed so far")
    succeeded_records: int = Field(..., description="Number of records successfully synced")
    failed_records: int = Field(..., description="Number of records that failed to sync")
    progress_percent: float = Field(..., description="Current progress percentage")
    error_message: Optional[str] = Field(None, description="Error message if the sync operation failed")


# Mock operation to simulate record processing
async def process_records(
    sync_id: str,
    entity_types: List[str],
    total_records: int,
    source_system: str,
    target_system: str,
    is_incremental: bool = False
) -> None:
    """
    Simulate processing records in a background task.
    
    Args:
        sync_id: ID of the sync operation
        entity_types: List of entity types being synced
        total_records: Total number of records to process
        source_system: Source system name
        target_system: Target system name
        is_incremental: Whether this is an incremental sync
    """
    try:
        # Start the sync operation
        start_sync_operation(sync_id)
        
        # Initialize metrics if they don't exist
        for entity_type in entity_types:
            # Create metrics for this entity type if they don't exist
            metric_labels = {
                'entity_type': entity_type,
                'source_system': source_system,
                'target_system': target_system
            }
            
            # Records processed counter
            create_counter(
                name=f"entity_{entity_type}_records_processed_total",
                description=f"Total {entity_type} records processed",
                initial_value=0,
                labels=metric_labels
            )
            
            # Records succeeded counter
            create_counter(
                name=f"entity_{entity_type}_records_succeeded_total",
                description=f"Total {entity_type} records succeeded",
                initial_value=0,
                labels=metric_labels
            )
            
            # Records failed counter
            create_counter(
                name=f"entity_{entity_type}_records_failed_total",
                description=f"Total {entity_type} records failed",
                initial_value=0,
                labels=metric_labels
            )
            
            # Processing time histogram
            create_histogram(
                name=f"entity_{entity_type}_processing_time_seconds",
                description=f"Time to process {entity_type} records",
                buckets=[0.001, 0.01, 0.1, 0.5, 1.0, 5.0, 10.0],
                labels=metric_labels
            )
        
        # Record overall metrics
        op_type = "incremental" if is_incremental else "full"
        op_labels = {
            'operation_type': op_type,
            'source_system': source_system,
            'target_system': target_system
        }
        
        # Sync operations counter
        create_counter(
            name="sync_operations_total",
            description="Total sync operations",
            initial_value=0,
            labels={**op_labels, 'status': 'started'}
        )
        increment_counter(
            name="sync_operations_total",
            labels={**op_labels, 'status': 'started'}
        )
        
        # Records counters
        create_counter(
            name="records_processed_total",
            description="Total records processed",
            initial_value=0,
            labels=op_labels
        )
        
        create_counter(
            name="records_succeeded_total",
            description="Total records succeeded",
            initial_value=0,
            labels=op_labels
        )
        
        create_counter(
            name="records_failed_total",
            description="Total records failed",
            initial_value=0,
            labels=op_labels
        )
        
        # Create sync duration histogram
        create_histogram(
            name="sync_duration_seconds",
            description="Sync operation duration in seconds",
            buckets=[1.0, 5.0, 15.0, 30.0, 60.0, 300.0, 600.0, 1800.0, 3600.0],
            labels=op_labels
        )
        
        # In a real implementation, this would fetch records from the source system
        # and process them batch by batch
        
        # For simulation, we'll just update progress periodically
        processed = 0
        succeeded = 0
        failed = 0
        
        batch_size = 10  # Process 10 records at a time
        
        while processed < total_records:
            # This would be actual record processing in a real implementation
            await asyncio.sleep(0.1)  # Simulate processing time
            
            # Update batch counts
            batch_processed = min(batch_size, total_records - processed)
            # Simulate some failures
            batch_succeeded = int(batch_processed * 0.95)  # 95% success rate
            batch_failed = batch_processed - batch_succeeded
            
            processed += batch_processed
            succeeded += batch_succeeded
            failed += batch_failed
            
            # Update metrics
            increment_counter("records_processed_total", batch_processed, op_labels)
            increment_counter("records_succeeded_total", batch_succeeded, op_labels)
            increment_counter("records_failed_total", batch_failed, op_labels)
            
            # Update entity metrics
            entities_per_batch = len(entity_types)
            for entity_type in entity_types:
                entity_batch_size = batch_processed // entities_per_batch
                entity_succeeded = int(entity_batch_size * 0.95)  # 95% success rate
                entity_failed = entity_batch_size - entity_succeeded
                
                metric_labels = {
                    'entity_type': entity_type,
                    'source_system': source_system,
                    'target_system': target_system
                }
                
                increment_counter(f"entity_{entity_type}_records_processed_total", entity_batch_size, metric_labels)
                increment_counter(f"entity_{entity_type}_records_succeeded_total", entity_succeeded, metric_labels)
                increment_counter(f"entity_{entity_type}_records_failed_total", entity_failed, metric_labels)
                
                # Simulate processing time
                observe_histogram(
                    f"entity_{entity_type}_processing_time_seconds",
                    0.05 + (0.1 * entity_batch_size / 10),  # Simulate variable processing time
                    metric_labels
                )
            
            # Update sync progress
            update_sync_progress(
                sync_id=sync_id,
                processed_records=processed,
                succeeded_records=succeeded,
                failed_records=failed
            )
        
        # Mark sync operation as completed
        complete_sync_operation(sync_id)
        
        # Record sync completion metrics
        increment_counter(
            name="sync_operations_total",
            labels={**op_labels, 'status': 'completed'}
        )
        
        # Record duration
        sync_op = get_sync_operation(sync_id)
        if sync_op and sync_op.duration_seconds is not None:
            observe_histogram(
                name="sync_duration_seconds",
                value=sync_op.duration_seconds,
                labels=op_labels
            )
        
    except Exception as e:
        logger.error(f"Error processing records for sync {sync_id}: {str(e)}")
        
        # Record sync failure metrics
        increment_counter(
            name="sync_operations_total",
            labels={**op_labels, 'status': 'failed'}
        )
        
        # Mark sync operation as failed
        fail_sync_operation(sync_id, str(e))


@router.post("/full", response_model=SyncResponse)
async def full_sync(
    request: FullSyncRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Trigger a full sync operation.
    
    This endpoint initiates a full sync operation between the specified source and target systems
    for the specified entity types. The sync operation will run in the background.
    
    Args:
        request: Full sync request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Sync operation details with ID and initial status
    """
    try:
        logger.info(
            f"Full sync requested: {request.source_system} -> {request.target_system}, "
            f"entities: {request.entity_types}"
        )
        
        # Create a new sync operation
        sync_op = create_sync_operation(
            sync_type=SyncType.FULL,
            source_system=request.source_system,
            target_system=request.target_system,
            entity_types=request.entity_types,
            filter_criteria=request.filter_criteria or {},
            total_records=100  # This would be determined by querying the source system
        )
        
        # Start the sync operation in the background
        background_tasks.add_task(
            process_records,
            sync_id=sync_op.sync_id,
            entity_types=request.entity_types,
            total_records=100,
            source_system=request.source_system,
            target_system=request.target_system,
            is_incremental=False
        )
        
        return {
            "sync_id": sync_op.sync_id,
            "status": sync_op.status,
            "message": f"Full sync operation started between {request.source_system} and {request.target_system}"
        }
    except Exception as e:
        logger.error(f"Error starting full sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.post("/incremental", response_model=SyncResponse)
async def incremental_sync(
    request: IncrementalSyncRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Trigger an incremental sync operation.
    
    This endpoint initiates an incremental sync operation between the specified source and target systems
    for the specified entity types, syncing only records that have changed since the specified timestamp.
    The sync operation will run in the background.
    
    Args:
        request: Incremental sync request parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Sync operation details with ID and initial status
    """
    try:
        # Default to 24 hours ago if since is not provided
        since = request.since or (datetime.now() - timedelta(hours=24))
        
        logger.info(
            f"Incremental sync requested: {request.source_system} -> {request.target_system}, "
            f"entities: {request.entity_types}, since: {since.isoformat()}"
        )
        
        # Create a new sync operation
        sync_op = create_sync_operation(
            sync_type=SyncType.INCREMENTAL,
            source_system=request.source_system,
            target_system=request.target_system,
            entity_types=request.entity_types,
            filter_criteria={
                **(request.filter_criteria or {}),
                "since": since.isoformat()
            },
            total_records=50  # This would be determined by querying the source system
        )
        
        # Start the sync operation in the background
        background_tasks.add_task(
            process_records,
            sync_id=sync_op.sync_id,
            entity_types=request.entity_types,
            total_records=50,
            source_system=request.source_system,
            target_system=request.target_system,
            is_incremental=True
        )
        
        return {
            "sync_id": sync_op.sync_id,
            "status": sync_op.status,
            "message": f"Incremental sync operation started between {request.source_system} and {request.target_system}"
        }
    except Exception as e:
        logger.error(f"Error starting incremental sync: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start sync: {str(e)}")


@router.get("/status/{sync_id}", response_model=SyncStatusResponse)
async def get_sync_status(
    sync_id: str = Path(..., description="ID of the sync operation")
) -> Dict[str, Any]:
    """
    Get the status of a sync operation.
    
    This endpoint retrieves the current status of a sync operation.
    
    Args:
        sync_id: ID of the sync operation
        
    Returns:
        Current status of the sync operation
    """
    sync_op = get_sync_operation(sync_id)
    
    if not sync_op:
        raise HTTPException(status_code=404, detail=f"Sync operation {sync_id} not found")
    
    return sync_op.to_dict()


@router.post("/cancel/{sync_id}", response_model=SyncResponse)
async def cancel_sync(
    sync_id: str = Path(..., description="ID of the sync operation to cancel")
) -> Dict[str, Any]:
    """
    Cancel a sync operation.
    
    This endpoint cancels an in-progress sync operation.
    
    Args:
        sync_id: ID of the sync operation to cancel
        
    Returns:
        Result of the cancel operation
    """
    sync_op = get_sync_operation(sync_id)
    
    if not sync_op:
        raise HTTPException(status_code=404, detail=f"Sync operation {sync_id} not found")
    
    if sync_op.status not in (SyncStatus.PENDING, SyncStatus.RUNNING):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel sync operation in status: {sync_op.status}"
        )
    
    # Cancel the sync operation
    cancel_sync_operation(sync_id)
    
    return {
        "sync_id": sync_id,
        "status": "canceled",
        "message": f"Sync operation {sync_id} has been canceled"
    }


@router.get("/active", response_model=List[SyncStatusResponse])
async def get_active_syncs() -> List[Dict[str, Any]]:
    """
    Get all active sync operations.
    
    This endpoint retrieves all active (pending or running) sync operations.
    
    Returns:
        List of active sync operations
    """
    active_syncs = get_active_sync_operations()
    return [sync_op.to_dict() for sync_op in active_syncs]