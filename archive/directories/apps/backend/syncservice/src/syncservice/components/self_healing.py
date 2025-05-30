"""
Self-Healing Orchestrator component for the SyncService.

This module manages the orchestration of the sync process, handles failures,
resolves conflicts, and provides self-healing capabilities.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

from tenacity import (RetryError, Retrying, retry, retry_if_exception_type,
                     stop_after_attempt, wait_exponential)

from syncservice.models.audit import (AuditLogEntry, ConflictRecordCreate,
                                    SyncAudit)
from syncservice.models.base import ConflictRecord
from syncservice.utils.database import (execute_target_query,
                                       get_source_session, get_target_session)
from syncservice.utils.event_bus import publish_event

logger = logging.getLogger(__name__)


class SelfHealingOrchestrator:
    """
    Orchestrates the sync process with self-healing capabilities.
    
    This component manages the overall sync workflow, handles errors,
    resolves conflicts, and ensures data integrity.
    """

    def __init__(self):
        """Initialize the Self-Healing Orchestrator component."""
        self.source_session = None
        self.target_session = None
        self.audit_records = []
        self.conflicts = []

    async def initialize(self):
        """Initialize database sessions and other resources."""
        self.source_session = await get_source_session()
        self.target_session = await get_target_session()

    async def run_sync_pipeline(
        self, 
        detector, 
        transformer, 
        validator,
        since: Optional[datetime] = None,
        is_full_sync: bool = False
    ) -> Dict:
        """
        Run the complete sync pipeline with self-healing capabilities.
        
        Args:
            detector: ChangeDetector component instance
            transformer: Transformer component instance
            validator: Validator component instance
            since: Timestamp to check for changes since
            is_full_sync: Whether this is a full sync operation
            
        Returns:
            Dictionary with sync operation results
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting {'full' if is_full_sync else 'incremental'} sync pipeline at {start_time}")
        
        # Initialize sessions
        await self.initialize()
        
        # Create audit record
        sync_audit = SyncAudit(
            id=str(uuid.uuid4()),
            operation_type="full_sync" if is_full_sync else "incremental_sync",
            operation_timestamp=start_time,
            source_system="PACS",
            target_system="CAMA",
            record_count=0,
            success=False
        )
        
        try:
            # Step 1: Detect changes
            if is_full_sync:
                change_counts = await detector.perform_full_change_detection()
                logger.info(f"Full change detection complete: {change_counts}")
                # For full sync, we'd typically process records in batches
                # This is a placeholder - actual implementation would use pagination
                changed_records = {"properties": [], "owners": [], "values": [], "structures": []}
            else:
                changed_records = await detector.get_changed_records(since=since)
                logger.info(f"Change detection complete, found: {sum(len(v) for k, v in changed_records.items() if k != 'related')}")
            
            # Step 2: Transform records
            transformed_records = await transformer.batch_transform_records(changed_records)
            logger.info(f"Transformation complete")
            
            # Step 3: Validate records
            validation_results = await validator.batch_validate_records(transformed_records)
            logger.info(f"Validation complete: {validation_results['stats']}")
            
            # Step 4: Detect and resolve conflicts
            conflicts = await self.detect_conflicts(transformed_records)
            resolved_conflicts = await self.resolve_conflicts(conflicts)
            logger.info(f"Conflict resolution complete: {len(resolved_conflicts)} conflicts resolved")
            
            # Update records with conflict resolutions
            await self.apply_conflict_resolutions(transformed_records, resolved_conflicts)
            
            # Step 5: Persist valid records to target system
            persist_result = await self.persist_records(validation_results["valid"])
            logger.info(f"Persistence complete: {persist_result}")
            
            # Step 6: Handle invalid records
            healing_result = await self.heal_invalid_records(validation_results["invalid"])
            logger.info(f"Self-healing complete: {healing_result}")
            
            # Record final counts
            total_processed = validation_results["stats"]["total_records"]
            total_valid = validation_results["stats"]["valid_records"]
            total_healed = healing_result.get("healed_count", 0)
            total_failed = total_processed - total_valid - total_healed
            
            # Update audit record
            sync_audit.record_count = total_processed
            sync_audit.success = True
            sync_audit.details = {
                "valid_count": total_valid,
                "invalid_count": validation_results["stats"]["invalid_records"],
                "healed_count": total_healed,
                "failed_count": total_failed,
                "conflict_count": len(conflicts),
                "resolved_conflict_count": len(resolved_conflicts)
            }
            
            # Publish success event
            await publish_event(
                "sync_completed",
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation_type": "full_sync" if is_full_sync else "incremental_sync",
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds(),
                    "record_counts": {
                        "processed": total_processed,
                        "valid": total_valid,
                        "healed": total_healed,
                        "failed": total_failed,
                        "conflicts": len(conflicts),
                        "resolved_conflicts": len(resolved_conflicts)
                    }
                }
            )
            
            return {
                "success": True,
                "count": total_processed,
                "timestamp": datetime.utcnow().isoformat(),
                "details": {
                    "valid_count": total_valid,
                    "invalid_count": validation_results["stats"]["invalid_records"],
                    "healed_count": total_healed,
                    "failed_count": total_failed,
                    "conflict_count": len(conflicts),
                    "resolved_conflict_count": len(resolved_conflicts),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in sync pipeline: {str(e)}", exc_info=True)
            
            # Update audit record with error
            sync_audit.success = False
            sync_audit.error_message = str(e)
            
            # Publish failure event
            await publish_event(
                "sync_failed",
                {
                    "timestamp": datetime.utcnow().isoformat(),
                    "operation_type": "full_sync" if is_full_sync else "incremental_sync",
                    "error": str(e),
                    "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                }
            )
            
            return {
                "success": False,
                "count": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        finally:
            # Persist the audit record
            await self.persist_audit_record(sync_audit)
            
            # Record operation duration
            duration = datetime.utcnow() - start_time
            logger.info(f"Sync pipeline completed in {duration.total_seconds()} seconds")

    async def detect_conflicts(
        self, 
        transformed_records: Dict[str, List]
    ) -> List[ConflictRecord]:
        """
        Detect conflicts between source and target data.
        
        Args:
            transformed_records: Dictionary containing transformed records by entity type
            
        Returns:
            List of detected conflicts
        """
        logger.info("Detecting conflicts")
        conflicts = []
        
        # Check for conflicts in properties
        for property_data in transformed_records.get("properties", []):
            # Look for existing property with same source_id in target system
            query = "SELECT * FROM cama_property WHERE source_id = %s"
            existing_records = await execute_target_query(query, [property_data.source_id])
            
            if existing_records:
                existing_record = existing_records[0]
                
                # Compare fields to detect conflicts
                for field_name in ["address", "city", "state", "zip_code", "legal_description", "acreage", "year_built"]:
                    source_value = getattr(property_data, field_name)
                    target_value = existing_record.get(field_name)
                    
                    # If both values exist and are different, it's a conflict
                    if source_value is not None and target_value is not None and source_value != target_value:
                        conflicts.append(ConflictRecord(
                            record_id=existing_record.get("id"),
                            source_value=source_value,
                            target_value=target_value,
                            field_name=field_name,
                            resolution_strategy=None
                        ))
        
        # Similar conflict detection for owners, values, and structures
        # This is simplified for brevity but would follow the same pattern
        
        logger.info(f"Detected {len(conflicts)} conflicts")
        return conflicts

    async def resolve_conflicts(
        self, 
        conflicts: List[ConflictRecord]
    ) -> List[ConflictRecord]:
        """
        Resolve conflicts using configured resolution strategies.
        
        Args:
            conflicts: List of detected conflicts
            
        Returns:
            List of resolved conflicts
        """
        resolved_conflicts = []
        
        for conflict in conflicts:
            # Apply resolution strategy based on field and values
            strategy = await self._determine_resolution_strategy(conflict)
            conflict.resolution_strategy = strategy
            
            # Store the conflict record for auditing
            conflict_record = ConflictRecordCreate(
                record_id=conflict.record_id,
                source_value=conflict.source_value,
                target_value=conflict.target_value,
                field_name=conflict.field_name,
                resolution_strategy=strategy
            )
            self.conflicts.append(conflict_record)
            
            # Add to resolved conflicts
            resolved_conflicts.append(conflict)
            
            # Log the resolution
            logger.info(f"Resolved conflict for record {conflict.record_id}, field {conflict.field_name} with strategy {strategy}")
            
            # Publish conflict resolution event
            await publish_event(
                "conflict_resolved",
                {
                    "record_id": conflict.record_id,
                    "field_name": conflict.field_name,
                    "source_value": str(conflict.source_value),
                    "target_value": str(conflict.target_value),
                    "resolution_strategy": strategy,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
        
        return resolved_conflicts

    async def _determine_resolution_strategy(
        self, 
        conflict: ConflictRecord
    ) -> str:
        """
        Determine the appropriate resolution strategy for a conflict.
        
        Args:
            conflict: The conflict to resolve
            
        Returns:
            Resolution strategy to apply
        """
        # Simple strategy: choose based on field name
        field_name = conflict.field_name.lower()
        
        # For address-related fields, source system (PACS) is authoritative
        if field_name in ["address", "city", "state", "zip_code", "legal_description"]:
            return "source_wins"
        
        # For valuation fields, target system (CAMA) is authoritative
        elif field_name in ["market_value", "assessed_value", "land_value", "improvement_value"]:
            return "target_wins"
        
        # For structural fields, merge the data (in practice, this would be more sophisticated)
        elif field_name in ["square_footage", "bedrooms", "bathrooms", "year_built"]:
            return "merge"
        
        # Default to source system
        return "source_wins"

    async def apply_conflict_resolutions(
        self, 
        records: Dict[str, List],
        resolved_conflicts: List[ConflictRecord]
    ) -> None:
        """
        Apply conflict resolutions to the transformed records.
        
        Args:
            records: Dictionary containing transformed records by entity type
            resolved_conflicts: List of resolved conflicts
        """
        # Create lookup maps for conflicts by record ID
        conflict_map = {}
        for conflict in resolved_conflicts:
            if conflict.record_id not in conflict_map:
                conflict_map[conflict.record_id] = {}
            conflict_map[conflict.record_id][conflict.field_name] = conflict
        
        # Apply resolutions to properties
        for property_data in records.get("properties", []):
            if property_data.id in conflict_map:
                field_conflicts = conflict_map[property_data.id]
                for field_name, conflict in field_conflicts.items():
                    if conflict.resolution_strategy == "source_wins":
                        # Source already wins as it's the value in the transformed record
                        pass
                    elif conflict.resolution_strategy == "target_wins":
                        # Use target value
                        setattr(property_data, field_name, conflict.target_value)
                    elif conflict.resolution_strategy == "merge":
                        # Simple merge - in practice, this would be more sophisticated
                        if isinstance(conflict.source_value, (int, float)) and isinstance(conflict.target_value, (int, float)):
                            merged_value = (conflict.source_value + conflict.target_value) / 2
                            setattr(property_data, field_name, merged_value)
        
        # Similar resolution application for owners, values, and structures
        # This is simplified for brevity but would follow the same pattern

    async def persist_records(
        self, 
        valid_records: Dict[str, List]
    ) -> Dict:
        """
        Persist valid records to the target system.
        
        Args:
            valid_records: Dictionary containing valid records by entity type
            
        Returns:
            Dictionary with persistence results
        """
        logger.info("Persisting valid records to target system")
        
        # Counters for successful insertions/updates
        inserted_properties = 0
        updated_properties = 0
        inserted_owners = 0
        updated_owners = 0
        inserted_values = 0
        updated_values = 0
        inserted_structures = 0
        updated_structures = 0
        
        # Persist properties first
        for property_data in valid_records.get("properties", []):
            try:
                # Check if property already exists by source_id
                query = "SELECT id FROM cama_property WHERE source_id = %s"
                existing = await execute_target_query(query, [property_data.source_id])
                
                if existing:
                    # Update existing property
                    update_query = """
                    UPDATE cama_property SET 
                        parcel_number = %s,
                        address = %s,
                        city = %s,
                        state = %s,
                        zip_code = %s,
                        legal_description = %s,
                        acreage = %s,
                        year_built = %s,
                        source_last_modified = %s,
                        is_active = %s,
                        geo_coordinates = %s,
                        additional_data = %s,
                        updated_at = %s
                    WHERE source_id = %s
                    """
                    
                    params = [
                        property_data.parcel_number,
                        property_data.address,
                        property_data.city,
                        property_data.state,
                        property_data.zip_code,
                        property_data.legal_description,
                        property_data.acreage,
                        property_data.year_built,
                        property_data.source_last_modified,
                        property_data.is_active,
                        json.dumps(property_data.geo_coordinates) if property_data.geo_coordinates else None,
                        json.dumps(property_data.additional_data) if property_data.additional_data else None,
                        datetime.utcnow(),
                        property_data.source_id
                    ]
                    
                    await execute_target_query(update_query, params)
                    updated_properties += 1
                else:
                    # Insert new property
                    insert_query = """
                    INSERT INTO cama_property (
                        id, source_id, parcel_number, address, city, state, zip_code,
                        legal_description, acreage, year_built, source_last_modified,
                        is_active, geo_coordinates, additional_data, created_at, updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    params = [
                        property_data.id,
                        property_data.source_id,
                        property_data.parcel_number,
                        property_data.address,
                        property_data.city,
                        property_data.state,
                        property_data.zip_code,
                        property_data.legal_description,
                        property_data.acreage,
                        property_data.year_built,
                        property_data.source_last_modified,
                        property_data.is_active,
                        json.dumps(property_data.geo_coordinates) if property_data.geo_coordinates else None,
                        json.dumps(property_data.additional_data) if property_data.additional_data else None,
                        datetime.utcnow(),
                        datetime.utcnow()
                    ]
                    
                    await execute_target_query(insert_query, params)
                    inserted_properties += 1
                
                # Record audit for property operation
                self.audit_records.append(AuditLogEntry(
                    id=str(uuid.uuid4()),
                    event_type="property_persisted",
                    component="self_healing_orchestrator",
                    event_timestamp=datetime.utcnow(),
                    record_id=property_data.id,
                    details={
                        "source_id": property_data.source_id,
                        "operation": "update" if existing else "insert"
                    }
                ))
                
            except Exception as e:
                logger.error(f"Error persisting property {property_data.id}: {str(e)}")
                
                # Record error in audit
                self.audit_records.append(AuditLogEntry(
                    id=str(uuid.uuid4()),
                    event_type="property_persist_failed",
                    component="self_healing_orchestrator",
                    event_timestamp=datetime.utcnow(),
                    record_id=property_data.id,
                    details={
                        "source_id": property_data.source_id,
                        "error": str(e)
                    }
                ))
        
        # Similar persistence logic for owners, values, and structures
        # This is simplified for brevity but would follow the same pattern
        
        # Publish persistence event
        await publish_event(
            "records_persisted",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "counts": {
                    "properties": {
                        "inserted": inserted_properties,
                        "updated": updated_properties
                    },
                    "owners": {
                        "inserted": inserted_owners,
                        "updated": updated_owners
                    },
                    "values": {
                        "inserted": inserted_values,
                        "updated": updated_values
                    },
                    "structures": {
                        "inserted": inserted_structures,
                        "updated": updated_structures
                    }
                }
            }
        )
        
        return {
            "properties": {
                "inserted": inserted_properties,
                "updated": updated_properties
            },
            "owners": {
                "inserted": inserted_owners,
                "updated": updated_owners
            },
            "values": {
                "inserted": inserted_values,
                "updated": updated_values
            },
            "structures": {
                "inserted": inserted_structures,
                "updated": updated_structures
            }
        }

    async def heal_invalid_records(
        self, 
        invalid_records: Dict[str, List]
    ) -> Dict:
        """
        Attempt to heal invalid records using corrective strategies.
        
        Args:
            invalid_records: Dictionary containing invalid records by entity type
            
        Returns:
            Dictionary with healing results
        """
        logger.info("Attempting to heal invalid records")
        
        healed_count = 0
        failed_count = 0
        
        # Heal properties
        healed_properties = []
        for property_data, errors in invalid_records.get("properties", []):
            try:
                # Apply healing strategies based on the validation errors
                healed = await self._apply_healing_strategies(property_data, errors, "property")
                
                if healed:
                    healed_properties.append(property_data)
                    healed_count += 1
                    
                    # Record successful healing in audit
                    self.audit_records.append(AuditLogEntry(
                        id=str(uuid.uuid4()),
                        event_type="property_healed",
                        component="self_healing_orchestrator",
                        event_timestamp=datetime.utcnow(),
                        record_id=property_data.id,
                        details={
                            "source_id": property_data.source_id,
                            "original_errors": errors,
                            "healing_actions": self._get_healing_actions(errors)
                        }
                    ))
                else:
                    failed_count += 1
                    
                    # Record failed healing in audit
                    self.audit_records.append(AuditLogEntry(
                        id=str(uuid.uuid4()),
                        event_type="property_healing_failed",
                        component="self_healing_orchestrator",
                        event_timestamp=datetime.utcnow(),
                        record_id=property_data.id,
                        details={
                            "source_id": property_data.source_id,
                            "errors": errors
                        }
                    ))
            except Exception as e:
                logger.error(f"Error healing property {property_data.id}: {str(e)}")
                failed_count += 1
        
        # Similar healing logic for owners, values, and structures
        # This is simplified for brevity but would follow the same pattern
        
        # Publish healing event
        await publish_event(
            "records_healed",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "healed_count": healed_count,
                "failed_count": failed_count
            }
        )
        
        return {
            "healed_count": healed_count,
            "failed_count": failed_count,
            "healed_properties": healed_properties
            # Other healed records would be here
        }

    async def _apply_healing_strategies(
        self, 
        record, 
        errors: List[str],
        record_type: str
    ) -> bool:
        """
        Apply healing strategies to a record based on validation errors.
        
        Args:
            record: The record to heal
            errors: List of validation errors
            record_type: Type of record (property, owner, etc.)
            
        Returns:
            Whether healing was successful
        """
        if not errors:
            return True
            
        all_fixed = True
        
        # Go through each error and apply appropriate healing strategy
        for error in errors:
            fixed = False
            
            # Parcel number format issues
            if "Parcel number must contain only letters, numbers, and dashes" in error:
                if hasattr(record, "parcel_number") and record.parcel_number:
                    # Clean up parcel number to match required format
                    cleaned = ''.join(c for c in record.parcel_number if c.isalnum() or c == '-')
                    if cleaned:
                        record.parcel_number = cleaned
                        fixed = True
            
            # Address length issues
            elif "Address must be at least 5 characters long" in error:
                if hasattr(record, "address") and record.address:
                    # If address is too short, append municipality or set to "Unknown"
                    if len(record.address) < 5:
                        if hasattr(record, "city") and record.city:
                            record.address = f"{record.address}, {record.city}"
                        else:
                            record.address = "Unknown Address"
                        fixed = True
            
            # State code issues
            elif "State must be a 2-letter code" in error:
                if hasattr(record, "state") and record.state:
                    # Truncate to 2 letters or set default
                    if len(record.state) > 2:
                        record.state = record.state[:2].upper()
                        fixed = True
                    elif len(record.state) < 2:
                        record.state = "XX"  # Default for unknown
                        fixed = True
            
            # Numeric validation issues
            elif "must be greater than 0" in error:
                # Extract field name from error message
                field_name = error.split()[0].lower()
                if hasattr(record, field_name) and getattr(record, field_name) is not None:
                    if getattr(record, field_name) <= 0:
                        # Set to smallest valid value
                        setattr(record, field_name, 0.01)
                        fixed = True
            
            # Year built issues
            elif "Year built must be between" in error:
                if hasattr(record, "year_built") and record.year_built is not None:
                    current_year = datetime.now().year
                    if record.year_built < 1700:
                        record.year_built = 1700
                        fixed = True
                    elif record.year_built > current_year:
                        record.year_built = current_year
                        fixed = True
            
            # Update all_fixed flag
            all_fixed = all_fixed and fixed
            
            # If not fixed, log it
            if not fixed:
                logger.warning(f"Could not heal error: {error}")
        
        return all_fixed

    def _get_healing_actions(self, errors: List[str]) -> List[str]:
        """
        Generate descriptions of healing actions based on errors.
        
        Args:
            errors: List of validation errors
            
        Returns:
            List of descriptions of healing actions taken
        """
        actions = []
        
        for error in errors:
            if "Parcel number must contain only letters, numbers, and dashes" in error:
                actions.append("Cleaned parcel number to contain only alphanumeric characters and dashes")
            elif "Address must be at least 5 characters long" in error:
                actions.append("Extended address with city information or set to 'Unknown Address'")
            elif "State must be a 2-letter code" in error:
                actions.append("Adjusted state code to standard 2-letter format")
            elif "must be greater than 0" in error:
                field = error.split()[0].lower()
                actions.append(f"Set {field} to minimum valid value (0.01)")
            elif "Year built must be between" in error:
                actions.append("Adjusted year built to valid range (1700-current year)")
        
        return actions

    async def persist_audit_record(self, sync_audit: SyncAudit) -> None:
        """
        Persist audit records to the database.
        
        Args:
            sync_audit: The main sync audit record
        """
        try:
            # Insert sync audit record
            audit_query = """
            INSERT INTO sync_audit (
                id, operation_type, operation_timestamp, source_system,
                target_system, record_count, success, error_message,
                details, initiated_by, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            audit_params = [
                sync_audit.id,
                sync_audit.operation_type,
                sync_audit.operation_timestamp,
                sync_audit.source_system,
                sync_audit.target_system,
                sync_audit.record_count,
                sync_audit.success,
                sync_audit.error_message,
                json.dumps(sync_audit.details) if sync_audit.details else None,
                sync_audit.initiated_by,
                datetime.utcnow(),
                datetime.utcnow()
            ]
            
            await execute_target_query(audit_query, audit_params)
            
            # Insert detailed audit log entries
            for entry in self.audit_records:
                entry_query = """
                INSERT INTO audit_log (
                    id, event_type, component, event_timestamp, record_id,
                    user_id, details, sync_audit_id, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                entry_params = [
                    entry.id,
                    entry.event_type,
                    entry.component,
                    entry.event_timestamp,
                    entry.record_id,
                    entry.user_id,
                    json.dumps(entry.details) if entry.details else None,
                    sync_audit.id,
                    datetime.utcnow(),
                    datetime.utcnow()
                ]
                
                await execute_target_query(entry_query, entry_params)
            
            # Insert conflict records
            for conflict in self.conflicts:
                conflict_query = """
                INSERT INTO sync_conflicts (
                    id, record_id, source_value, target_value, field_name,
                    resolution_strategy, resolved, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                conflict_params = [
                    str(uuid.uuid4()),
                    conflict.record_id,
                    json.dumps(conflict.source_value),
                    json.dumps(conflict.target_value),
                    conflict.field_name,
                    conflict.resolution_strategy,
                    True,  # All conflicts are resolved at this point
                    datetime.utcnow(),
                    datetime.utcnow()
                ]
                
                await execute_target_query(conflict_query, conflict_params)
            
        except Exception as e:
            logger.error(f"Error persisting audit records: {str(e)}")
