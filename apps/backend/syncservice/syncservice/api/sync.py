"""
Sync endpoints for the SyncService.

This module implements full and incremental sync endpoints with support for
various source and target system types.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Path, Depends
from pydantic import BaseModel, Field

from syncservice.config.system_config import (
    get_sync_config, get_sync_pair_config, get_source_system_config, get_target_system_config
)
from syncservice.adapters import (
    get_source_adapter_class, get_target_adapter_class
)

# Configure router
router = APIRouter()

# Mock storage for sync jobs
sync_jobs = {}


class SyncRequest(BaseModel):
    """Request schema for sync operations."""
    
    pair_id: Optional[str] = Field(
        default=None, 
        description="ID of the sync pair to use (default: all enabled pairs)"
    )
    batch_size: Optional[int] = Field(
        default=100, 
        description="Number of records to process in each batch"
    )
    timeout_seconds: Optional[int] = Field(
        default=3600, 
        description="Maximum time in seconds to run the sync operation"
    )
    initiated_by: Optional[str] = Field(
        default=None, 
        description="Identifier of the user or process that initiated the sync"
    )
    since: Optional[datetime] = Field(
        default=None, 
        description="For incremental sync, the timestamp to start from (default: 24 hours ago)"
    )
    entity_types: Optional[List[str]] = Field(
        default=None, 
        description="List of entity types to sync (default: all available types in the sync pair)"
    )


class SyncResponse(BaseModel):
    """Response schema for sync operations."""
    
    job_id: str = Field(..., description="Unique identifier for the sync job")
    status: str = Field(..., description="Status of the sync job (pending, in_progress, completed, failed)")
    timestamp: datetime = Field(..., description="Timestamp when the job was created")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional details about the job")


@router.post("/full", response_model=SyncResponse)
async def run_full_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Start a full sync operation.
    
    This endpoint initiates a complete data sync from the source system to the target.
    It returns immediately with a job ID, and the sync continues in the background.
    
    Args:
        request: Parameters for the sync operation
        background_tasks: FastAPI background tasks
        
    Returns:
        Job status information
    """
    job_id = f"full-sync-{datetime.utcnow().isoformat()}"
    
    # Store job details
    sync_jobs[job_id] = {
        "status": "pending",
        "timestamp": datetime.utcnow(),
        "type": "full",
        "params": request.dict(),
        "details": {
            "pair_id": request.pair_id,
            "initiated_by": request.initiated_by
        }
    }
    
    # Queue the background task
    background_tasks.add_task(_run_full_sync, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "timestamp": datetime.utcnow(),
        "details": {
            "pair_id": request.pair_id,
            "message": "Full sync job has been queued and will run in the background"
        }
    }


@router.post("/incremental", response_model=SyncResponse)
async def run_incremental_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
) -> Dict:
    """
    Start an incremental sync operation.
    
    This endpoint initiates a sync of changes that occurred since the last successful sync.
    It returns immediately with a job ID, and the sync continues in the background.
    
    Args:
        request: Parameters for the sync operation
        background_tasks: FastAPI background tasks
        
    Returns:
        Job status information
    """
    job_id = f"incremental-sync-{datetime.utcnow().isoformat()}"
    
    # Store job details
    sync_jobs[job_id] = {
        "status": "pending",
        "timestamp": datetime.utcnow(),
        "type": "incremental",
        "params": request.dict(),
        "details": {
            "pair_id": request.pair_id,
            "initiated_by": request.initiated_by,
            "since": request.since
        }
    }
    
    # Queue the background task
    background_tasks.add_task(_run_incremental_sync, job_id, request)
    
    return {
        "job_id": job_id,
        "status": "pending",
        "timestamp": datetime.utcnow(),
        "details": {
            "pair_id": request.pair_id,
            "message": "Incremental sync job has been queued and will run in the background"
        }
    }


