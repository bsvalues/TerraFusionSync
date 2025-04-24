"""
Synchronization API for the SyncService.

This module defines the API endpoints for managing synchronization operations.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator

from ..models.base import SyncType, SyncStatus, SyncOperation, SyncOperationDetails
from ..core.sync_engine import SyncEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


class StartSyncRequest(BaseModel):
    """Request model for starting a sync operation."""
    sync_pair_id: str
    sync_type: SyncType
    entity_types: List[str]
    incremental_hours: Optional[int] = None
    
    @validator('incremental_hours')
    def validate_incremental_hours(cls, v, values):
        """Validate that incremental_hours is provided for incremental syncs."""
        if values.get('sync_type') == SyncType.INCREMENTAL and v is None:
            raise ValueError('incremental_hours is required for incremental syncs')
        return v


class SyncOperationResponse(BaseModel):
    """Response model for sync operations."""
    operation_id: str
    sync_pair_id: str
    sync_type: SyncType
    entity_types: List[str]
    status: SyncStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Dependency to get the sync engine
async def get_sync_engine():
    """Dependency to get the sync engine instance."""
    # This would normally retrieve the engine from a dependency container
    # For now, returning None as a placeholder
    return None


@router.post("/start", response_model=SyncOperationResponse)
async def start_sync(
    request: StartSyncRequest,
    sync_engine: Optional[SyncEngine] = Depends(get_sync_engine)
):
    """
    Start a synchronization operation.
    
    Args:
        request: Request containing sync parameters
        sync_engine: Sync engine instance from dependency
        
    Returns:
        Response containing the created sync operation
    """
    if sync_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Sync engine is not available"
        )
    
    try:
        # Generate an operation ID
        operation_id = f"{request.sync_type.value}-{uuid4()}"
        
        logger.info(f"Starting {request.sync_type.value} sync operation {operation_id} "
                    f"for pair {request.sync_pair_id}")
        
        # Determine since date for incremental syncs
        since = None
        if request.sync_type == SyncType.INCREMENTAL:
            since = datetime.utcnow() - timedelta(hours=request.incremental_hours)
        
        # Start the sync operation
        if request.sync_type == SyncType.FULL:
            sync_op = await sync_engine.perform_full_sync(
                sync_pair_id=request.sync_pair_id,
                entity_types=request.entity_types,
                operation_id=operation_id
            )
        else:
            if since is None:
                raise HTTPException(
                    status_code=400,
                    detail="Since date is required for incremental syncs"
                )
            
            sync_op = await sync_engine.perform_incremental_sync(
                sync_pair_id=request.sync_pair_id,
                entity_types=request.entity_types,
                since=since,
                operation_id=operation_id
            )
        
        # Convert to response model
        response = SyncOperationResponse(
            operation_id=sync_op.id,
            sync_pair_id=sync_op.sync_pair_id,
            sync_type=sync_op.sync_type,
            entity_types=sync_op.entity_types,
            status=sync_op.status,
            start_time=sync_op.start_time,
            end_time=sync_op.end_time,
            details=sync_op.details.dict() if sync_op.details else None,
            error=sync_op.error
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error starting sync operation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error starting sync operation: {str(e)}"
        )


@router.get("/operations", response_model=List[SyncOperationResponse])
async def get_sync_operations(
    sync_pair_id: Optional[str] = Query(None),
    sync_type: Optional[SyncType] = Query(None),
    status: Optional[SyncStatus] = Query(None),
    limit: int = Query(10, gt=0, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get a list of sync operations.
    
    Args:
        sync_pair_id: Optional filter by sync pair ID
        sync_type: Optional filter by sync type
        status: Optional filter by status
        limit: Maximum number of operations to return
        offset: Starting offset for pagination
        
    Returns:
        List of sync operations
    """
    # This would normally query the database for sync operations
    # For now, returning an empty list as a placeholder
    return []


@router.get("/operations/{operation_id}", response_model=SyncOperationResponse)
async def get_sync_operation(operation_id: str):
    """
    Get details for a specific sync operation.
    
    Args:
        operation_id: ID of the sync operation
        
    Returns:
        Sync operation details
    """
    # This would normally query the database for the sync operation
    # For now, raising a not found exception
    raise HTTPException(
        status_code=404,
        detail=f"Sync operation {operation_id} not found"
    )


@router.post("/operations/{operation_id}/cancel")
async def cancel_sync_operation(
    operation_id: str,
    sync_engine: Optional[SyncEngine] = Depends(get_sync_engine)
):
    """
    Cancel a running sync operation.
    
    Args:
        operation_id: ID of the sync operation to cancel
        sync_engine: Sync engine instance from dependency
        
    Returns:
        Success message
    """
    if sync_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Sync engine is not available"
        )
    
    # This would normally attempt to cancel the operation
    # For now, returning a success message
    return {"message": f"Sync operation {operation_id} canceled"}


@router.get("/pairs", response_model=List[Dict[str, Any]])
async def get_sync_pairs():
    """
    Get a list of sync pairs.
    
    Returns:
        List of sync pairs
    """
    # This would normally query the database for sync pairs
    # For now, returning an empty list as a placeholder
    return []


@router.get("/pairs/{sync_pair_id}")
async def get_sync_pair(sync_pair_id: str):
    """
    Get details for a specific sync pair.
    
    Args:
        sync_pair_id: ID of the sync pair
        
    Returns:
        Sync pair details
    """
    # This would normally query the database for the sync pair
    # For now, raising a not found exception
    raise HTTPException(
        status_code=404,
        detail=f"Sync pair {sync_pair_id} not found"
    )