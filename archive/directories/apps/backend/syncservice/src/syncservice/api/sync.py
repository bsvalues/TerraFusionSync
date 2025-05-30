"""
Sync API endpoints for the SyncService.

This module implements the endpoints for triggering sync operations.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from syncservice.components.change_detector import ChangeDetector
from syncservice.components.self_healing import SelfHealingOrchestrator
from syncservice.components.transformer import Transformer
from syncservice.components.validator import Validator
from syncservice.models.base import SyncResult
from syncservice.utils.database import check_source_connection, check_target_connection
from syncservice.utils.event_bus import check_nats_connection, publish_event

logger = logging.getLogger(__name__)

router = APIRouter()


class SyncRequest(BaseModel):
    """Request model for sync operations."""
    
    since: Optional[datetime] = Field(
        default=None, 
        description="Timestamp to sync changes since. If not provided, defaults to 24 hours ago"
    )
    limit: Optional[int] = Field(
        default=1000, 
        description="Maximum number of records to process"
    )
    options: Optional[Dict] = Field(
        default=None,
        description="Additional options for the sync operation"
    )


@router.post("/full", response_model=SyncResult, status_code=status.HTTP_202_ACCEPTED)
async def full_sync(
    background_tasks: BackgroundTasks,
    request: Optional[SyncRequest] = None
) -> SyncResult:
    """
    Trigger a full sync of all data from source to target system.
    
    This is a potentially long-running operation that will be executed in the background.
    
    Args:
        background_tasks: FastAPI background tasks
        request: Optional sync request parameters
        
    Returns:
        SyncResult indicating the operation has been queued
    """
    # First check connections
    if not await check_dependencies():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies (database, messaging) are not available"
        )
    
    # Create operation ID
    operation_id = str(uuid.uuid4())
    
    # Log the request
    logger.info(f"Full sync operation requested, ID: {operation_id}")
    
    # Initialize sync components
    detector = ChangeDetector()
    transformer = Transformer()
    validator = Validator()
    orchestrator = SelfHealingOrchestrator()
    
    # Add sync task to background tasks
    background_tasks.add_task(
        _run_full_sync,
        orchestrator=orchestrator,
        detector=detector,
        transformer=transformer,
        validator=validator,
        operation_id=operation_id,
        options=request.options if request else None
    )
    
    # Publish event that sync was requested
    await publish_event(
        "full_sync_requested",
        {
            "operation_id": operation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "options": request.options if request and request.options else {}
        }
    )
    
    # Return immediate response
    return SyncResult(
        success=True,
        count=0,
        timestamp=datetime.utcnow(),
        details={
            "operation_id": operation_id,
            "status": "queued",
            "message": "Full sync operation has been queued and will run in the background"
        }
    )


@router.post("/incremental", response_model=SyncResult, status_code=status.HTTP_202_ACCEPTED)
async def incremental_sync(
    background_tasks: BackgroundTasks,
    request: Optional[SyncRequest] = None
) -> SyncResult:
    """
    Trigger an incremental sync of changed data from source to target system.
    
    This operation syncs only data that has changed since the specified time.
    
    Args:
        background_tasks: FastAPI background tasks
        request: Optional sync request parameters
        
    Returns:
        SyncResult indicating the operation has been queued
    """
    # First check connections
    if not await check_dependencies():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service dependencies (database, messaging) are not available"
        )
    
    # Create operation ID
    operation_id = str(uuid.uuid4())
    
    # Get since timestamp from request or default to 24 hours ago
    since = None
    if request and request.since:
        since = request.since
    else:
        since = datetime.utcnow() - timedelta(hours=24)
    
    # Log the request
    logger.info(f"Incremental sync operation requested, ID: {operation_id}, since: {since}")
    
    # Initialize sync components
    detector = ChangeDetector()
    transformer = Transformer()
    validator = Validator()
    orchestrator = SelfHealingOrchestrator()
    
    # Add sync task to background tasks
    background_tasks.add_task(
        _run_incremental_sync,
        orchestrator=orchestrator,
        detector=detector,
        transformer=transformer,
        validator=validator,
        operation_id=operation_id,
        since=since,
        limit=request.limit if request and request.limit else 1000,
        options=request.options if request and request.options else None
    )
    
    # Publish event that sync was requested
    await publish_event(
        "incremental_sync_requested",
        {
            "operation_id": operation_id,
            "timestamp": datetime.utcnow().isoformat(),
            "since": since.isoformat(),
            "limit": request.limit if request and request.limit else 1000,
            "options": request.options if request and request.options else {}
        }
    )
    
    # Return immediate response
    return SyncResult(
        success=True,
        count=0,
        timestamp=datetime.utcnow(),
        details={
            "operation_id": operation_id,
            "status": "queued",
            "since": since.isoformat(),
            "message": "Incremental sync operation has been queued and will run in the background"
        }
    )


@router.get("/status/{operation_id}", status_code=status.HTTP_200_OK)
async def sync_status(operation_id: str) -> Dict:
    """
    Check the status of a sync operation.
    
    Args:
        operation_id: ID of the sync operation to check
        
    Returns:
        Status information for the operation
    """
    # This is a placeholder - in a real implementation, this would query a status
    # tracking system (database, Redis, etc.) to get the current status
    
    # For now, just return a mock response
    return {
        "operation_id": operation_id,
        "status": "unknown",
        "message": "Operation status tracking is not implemented yet"
    }


async def _run_full_sync(
    orchestrator: SelfHealingOrchestrator,
    detector: ChangeDetector,
    transformer: Transformer,
    validator: Validator,
    operation_id: str,
    options: Optional[Dict] = None
) -> None:
    """
    Run a full sync operation in the background.
    
    Args:
        orchestrator: SelfHealingOrchestrator instance
        detector: ChangeDetector instance
        transformer: Transformer instance
        validator: Validator instance
        operation_id: Unique operation ID
        options: Additional options for the sync operation
    """
    logger.info(f"Starting full sync operation: {operation_id}")
    
    try:
        # Run the sync pipeline
        result = await orchestrator.run_sync_pipeline(
            detector=detector,
            transformer=transformer,
            validator=validator,
            is_full_sync=True
        )
        
        logger.info(f"Full sync operation completed: {operation_id}, result: {result}")
        
        # Publish completion event
        await publish_event(
            "full_sync_completed",
            {
                "operation_id": operation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "result": result
            }
        )
    
    except Exception as e:
        logger.error(f"Error in full sync operation {operation_id}: {str(e)}", exc_info=True)
        
        # Publish failure event
        await publish_event(
            "full_sync_failed",
            {
                "operation_id": operation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


async def _run_incremental_sync(
    orchestrator: SelfHealingOrchestrator,
    detector: ChangeDetector,
    transformer: Transformer,
    validator: Validator,
    operation_id: str,
    since: datetime,
    limit: int = 1000,
    options: Optional[Dict] = None
) -> None:
    """
    Run an incremental sync operation in the background.
    
    Args:
        orchestrator: SelfHealingOrchestrator instance
        detector: ChangeDetector instance
        transformer: Transformer instance
        validator: Validator instance
        operation_id: Unique operation ID
        since: Timestamp to sync changes since
        limit: Maximum number of records to process
        options: Additional options for the sync operation
    """
    logger.info(f"Starting incremental sync operation: {operation_id}, since: {since}")
    
    try:
        # Run the sync pipeline
        result = await orchestrator.run_sync_pipeline(
            detector=detector,
            transformer=transformer,
            validator=validator,
            since=since,
            is_full_sync=False
        )
        
        logger.info(f"Incremental sync operation completed: {operation_id}, result: {result}")
        
        # Publish completion event
        await publish_event(
            "incremental_sync_completed",
            {
                "operation_id": operation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "since": since.isoformat(),
                "result": result
            }
        )
    
    except Exception as e:
        logger.error(f"Error in incremental sync operation {operation_id}: {str(e)}", exc_info=True)
        
        # Publish failure event
        await publish_event(
            "incremental_sync_failed",
            {
                "operation_id": operation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "since": since.isoformat(),
                "error": str(e)
            }
        )


async def check_dependencies() -> bool:
    """
    Check if all dependencies (databases, NATS) are available.
    
    Returns:
        True if all dependencies are available, False otherwise
    """
    # Check source database
    source_db_ok = await check_source_connection()
    
    # Check target database
    target_db_ok = await check_target_connection()
    
    # Check NATS
    nats_ok = await check_nats_connection()
    
    # All checks must pass
    return source_db_ok and target_db_ok and nats_ok
