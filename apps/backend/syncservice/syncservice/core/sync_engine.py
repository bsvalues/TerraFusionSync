"""
Synchronization Engine module for the SyncService.

This module orchestrates the end-to-end synchronization process, coordinating the various
components to detect changes, transform, validate, and sync data between systems.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union

from ..interfaces.system_adapter import SourceSystemAdapter, TargetSystemAdapter
from ..models.base import (
    SyncType, SyncStatus, SyncOperation, SyncOperationDetails, 
    SourceRecord, TargetRecord, TransformedRecord, ValidationResult, EntityStats
)
from .change_detector import ChangeDetector
from .transformer import Transformer
from .validator import Validator
from .self_healing import SelfHealingOrchestrator

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Engine that orchestrates the end-to-end synchronization process.
    
    This component coordinates the various sub-components to detect changes, transform,
    validate, and sync data between source and target systems.
    """
    
    def __init__(
        self,
        source_adapter: SourceSystemAdapter,
        target_adapter: TargetSystemAdapter,
        transformer: Transformer,
        validator: Validator,
        self_healing: SelfHealingOrchestrator
    ):
        """
        Initialize the Sync Engine.
        
        Args:
            source_adapter: Adapter for the source system
            target_adapter: Adapter for the target system
            transformer: Data transformer component
            validator: Data validator component
            self_healing: Self-healing orchestrator component
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.transformer = transformer
        self.validator = validator
        self.self_healing = self_healing
        
        # Create a change detector
        self.change_detector = ChangeDetector(source_adapter)
    
    async def perform_full_sync(
        self,
        sync_pair_id: str,
        entity_types: List[str],
        operation_id: Optional[str] = None,
        batch_size: int = 100
    ) -> SyncOperation:
        """
        Perform a full synchronization for specified entity types.
        
        Args:
            sync_pair_id: ID of the sync pair configuration
            entity_types: List of entity types to synchronize
            operation_id: Optional ID for the sync operation
            batch_size: Batch size for processing records
            
        Returns:
            Sync operation details
        """
        # Generate an operation ID if not provided
        if not operation_id:
            operation_id = f"full-sync-{uuid.uuid4()}"
        
        logger.info(f"Starting full sync operation {operation_id} for pair {sync_pair_id}")
        
        # Create a sync operation record
        sync_op = SyncOperation(
            id=operation_id,
            sync_type=SyncType.FULL,
            sync_pair_id=sync_pair_id,
            entity_types=entity_types,
            status=SyncStatus.IN_PROGRESS,
            start_time=datetime.utcnow()
        )
        
        # Initialize sync operation details
        details = SyncOperationDetails(
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            entities={}
        )
        
        # Process each entity type
        try:
            for entity_type in entity_types:
                logger.info(f"Processing entity type: {entity_type}")
                
                # Initialize entity stats
                details.entities[entity_type] = {
                    "processed": 0,
                    "succeeded": 0,
                    "failed": 0
                }
                
                # Get count of records for this entity type
                count = await self.source_adapter.get_record_count(entity_type)
                
                # Process records in batches
                offset = 0
                while offset < count:
                    # Get a batch of records from the source system
                    records, _ = await self.source_adapter.get_records(
                        entity_type=entity_type,
                        batch_size=batch_size,
                        offset=offset
                    )
                    
                    if not records:
                        break
                    
                    # Process the batch
                    batch_result = await self.process_record_batch(
                        entity_type=entity_type,
                        source_records=records
                    )
                    
                    # Update entity stats
                    details.entities[entity_type]["processed"] += batch_result["processed"]
                    details.entities[entity_type]["succeeded"] += batch_result["succeeded"]
                    details.entities[entity_type]["failed"] += batch_result["failed"]
                    
                    # Update total stats
                    details.records_processed += batch_result["processed"]
                    details.records_succeeded += batch_result["succeeded"]
                    details.records_failed += batch_result["failed"]
                    
                    # Move to next batch
                    offset += batch_size
                
                logger.info(f"Finished processing entity type {entity_type}: "
                            f"{details.entities[entity_type]['processed']} processed, "
                            f"{details.entities[entity_type]['succeeded']} succeeded, "
                            f"{details.entities[entity_type]['failed']} failed")
            
            # Mark the operation as completed
            sync_op.status = SyncStatus.COMPLETED
            sync_op.end_time = datetime.utcnow()
            sync_op.details = details
            
            logger.info(f"Full sync operation {operation_id} completed. "
                        f"Total: {details.records_processed} processed, "
                        f"{details.records_succeeded} succeeded, "
                        f"{details.records_failed} failed")
            
        except Exception as e:
            logger.error(f"Error during full sync: {str(e)}")
            
            # Mark the operation as failed
            sync_op.status = SyncStatus.FAILED
            sync_op.end_time = datetime.utcnow()
            sync_op.error = str(e)
            sync_op.details = details
        
        return sync_op
    
    async def perform_incremental_sync(
        self,
        sync_pair_id: str,
        entity_types: List[str],
        since: datetime,
        operation_id: Optional[str] = None,
        batch_size: int = 100
    ) -> SyncOperation:
        """
        Perform an incremental synchronization for changes since a specific time.
        
        Args:
            sync_pair_id: ID of the sync pair configuration
            entity_types: List of entity types to synchronize
            since: Only sync records modified since this time
            operation_id: Optional ID for the sync operation
            batch_size: Batch size for processing records
            
        Returns:
            Sync operation details
        """
        # Generate an operation ID if not provided
        if not operation_id:
            operation_id = f"incremental-sync-{uuid.uuid4()}"
        
        logger.info(f"Starting incremental sync operation {operation_id} for pair {sync_pair_id} "
                    f"since {since}")
        
        # Create a sync operation record
        sync_op = SyncOperation(
            id=operation_id,
            sync_type=SyncType.INCREMENTAL,
            sync_pair_id=sync_pair_id,
            entity_types=entity_types,
            status=SyncStatus.IN_PROGRESS,
            start_time=datetime.utcnow()
        )
        
        # Initialize sync operation details
        details = SyncOperationDetails(
            records_processed=0,
            records_succeeded=0,
            records_failed=0,
            entities={}
        )
        
        # Process each entity type
        try:
            for entity_type in entity_types:
                logger.info(f"Processing entity type: {entity_type}")
                
                # Initialize entity stats
                details.entities[entity_type] = {
                    "processed": 0,
                    "succeeded": 0,
                    "failed": 0
                }
                
                # Get changed records for this entity type
                records, count = await self.change_detector.get_changed_records(
                    entity_type=entity_type,
                    since=since,
                    batch_size=batch_size
                )
                
                # If there are changes, process them
                if records:
                    # Process the batch
                    batch_result = await self.process_record_batch(
                        entity_type=entity_type,
                        source_records=records
                    )
                    
                    # Update entity stats
                    details.entities[entity_type]["processed"] += batch_result["processed"]
                    details.entities[entity_type]["succeeded"] += batch_result["succeeded"]
                    details.entities[entity_type]["failed"] += batch_result["failed"]
                    
                    # Update total stats
                    details.records_processed += batch_result["processed"]
                    details.records_succeeded += batch_result["succeeded"]
                    details.records_failed += batch_result["failed"]
                
                logger.info(f"Finished processing entity type {entity_type}: "
                            f"{details.entities[entity_type]['processed']} processed, "
                            f"{details.entities[entity_type]['succeeded']} succeeded, "
                            f"{details.entities[entity_type]['failed']} failed")
            
            # Mark the operation as completed
            sync_op.status = SyncStatus.COMPLETED
            sync_op.end_time = datetime.utcnow()
            sync_op.details = details
            
            logger.info(f"Incremental sync operation {operation_id} completed. "
                        f"Total: {details.records_processed} processed, "
                        f"{details.records_succeeded} succeeded, "
                        f"{details.records_failed} failed")
            
        except Exception as e:
            logger.error(f"Error during incremental sync: {str(e)}")
            
            # Mark the operation as failed
            sync_op.status = SyncStatus.FAILED
            sync_op.end_time = datetime.utcnow()
            sync_op.error = str(e)
            sync_op.details = details
        
        return sync_op
    
    async def process_record_batch(
        self,
        entity_type: str,
        source_records: List[SourceRecord]
    ) -> Dict[str, int]:
        """
        Process a batch of records through the full sync pipeline.
        
        This method performs transformation, validation, self-healing, and synchronization
        for a batch of records.
        
        Args:
            entity_type: Type of entity being processed
            source_records: List of source records to process
            
        Returns:
            Dictionary with counts of processed, succeeded, and failed records
        """
        logger.info(f"Processing batch of {len(source_records)} {entity_type} records")
        
        # Initialize metrics
        result = {
            "processed": len(source_records),
            "succeeded": 0,
            "failed": 0
        }
        
        try:
            # 1. Get existing record IDs from target system
            source_ids = [record.source_id for record in source_records]
            target_id_map = {}
            
            for source_id in source_ids:
                existing_record = await self.target_adapter.get_existing_record(
                    entity_type=entity_type,
                    source_id=source_id
                )
                if existing_record:
                    target_id_map[source_id] = existing_record.target_id
            
            # 2. Transform the records
            transformed_records = await self.transformer.batch_transform_records(
                entity_type=entity_type,
                source_records=source_records,
                target_id_map=target_id_map
            )
            
            # 3. Validate the transformed records
            validation_results = await self.validator.batch_validate_records(
                entity_type=entity_type,
                records=transformed_records
            )
            
            # 4. Apply self-healing to invalid records
            invalid_indices = [i for i, v in enumerate(validation_results) if not v.is_valid]
            
            if invalid_indices:
                invalid_records = [transformed_records[i] for i in invalid_indices]
                invalid_validations = [validation_results[i] for i in invalid_indices]
                
                healed_records = await self.self_healing.heal_invalid_records(
                    entity_type=entity_type,
                    transformed_records=invalid_records,
                    validation_results=invalid_validations
                )
                
                # Replace invalid records with healed versions
                for i, healed_record in zip(invalid_indices, healed_records):
                    transformed_records[i] = healed_record
                
                # Re-validate the healed records
                for i, healed_record in zip(invalid_indices, healed_records):
                    validation_results[i] = await self.validator.validate_record(
                        entity_type=entity_type,
                        data=healed_record.target_data,
                        entity_id=healed_record.source_id
                    )
            
            # 5. Process each record - create, update, or skip based on validation
            for record, validation in zip(transformed_records, validation_results):
                if not validation.is_valid:
                    # Record is still invalid after healing, skip it
                    logger.warning(f"Skipping invalid {entity_type} record {record.source_id}: "
                                   f"{validation.errors}")
                    result["failed"] += 1
                    continue
                
                try:
                    # Check if record has a target ID (existing record)
                    if record.target_id:
                        # Get existing record to check for conflicts
                        existing_target = await self.target_adapter.get_record_by_id(
                            entity_type=entity_type,
                            target_id=record.target_id
                        )
                        
                        if existing_target:
                            # Detect conflicts
                            conflicts = await self.self_healing.detect_conflicts(
                                entity_type=entity_type,
                                transformed_record=record,
                                existing_record=existing_target.data
                            )
                            
                            # Resolve conflicts if any
                            if conflicts:
                                record = await self.self_healing.resolve_conflicts(
                                    entity_type=entity_type,
                                    transformed_record=record,
                                    conflicts=conflicts
                                )
                            
                            # Update the existing record
                            success = await self.target_adapter.update_record(
                                entity_type=entity_type,
                                target_id=record.target_id,
                                data=record.target_data
                            )
                            
                            if success:
                                result["succeeded"] += 1
                            else:
                                result["failed"] += 1
                        else:
                            # Target ID is invalid, create a new record instead
                            new_target_id = await self.target_adapter.create_record(
                                entity_type=entity_type,
                                source_id=record.source_id,
                                data=record.target_data
                            )
                            
                            if new_target_id:
                                result["succeeded"] += 1
                            else:
                                result["failed"] += 1
                    else:
                        # Create a new record
                        new_target_id = await self.target_adapter.create_record(
                            entity_type=entity_type,
                            source_id=record.source_id,
                            data=record.target_data
                        )
                        
                        if new_target_id:
                            result["succeeded"] += 1
                        else:
                            result["failed"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing {entity_type} record {record.source_id}: {str(e)}")
                    result["failed"] += 1
            
            logger.info(f"Batch processing complete: {result['succeeded']} succeeded, "
                        f"{result['failed']} failed")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing record batch: {str(e)}")
            result["failed"] = len(source_records)
            result["succeeded"] = 0
            return result