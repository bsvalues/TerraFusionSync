"""
Sync API for the SyncService.

This module defines the API endpoints for managing sync operations.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from ..monitoring.sync_tracker import SyncTracker, SyncStatus, SyncType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


# Dependency to get the sync tracker
async def get_sync_tracker():
    """Dependency to get the sync tracker instance."""
    # In a real implementation, this would retrieve the tracker from a dependency container
    # For now, returning None as a placeholder
    return None


class FullSyncRequest(BaseModel):
    """Request model for starting a full sync."""
    sync_pair_id: str = Field(..., description="ID of the sync pair to sync")
    entity_types: List[str] = Field(default=["property", "owner"], description="Types of entities to sync")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters for the sync operation")


class IncrementalSyncRequest(BaseModel):
    """Request model for starting an incremental sync."""
    sync_pair_id: str = Field(..., description="ID of the sync pair to sync")
    entity_types: List[str] = Field(default=["property", "owner"], description="Types of entities to sync")
    hours: Optional[int] = Field(default=24, description="Number of hours to look back for changes")
    params: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters for the sync operation")


@router.post("/full")
async def start_full_sync(
    request: FullSyncRequest,
    sync_tracker: Optional[SyncTracker] = Depends(get_sync_tracker)
):
    """
    Start a full sync operation.
    
    Args:
        request: Sync request parameters
        sync_tracker: Sync tracker instance from dependency
        
    Returns:
        Dictionary with operation details
    """
    if not sync_tracker:
        # For development, return a mock operation
        operation_id = f"mock-full-{uuid.uuid4().hex[:8]}"
        
        return {
            "id": operation_id,
            "sync_pair_id": request.sync_pair_id,
            "sync_type": SyncType.FULL,
            "status": SyncStatus.RUNNING,
            "start_time": datetime.utcnow().isoformat(),
            "entity_types": request.entity_types,
            "message": "Sync operation started in mock mode"
        }
    
    # Generate a unique ID for this operation
    operation_id = f"full-{uuid.uuid4().hex[:8]}"
    
    # Start tracking the operation
    operation = await sync_tracker.start_operation(
        operation_id=operation_id,
        sync_pair_id=request.sync_pair_id,
        sync_type=SyncType.FULL,
        entity_types=request.entity_types,
        parameters=request.params
    )
    
    # Start the sync in the background
    asyncio.create_task(_run_full_sync(operation_id, request.sync_pair_id, request.entity_types, request.params, sync_tracker))
    
    return {
        "id": operation["id"],
        "sync_pair_id": operation["sync_pair_id"],
        "sync_type": operation["sync_type"],
        "status": operation["status"],
        "start_time": operation["start_time"],
        "entity_types": operation["entity_types"],
        "message": "Sync operation started"
    }


@router.post("/incremental")
async def start_incremental_sync(
    request: IncrementalSyncRequest,
    sync_tracker: Optional[SyncTracker] = Depends(get_sync_tracker)
):
    """
    Start an incremental sync operation.
    
    Args:
        request: Sync request parameters
        sync_tracker: Sync tracker instance from dependency
        
    Returns:
        Dictionary with operation details
    """
    if not sync_tracker:
        # For development, return a mock operation
        operation_id = f"mock-incremental-{uuid.uuid4().hex[:8]}"
        
        return {
            "id": operation_id,
            "sync_pair_id": request.sync_pair_id,
            "sync_type": SyncType.INCREMENTAL,
            "status": SyncStatus.RUNNING,
            "start_time": datetime.utcnow().isoformat(),
            "entity_types": request.entity_types,
            "hours": request.hours,
            "message": "Sync operation started in mock mode"
        }
    
    # Generate a unique ID for this operation
    operation_id = f"incremental-{uuid.uuid4().hex[:8]}"
    
    # Start tracking the operation
    params = request.params or {}
    params["hours"] = request.hours
    
    operation = await sync_tracker.start_operation(
        operation_id=operation_id,
        sync_pair_id=request.sync_pair_id,
        sync_type=SyncType.INCREMENTAL,
        entity_types=request.entity_types,
        parameters=params
    )
    
    # Start the sync in the background
    asyncio.create_task(_run_incremental_sync(operation_id, request.sync_pair_id, request.entity_types, request.hours, params, sync_tracker))
    
    return {
        "id": operation["id"],
        "sync_pair_id": operation["sync_pair_id"],
        "sync_type": operation["sync_type"],
        "status": operation["status"],
        "start_time": operation["start_time"],
        "entity_types": operation["entity_types"],
        "hours": request.hours,
        "message": "Sync operation started"
    }


@router.get("/status/{operation_id}")
async def get_sync_status(
    operation_id: str,
    sync_tracker: Optional[SyncTracker] = Depends(get_sync_tracker)
):
    """
    Get the status of a sync operation.
    
    Args:
        operation_id: ID of the operation
        sync_tracker: Sync tracker instance from dependency
        
    Returns:
        Dictionary with operation status
    """
    if not sync_tracker:
        # For development, return a mock operation
        if operation_id.startswith("mock-"):
            status = SyncStatus.COMPLETED if datetime.utcnow().second % 2 == 0 else SyncStatus.RUNNING
            end_time = datetime.utcnow() if status == SyncStatus.COMPLETED else None
            
            return {
                "id": operation_id,
                "status": status,
                "progress": 75 if status == SyncStatus.RUNNING else 100,
                "start_time": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "end_time": end_time.isoformat() if end_time else None,
                "duration_seconds": 300 if status == SyncStatus.COMPLETED else None,
                "records_processed": 1250,
                "records_succeeded": 1200,
                "records_failed": 50,
                "message": "Mock operation status"
            }
        else:
            raise HTTPException(status_code=404, detail="Operation not found")
    
    # Find the operation in active operations
    active_operations = await sync_tracker.get_active_operations()
    for op in active_operations:
        if op["id"] == operation_id:
            return op
    
    # If not active, get from completed operations
    operations = await sync_tracker.get_operations(
        limit=1,
        offset=0
    )
    
    for op in operations:
        if op["id"] == operation_id:
            return op
    
    # If not found at all
    raise HTTPException(status_code=404, detail="Operation not found")


@router.post("/cancel/{operation_id}")
async def cancel_sync_operation(
    operation_id: str,
    sync_tracker: Optional[SyncTracker] = Depends(get_sync_tracker)
):
    """
    Cancel a sync operation.
    
    Args:
        operation_id: ID of the operation
        sync_tracker: Sync tracker instance from dependency
        
    Returns:
        Dictionary with operation status
    """
    if not sync_tracker:
        # For development, return a mock response
        if operation_id.startswith("mock-"):
            return {
                "id": operation_id,
                "status": SyncStatus.CANCELLED,
                "message": "Operation cancelled in mock mode"
            }
        else:
            raise HTTPException(status_code=404, detail="Operation not found")
    
    # Update the operation status to cancelled
    operation = await sync_tracker.update_operation(
        operation_id=operation_id,
        status=SyncStatus.CANCELLED
    )
    
    if not operation:
        raise HTTPException(status_code=404, detail="Operation not found")
    
    return {
        "id": operation["id"],
        "status": operation["status"],
        "message": "Operation cancelled"
    }


async def _run_full_sync(
    operation_id: str,
    sync_pair_id: str,
    entity_types: List[str],
    params: Optional[Dict[str, Any]],
    sync_tracker: SyncTracker
):
    """
    Run a full sync operation in the background.
    
    Args:
        operation_id: ID of the operation
        sync_pair_id: ID of the sync pair
        entity_types: Types of entities to sync
        params: Additional parameters
        sync_tracker: Sync tracker instance
    """
    try:
        # In a real implementation, this would call the sync engine
        logger.info(f"Starting full sync for operation {operation_id}")
        
        # Simulate processing time
        await asyncio.sleep(10)
        
        # Update the operation with success status
        await sync_tracker.complete_operation(
            operation_id=operation_id,
            success=True,
            records_processed=1250,
            records_succeeded=1200,
            records_failed=50,
            results={
                "property": {
                    "processed": 750,
                    "succeeded": 725,
                    "failed": 25
                },
                "owner": {
                    "processed": 500,
                    "succeeded": 475,
                    "failed": 25
                }
            }
        )
        
        logger.info(f"Completed full sync for operation {operation_id}")
        
    except Exception as e:
        logger.error(f"Error in full sync operation {operation_id}: {str(e)}", exc_info=True)
        
        # Update the operation with failure status
        await sync_tracker.complete_operation(
            operation_id=operation_id,
            success=False,
            error_message=str(e)
        )


async def _run_incremental_sync(
    operation_id: str,
    sync_pair_id: str,
    entity_types: List[str],
    hours: int,
    params: Optional[Dict[str, Any]],
    sync_tracker: SyncTracker
):
    """
    Run an incremental sync operation in the background.
    
    Args:
        operation_id: ID of the operation
        sync_pair_id: ID of the sync pair
        entity_types: Types of entities to sync
        hours: Number of hours to look back
        params: Additional parameters
        sync_tracker: Sync tracker instance
    """
    try:
        # In a real implementation, this would call the sync engine
        logger.info(f"Starting incremental sync for operation {operation_id} (last {hours} hours)")
        
        # Simulate processing time
        await asyncio.sleep(5)
        
        # Update the operation with success status
        await sync_tracker.complete_operation(
            operation_id=operation_id,
            success=True,
            records_processed=250,
            records_succeeded=245,
            records_failed=5,
            results={
                "property": {
                    "processed": 150,
                    "succeeded": 148,
                    "failed": 2
                },
                "owner": {
                    "processed": 100,
                    "succeeded": 97,
                    "failed": 3
                }
            }
        )
        
        logger.info(f"Completed incremental sync for operation {operation_id}")
        
    except Exception as e:
        logger.error(f"Error in incremental sync operation {operation_id}: {str(e)}", exc_info=True)
        
        # Update the operation with failure status
        await sync_tracker.complete_operation(
            operation_id=operation_id,
            success=False,
            error_message=str(e)
        )