@router.get("/status/{job_id}", response_model=SyncResponse)
async def get_sync_status(job_id: str = Path(..., description="ID of the sync job to check")) -> Dict:
    """
    Get the status of a sync job.
    
    Args:
        job_id: The ID of the sync job to check
        
    Returns:
        Current job status
    """
    if job_id not in sync_jobs:
        raise HTTPException(status_code=404, detail=f"Sync job {job_id} not found")
    
    job = sync_jobs[job_id]
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "timestamp": job["timestamp"],
        "details": job.get("details")
    }


# Background task implementations
async def _run_full_sync(job_id: str, request: SyncRequest) -> None:
    """Run a full sync operation in the background."""
    try:
        # Update job status
        sync_jobs[job_id]["status"] = "in_progress"
        
        # Get sync pairs to process
        pairs_to_process = []
        if request.pair_id:
            # Process a specific pair
            pair_config = get_sync_pair_config(request.pair_id)
            if not pair_config:
                raise ValueError(f"Sync pair {request.pair_id} not found")
            if not pair_config.is_enabled:
                raise ValueError(f"Sync pair {request.pair_id} is disabled")
            pairs_to_process.append(pair_config)
        else:
            # Process all enabled pairs
            config = get_sync_config()
            pairs_to_process = [
                pair for pair in config.sync_pairs.values() 
                if pair.is_enabled
            ]
        
        if not pairs_to_process:
            raise ValueError("No enabled sync pairs found")
        
        total_records_processed = 0
        total_records_succeeded = 0
        total_records_failed = 0
        
        # Process each sync pair
        for pair in pairs_to_process:
            # Get source and target system configs
            source_config = get_source_system_config(pair.source_system)
            if not source_config or not source_config.is_enabled:
                continue
                
            target_config = get_target_system_config(pair.target_system)
            if not target_config or not target_config.is_enabled:
                continue
            
            # Get entity types to process
            entity_types = request.entity_types or list(pair.entity_mappings.keys())
            
            # Create source and target adapters
            source_adapter_class = get_source_adapter_class(source_config.system_type)
            if not source_adapter_class:
                continue
                
            target_adapter_class = get_target_adapter_class(target_config.system_type)
            if not target_adapter_class:
                continue
            
            source_adapter = source_adapter_class(source_config.connection_params)
            target_adapter = target_adapter_class(target_config.connection_params)
            
            # Connect to source and target systems
            source_connected = await source_adapter.connect()
            if not source_connected:
                continue
                
            target_connected = await target_adapter.connect()
            if not target_connected:
                await source_adapter.disconnect()
                continue
            
            # Process each entity type
            for source_entity_type in entity_types:
                if source_entity_type not in pair.entity_mappings:
                    continue
                    
                target_entity_type = pair.entity_mappings[source_entity_type]
                
                # Get records from source system
                source_records = await source_adapter.get_all_records(
                    source_entity_type,
                    batch_size=request.batch_size
                )
                
                if not source_records:
                    continue
                
                # Here in a real implementation, we would:
                # 1. Transform the records according to field mapping
                # 2. Validate the records
                # 3. Write them to the target system
                # 4. Handle any conflicts
                
                # For now, we'll just simulate a successful write
                records_count = len(source_records)
                success_count, failed_records = await target_adapter.write_records(
                    target_entity_type,
                    source_records
                )
                
                total_records_processed += records_count
                total_records_succeeded += success_count
                total_records_failed += len(failed_records)
            
            # Disconnect from source and target systems
            await source_adapter.disconnect()
            await target_adapter.disconnect()
        
        # Update job status
        sync_jobs[job_id]["status"] = "completed"
        sync_jobs[job_id]["details"] = {
            "records_processed": total_records_processed,
            "records_succeeded": total_records_succeeded,
            "records_failed": total_records_failed,
            "pairs_processed": len(pairs_to_process),
            "completion_time": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - sync_jobs[job_id]["timestamp"]).total_seconds()
        }
        
    except Exception as e:
        # Update job status on failure
        sync_jobs[job_id]["status"] = "failed"
        sync_jobs[job_id]["details"] = {
            "error": str(e),
            "failure_time": datetime.utcnow().isoformat()
        }


