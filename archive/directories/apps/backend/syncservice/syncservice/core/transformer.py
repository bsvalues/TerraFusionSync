"""
Transformer module for the SyncService.

This module is responsible for transforming data from source system format to target
system format, applying field mappings and transformations.
"""

import logging
import yaml
import os
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from functools import partial

from ..models.base import SourceRecord, TransformedRecord

logger = logging.getLogger(__name__)


# Type for transformation functions
TransformFunc = Callable[[Any], Any]


class Transformer:
    """
    Component responsible for transforming data from source to target format.
    
    This component applies field mappings and transformations to convert data
    from the source system format to the target system format.
    """
    
    def __init__(self, field_mapping_path: str):
        """
        Initialize the Transformer.
        
        Args:
            field_mapping_path: Path to the field mapping configuration file
        """
        self.field_mapping_path = field_mapping_path
        self.field_mappings = {}
        self.transformations = {}
        self.load_field_mapping()
        self.register_default_transformations()
    
    def load_field_mapping(self):
        """
        Load field mapping configuration from a YAML file.
        
        The field mapping configuration defines how fields in the source system
        map to fields in the target system, as well as any transformations that
        need to be applied.
        """
        try:
            if not os.path.exists(self.field_mapping_path):
                logger.warning(f"Field mapping file not found: {self.field_mapping_path}")
                return
            
            with open(self.field_mapping_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.field_mappings = config.get('field_mappings', {})
            
            logger.info(f"Loaded field mappings for {len(self.field_mappings)} entity types")
            
        except Exception as e:
            logger.error(f"Error loading field mapping: {str(e)}")
            raise
    
    def register_default_transformations(self):
        """
        Register default transformation functions.
        
        These functions can be referenced in the field mapping configuration
        to transform field values.
        """
        # String transformations
        self.register_transformation('uppercase', lambda x: x.upper() if x else x)
        self.register_transformation('lowercase', lambda x: x.lower() if x else x)
        self.register_transformation('capitalize', lambda x: x.capitalize() if x else x)
        self.register_transformation('trim', lambda x: x.strip() if x else x)
        
        # Numeric transformations
        self.register_transformation('to_int', lambda x: int(x) if x else 0)
        self.register_transformation('to_float', lambda x: float(x) if x else 0.0)
        
        # Boolean transformations
        self.register_transformation('to_bool', lambda x: bool(x) if x is not None else False)
        self.register_transformation('invert_bool', lambda x: not bool(x) if x is not None else True)
        
        # Date transformations
        self.register_transformation('format_date', 
                                    lambda x, fmt='%Y-%m-%d': x.strftime(fmt) if x else None)
        
        # Special transformations
        self.register_transformation('join_fields', 
                                    lambda x, sep=' ': sep.join(x) if isinstance(x, list) else x)
        self.register_transformation('split_field', 
                                    lambda x, sep=' ': x.split(sep) if x else [])
    
    def register_transformation(self, name: str, func: TransformFunc):
        """
        Register a transformation function.
        
        Args:
            name: Name of the transformation
            func: Transformation function
        """
        self.transformations[name] = func
        logger.debug(f"Registered transformation: {name}")
    
    def get_transformation(self, transform_spec: Dict[str, Any]) -> TransformFunc:
        """
        Get a transformation function based on a specification.
        
        Args:
            transform_spec: Transformation specification
            
        Returns:
            Transformation function
        """
        transform_name = transform_spec.get('name')
        if not transform_name or transform_name not in self.transformations:
            logger.warning(f"Unknown transformation: {transform_name}")
            return lambda x: x
        
        func = self.transformations[transform_name]
        args = transform_spec.get('args', {})
        
        # Create a partial function with the specified arguments
        if args:
            return partial(func, **args)
        
        return func
    
    def apply_transformations(
        self,
        value: Any,
        transformations: List[Dict[str, Any]]
    ) -> Any:
        """
        Apply a series of transformations to a value.
        
        Args:
            value: Value to transform
            transformations: List of transformation specifications
            
        Returns:
            Transformed value
        """
        result = value
        
        for transform_spec in transformations:
            transform_func = self.get_transformation(transform_spec)
            try:
                result = transform_func(result)
            except Exception as e:
                logger.error(f"Error applying transformation {transform_spec}: {str(e)}")
                # Continue with original value if transformation fails
        
        return result
    
    def transform_field(
        self,
        source_field: str,
        target_field: str,
        value: Any,
        field_config: Dict[str, Any]
    ) -> Any:
        """
        Transform a single field.
        
        Args:
            source_field: Source field name
            target_field: Target field name
            value: Field value to transform
            field_config: Field configuration
            
        Returns:
            Transformed field value
        """
        # Apply transformations if specified
        transformations = field_config.get('transformations', [])
        if transformations:
            value = self.apply_transformations(value, transformations)
        
        # Apply default value if original value is None and default is specified
        if value is None and 'default' in field_config:
            value = field_config['default']
        
        return value
    
    def transform_record(
        self,
        entity_type: str,
        source_record: Union[SourceRecord, Dict[str, Any]],
        target_id: Optional[str] = None
    ) -> TransformedRecord:
        """
        Transform a record from source format to target format.
        
        Args:
            entity_type: Type of entity to transform
            source_record: Source record to transform
            target_id: ID of the existing target record, if any
            
        Returns:
            Transformed record
        """
        # Extract source data
        if isinstance(source_record, SourceRecord):
            source_id = source_record.source_id
            source_data = source_record.data
        else:
            source_id = source_record.get('source_id', '')
            source_data = source_record.get('data', {})
        
        logger.debug(f"Transforming {entity_type} record {source_id}")
        
        # Get field mapping for this entity type
        entity_mapping = self.field_mappings.get(entity_type, {})
        if not entity_mapping:
            logger.warning(f"No field mapping found for {entity_type}")
            # Return the source data unchanged if no mapping exists
            return TransformedRecord(
                source_id=source_id,
                target_id=target_id,
                entity_type=entity_type,
                source_data=source_data,
                target_data=source_data.copy(),
                transformation_notes=["No field mapping available, using source data unchanged"]
            )
        
        # Initialize target data and transformation notes
        target_data = {}
        transformation_notes = []
        
        # Process field mappings
        for source_field, field_config in entity_mapping.items():
            # Skip if not a valid field configuration
            if not isinstance(field_config, dict):
                continue
            
            # Get target field name
            target_field = field_config.get('target_field', source_field)
            
            # Skip if field is not in source data and no default value
            if source_field not in source_data and 'default' not in field_config:
                continue
            
            # Get source value or None if not present
            source_value = source_data.get(source_field)
            
            # Transform the field
            target_value = self.transform_field(
                source_field, target_field, source_value, field_config
            )
            
            # Add to target data
            target_data[target_field] = target_value
            
            # Add transformation note if value changed
            if source_value != target_value:
                transformation_notes.append(
                    f"Transformed {source_field} to {target_field}: "
                    f"{source_value} -> {target_value}"
                )
        
        # Create and return the transformed record
        return TransformedRecord(
            source_id=source_id,
            target_id=target_id,
            entity_type=entity_type,
            source_data=source_data,
            target_data=target_data,
            transformation_notes=transformation_notes
        )
    
    async def batch_transform_records(
        self,
        entity_type: str,
        source_records: List[Union[SourceRecord, Dict[str, Any]]],
        target_id_map: Optional[Dict[str, str]] = None
    ) -> List[TransformedRecord]:
        """
        Transform multiple records in a batch.
        
        Args:
            entity_type: Type of entity to transform
            source_records: List of source records to transform
            target_id_map: Mapping of source IDs to target IDs for existing records
            
        Returns:
            List of transformed records
        """
        logger.info(f"Batch transforming {len(source_records)} {entity_type} records")
        
        target_id_map = target_id_map or {}
        transformed_records = []
        
        for source_record in source_records:
            # Get source ID
            if isinstance(source_record, SourceRecord):
                source_id = source_record.source_id
            else:
                source_id = source_record.get('source_id', '')
            
            # Get target ID if available
            target_id = target_id_map.get(source_id)
            
            # Transform the record
            transformed_record = self.transform_record(
                entity_type=entity_type,
                source_record=source_record,
                target_id=target_id
            )
            
            transformed_records.append(transformed_record)
        
        logger.info(f"Transformed {len(transformed_records)} {entity_type} records")
        
        return transformed_records