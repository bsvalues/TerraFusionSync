"""
Self-Healing Orchestrator module for the SyncService.

This module is responsible for detecting and resolving conflicts between source and target
systems, applying healing strategies to maintain data consistency.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set, Union

from ..interfaces.system_adapter import SourceSystemAdapter, TargetSystemAdapter
from ..models.base import (
    TransformedRecord, ValidationResult, Conflict, ConflictResolution
)

logger = logging.getLogger(__name__)


class SelfHealingOrchestrator:
    """
    Component responsible for detecting and resolving conflicts.
    
    The Self-Healing Orchestrator detects conflicts between source and target systems
    and applies appropriate resolution strategies to maintain data consistency.
    """
    
    def __init__(
        self,
        source_adapter: SourceSystemAdapter,
        target_adapter: TargetSystemAdapter,
        resolution_rules_path: Optional[str] = None
    ):
        """
        Initialize the Self-Healing Orchestrator.
        
        Args:
            source_adapter: Adapter for the source system
            target_adapter: Adapter for the target system
            resolution_rules_path: Path to the conflict resolution rules configuration
        """
        self.source_adapter = source_adapter
        self.target_adapter = target_adapter
        self.resolution_rules_path = resolution_rules_path
        self.resolution_rules = {}
        
        # TODO: Load resolution rules from file when available
    
    async def detect_conflicts(
        self,
        entity_type: str,
        transformed_record: TransformedRecord,
        existing_record: Optional[Dict[str, Any]] = None
    ) -> List[Conflict]:
        """
        Detect conflicts between a transformed record and an existing target record.
        
        Args:
            entity_type: Type of entity being processed
            transformed_record: Transformed record from source system
            existing_record: Existing record in target system, if any
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # If no existing record, there are no conflicts
        if not existing_record:
            return conflicts
        
        logger.debug(f"Detecting conflicts for {entity_type} record {transformed_record.source_id}")
        
        # Compare fields in transformed record with existing record
        for field, new_value in transformed_record.target_data.items():
            if field not in existing_record:
                continue
            
            existing_value = existing_record[field]
            
            # Skip if values are equal
            if new_value == existing_value:
                continue
            
            # Create conflict record
            conflict = Conflict(
                source_id=transformed_record.source_id,
                target_id=transformed_record.target_id or "",
                entity_type=entity_type,
                field=field,
                source_value=new_value,
                target_value=existing_value
            )
            
            conflicts.append(conflict)
            logger.debug(f"Detected conflict in field '{field}': {existing_value} vs {new_value}")
        
        logger.info(f"Detected {len(conflicts)} conflicts for {entity_type} record "
                    f"{transformed_record.source_id}")
        
        return conflicts
    
    def determine_resolution_strategy(
        self,
        entity_type: str,
        field: str,
        conflict: Conflict
    ) -> ConflictResolution:
        """
        Determine the appropriate resolution strategy for a conflict.
        
        Args:
            entity_type: Type of entity with the conflict
            field: Field with the conflict
            conflict: Conflict details
            
        Returns:
            Resolution strategy to apply
        """
        # Get resolution rules for this entity type and field
        entity_rules = self.resolution_rules.get(entity_type, {})
        field_rules = entity_rules.get(field, {})
        
        # Get default strategy from field rules or use SOURCE_WINS as fallback
        default_strategy = field_rules.get('default_strategy', ConflictResolution.SOURCE_WINS)
        
        # Check for specific conditions that might override the default
        
        # Critical fields might have special handling
        critical_fields = field_rules.get('critical_fields', [])
        if field in critical_fields:
            return ConflictResolution.MANUAL
        
        # Some fields might always prefer target values
        target_preference_fields = field_rules.get('target_preference_fields', [])
        if field in target_preference_fields:
            return ConflictResolution.TARGET_WINS
        
        # Check for more complex logic based on field values
        if 'value_based_rules' in field_rules:
            value_rules = field_rules['value_based_rules']
            for rule in value_rules:
                condition = rule.get('condition', {})
                
                # Simple equality condition for source value
                if 'source_value_equals' in condition:
                    if conflict.source_value == condition['source_value_equals']:
                        return ConflictResolution(rule.get('strategy', default_strategy))
                
                # Simple equality condition for target value
                if 'target_value_equals' in condition:
                    if conflict.target_value == condition['target_value_equals']:
                        return ConflictResolution(rule.get('strategy', default_strategy))
                
                # Simple null check for source value
                if condition.get('source_value_is_null', False) and conflict.source_value is None:
                    return ConflictResolution(rule.get('strategy', default_strategy))
                
                # Simple null check for target value
                if condition.get('target_value_is_null', False) and conflict.target_value is None:
                    return ConflictResolution(rule.get('strategy', default_strategy))
        
        # Return the default strategy if no specific rules matched
        return default_strategy
    
    def resolve_conflict(
        self,
        conflict: Conflict,
        strategy: Optional[ConflictResolution] = None
    ) -> Any:
        """
        Resolve a conflict using the specified strategy.
        
        Args:
            conflict: Conflict to resolve
            strategy: Strategy to apply, or None to determine automatically
            
        Returns:
            Resolved value
        """
        # Determine strategy if not provided
        if strategy is None:
            strategy = self.determine_resolution_strategy(
                entity_type=conflict.entity_type,
                field=conflict.field,
                conflict=conflict
            )
        
        # Apply resolution strategy
        if strategy == ConflictResolution.SOURCE_WINS:
            resolved_value = conflict.source_value
        elif strategy == ConflictResolution.TARGET_WINS:
            resolved_value = conflict.target_value
        elif strategy == ConflictResolution.MERGE:
            # Merge strategy depends on the data type
            if isinstance(conflict.source_value, dict) and isinstance(conflict.target_value, dict):
                # For dictionaries, merge keys
                resolved_value = {**conflict.target_value, **conflict.source_value}
            elif isinstance(conflict.source_value, list) and isinstance(conflict.target_value, list):
                # For lists, combine unique values
                resolved_value = list(set(conflict.target_value + conflict.source_value))
            else:
                # For other types, default to source value
                resolved_value = conflict.source_value
        else:
            # For manual resolution, we can't resolve automatically
            # Keeping target value as temporary strategy
            resolved_value = conflict.target_value
        
        # Update the conflict with resolution info
        conflict.resolution = strategy
        conflict.resolved_value = resolved_value
        
        logger.debug(f"Resolved conflict in {conflict.entity_type}.{conflict.field} "
                     f"using {strategy.value} strategy")
        
        return resolved_value
    
    async def resolve_conflicts(
        self,
        entity_type: str,
        transformed_record: TransformedRecord,
        conflicts: List[Conflict]
    ) -> TransformedRecord:
        """
        Resolve all conflicts for a transformed record.
        
        Args:
            entity_type: Type of entity being processed
            transformed_record: Transformed record with conflicts
            conflicts: List of detected conflicts
            
        Returns:
            Updated transformed record with conflicts resolved
        """
        if not conflicts:
            return transformed_record
        
        logger.info(f"Resolving {len(conflicts)} conflicts for {entity_type} record "
                    f"{transformed_record.source_id}")
        
        # Create a copy of the target data to modify
        resolved_data = transformed_record.target_data.copy()
        
        # Process each conflict
        for conflict in conflicts:
            # Resolve the conflict
            resolved_value = self.resolve_conflict(conflict)
            
            # Update the target data with the resolved value
            resolved_data[conflict.field] = resolved_value
            
            # Add a note about the conflict resolution
            transformed_record.transformation_notes.append(
                f"Resolved conflict in field '{conflict.field}' using {conflict.resolution.value} "
                f"strategy: {conflict.source_value} vs {conflict.target_value} -> {resolved_value}"
            )
        
        # Update the transformed record with resolved data
        result = TransformedRecord(
            source_id=transformed_record.source_id,
            target_id=transformed_record.target_id,
            entity_type=transformed_record.entity_type,
            source_data=transformed_record.source_data,
            target_data=resolved_data,
            transformation_notes=transformed_record.transformation_notes
        )
        
        return result
    
    async def heal_invalid_records(
        self,
        entity_type: str,
        transformed_records: List[TransformedRecord],
        validation_results: List[ValidationResult]
    ) -> List[TransformedRecord]:
        """
        Apply healing strategies to invalid records to make them valid.
        
        Args:
            entity_type: Type of entity being processed
            transformed_records: List of transformed records
            validation_results: Validation results for the records
            
        Returns:
            List of healed records
        """
        logger.info(f"Healing invalid {entity_type} records")
        
        healed_records = []
        
        # Process each record and its validation result
        for record, validation in zip(transformed_records, validation_results):
            # If the record is already valid, no healing needed
            if validation.is_valid:
                healed_records.append(record)
                continue
            
            logger.debug(f"Healing {entity_type} record {record.source_id} with "
                         f"{len(validation.errors)} errors")
            
            # Create a copy of the target data to modify
            healed_data = record.target_data.copy()
            healing_notes = list(record.transformation_notes)
            
            # Process each validation error
            for error in validation.errors:
                # Parse the field name from the error message
                # Format is typically "Field 'field_name': error details"
                field_name = None
                if "Field '" in error:
                    field_part = error.split("Field '")[1]
                    if "'" in field_part:
                        field_name = field_part.split("'")[0]
                
                if not field_name:
                    # Can't determine field from error, skip
                    continue
                
                # Apply healing strategy based on the field and error
                # This is a simplified approach; real implementation would be more sophisticated
                
                # Check if it's a required field that's missing
                if "required but missing" in error or "required but was None" in error:
                    # Try to provide a default value
                    healed_data[field_name] = self.get_default_value_for_field(
                        entity_type, field_name)
                    healing_notes.append(
                        f"Healed missing required field '{field_name}' with default value"
                    )
                
                # Check if it's a type error
                elif "must be a" in error:
                    # Try to convert the value to the right type
                    healed_data[field_name] = self.convert_value_type(
                        healed_data.get(field_name), error)
                    healing_notes.append(
                        f"Healed type error in field '{field_name}' with type conversion"
                    )
                
                # Other error types could be handled here
            
            # Create a healed record
            healed_record = TransformedRecord(
                source_id=record.source_id,
                target_id=record.target_id,
                entity_type=record.entity_type,
                source_data=record.source_data,
                target_data=healed_data,
                transformation_notes=healing_notes
            )
            
            healed_records.append(healed_record)
        
        logger.info(f"Healed {len(healed_records)} {entity_type} records")
        
        return healed_records
    
    def get_default_value_for_field(self, entity_type: str, field_name: str) -> Any:
        """
        Get a default value for a field based on entity type and field name.
        
        Args:
            entity_type: Type of entity
            field_name: Name of the field
            
        Returns:
            Default value for the field
        """
        # This would normally be loaded from configuration
        # For now, using simplified defaults
        
        # Common fields with sensible defaults
        if field_name in ['is_active', 'active', 'enabled']:
            return True
        
        if field_name in ['status', 'state']:
            return 'new'
        
        if field_name in ['priority', 'order']:
            return 0
        
        if field_name in ['created_at', 'updated_at', 'modified_at']:
            from datetime import datetime
            return datetime.utcnow().isoformat()
        
        # Return empty string as last resort for string fields
        return ""
    
    def convert_value_type(self, value: Any, error_message: str) -> Any:
        """
        Attempt to convert a value to the right type based on an error message.
        
        Args:
            value: Value to convert
            error_message: Error message containing type information
            
        Returns:
            Converted value
        """
        if value is None:
            return value
        
        try:
            # Determine target type from error message
            if "must be a string" in error_message:
                return str(value)
            
            if "must be an integer" in error_message:
                if isinstance(value, str):
                    # Try to extract numeric part
                    import re
                    numeric_part = re.search(r'\d+', value)
                    if numeric_part:
                        return int(numeric_part.group())
                    
                    return 0
                
                return int(float(value))
            
            if "must be a number" in error_message or "must be a float" in error_message:
                if isinstance(value, str):
                    # Try to extract numeric part
                    import re
                    numeric_part = re.search(r'\d+(\.\d+)?', value)
                    if numeric_part:
                        return float(numeric_part.group())
                    
                    return 0.0
                
                return float(value)
            
            if "must be a boolean" in error_message:
                if isinstance(value, str):
                    return value.lower() in ['true', 'yes', 'y', '1', 't']
                
                return bool(value)
            
            if "must be a date" in error_message:
                if isinstance(value, str):
                    from datetime import datetime
                    # Try common date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
                        try:
                            return datetime.strptime(value, fmt).isoformat()
                        except ValueError:
                            continue
                
                return value
            
            # Default to returning the original value
            return value
            
        except Exception as e:
            logger.error(f"Error converting value type: {str(e)}")
            return value