async def _run_incremental_sync(job_id: str, request: SyncRequest) -> None:
    """Run an incremental sync operation in the background."""
    try:
        # Update job status
        sync_jobs[job_id]["status"] = "in_progress"
        
        # Get sync pairs to process
        pairs_to_process = []
        if request.pair_id:
            # Process a specific pair
            pair_config = get_sync_pair_config(request.pair_id)
            if not pair_config:
                raise ValueError(f"Sync pair {request.pair_id} not found")
            if not pair_config.is_enabled:
                raise ValueError(f"Sync pair {request.pair_id} is disabled")
            pairs_to_process.append(pair_config)
        else:
            # Process all enabled pairs
            config = get_sync_config()
            pairs_to_process = [
                pair for pair in config.sync_pairs.values() 
                if pair.is_enabled
            ]
        
        if not pairs_to_process:
            raise ValueError("No enabled sync pairs found")
        
        # Default to 24 hours ago if no since timestamp provided
        since = request.since or (datetime.utcnow() - timedelta(hours=24))
        
        total_records_processed = 0
        total_records_succeeded = 0
        total_records_failed = 0
        
        # Process each sync pair
        for pair in pairs_to_process:
            # Get source and target system configs
            source_config = get_source_system_config(pair.source_system)
            if not source_config or not source_config.is_enabled:
                continue
                
            target_config = get_target_system_config(pair.target_system)
            if not target_config or not target_config.is_enabled:
                continue
            
            # Get entity types to process
            entity_types = request.entity_types or list(pair.entity_mappings.keys())
            
            # Create source and target adapters
            source_adapter_class = get_source_adapter_class(source_config.system_type)
            if not source_adapter_class:
                continue
                
            target_adapter_class = get_target_adapter_class(target_config.system_type)
            if not target_adapter_class:
                continue
            
            source_adapter = source_adapter_class(source_config.connection_params)
            target_adapter = target_adapter_class(target_config.connection_params)
            
            # Connect to source and target systems
            source_connected = await source_adapter.connect()
            if not source_connected:
                continue
                
            target_connected = await target_adapter.connect()
            if not target_connected:
                await source_adapter.disconnect()
                continue
            
            # Process each entity type
            for source_entity_type in entity_types:
                if source_entity_type not in pair.entity_mappings:
                    continue
                    
                target_entity_type = pair.entity_mappings[source_entity_type]
                
                # Get changed records from source system
                changed_records = await source_adapter.get_changed_records(
                    source_entity_type,
                    since=since,
                    batch_size=request.batch_size
                )
                
                if not changed_records:
                    continue
                
                # Here in a real implementation, we would:
                # 1. Transform the records according to field mapping
                # 2. Validate the records
                # 3. Write them to the target system
                # 4. Handle any conflicts
                
                # For now, we'll just simulate a successful write
                records_count = len(changed_records)
                success_count, failed_records = await target_adapter.write_records(
                    target_entity_type,
                    changed_records
                )
                
                total_records_processed += records_count
                total_records_succeeded += success_count
                total_records_failed += len(failed_records)
            
            # Disconnect from source and target systems
            await source_adapter.disconnect()
            await target_adapter.disconnect()
        
        # Update job status
        sync_jobs[job_id]["status"] = "completed"
        sync_jobs[job_id]["details"] = {
            "records_processed": total_records_processed,
            "records_succeeded": total_records_succeeded,
            "records_failed": total_records_failed,
            "pairs_processed": len(pairs_to_process),
            "since": since.isoformat(),
            "completion_time": datetime.utcnow().isoformat(),
            "duration_seconds": (datetime.utcnow() - sync_jobs[job_id]["timestamp"]).total_seconds()
        }
        
    except Exception as e:
        # Update job status on failure
        sync_jobs[job_id]["status"] = "failed"
        sync_jobs[job_id]["details"] = {
            "error": str(e),
            "failure_time": datetime.utcnow().isoformat()
        }