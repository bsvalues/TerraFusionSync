"""
Validator component for the SyncService.

This module is responsible for validating transformed data before
it is written to the target system, including data integrity checks
and business rule validation.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

from pydantic import ValidationError

from syncservice.models.cama import (CAMAOwnerSchema, CAMAPropertySchema,
                                   CAMAStructureSchema, CAMAValueSchema)
from syncservice.utils.event_bus import publish_event

logger = logging.getLogger(__name__)


class Validator:
    """Validates data integrity and business rules for transformed records."""

    def __init__(self):
        """Initialize the Validator component."""
        pass

    async def validate_property(
        self, 
        property_data: CAMAPropertySchema
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a property record.
        
        Args:
            property_data: Property data to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if not property_data.parcel_number:
            errors.append("Parcel number is required")
            
        # Validate parcel number format (example: must be alphanumeric with dashes)
        if property_data.parcel_number and not re.match(r'^[A-Z0-9\-]+$', property_data.parcel_number):
            errors.append("Parcel number must contain only letters, numbers, and dashes")
            
        # Validate address if present
        if property_data.address and len(property_data.address) < 5:
            errors.append("Address must be at least 5 characters long")
            
        # Validate state if present
        if property_data.state and len(property_data.state) != 2:
            errors.append("State must be a 2-letter code")
            
        # Validate acreage if present
        if property_data.acreage is not None and property_data.acreage <= 0:
            errors.append("Acreage must be greater than 0")
            
        # Validate year built if present
        current_year = datetime.now().year
        if property_data.year_built is not None:
            if property_data.year_built < 1700 or property_data.year_built > current_year:
                errors.append(f"Year built must be between 1700 and {current_year}")
        
        # Log validation result
        if errors:
            logger.warning(f"Property validation failed for {property_data.id}: {errors}")
            
            # Publish validation event
            await publish_event(
                "property_validation_failed",
                {
                    "record_id": property_data.id,
                    "source_id": property_data.source_id,
                    "errors": errors,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return False, errors
        
        # Publish validation event
        await publish_event(
            "property_validation_passed",
            {
                "record_id": property_data.id,
                "source_id": property_data.source_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True, None

    async def validate_owner(
        self, 
        owner_data: CAMAOwnerSchema,
        property_exists: bool
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate an owner record.
        
        Args:
            owner_data: Owner data to validate
            property_exists: Whether the referenced property exists
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if not owner_data.owner_name:
            errors.append("Owner name is required")
            
        # Check property reference
        if not property_exists:
            errors.append(f"Referenced property {owner_data.property_id} does not exist")
            
        # Validate ownership percentage if present
        if owner_data.ownership_percentage is not None:
            if owner_data.ownership_percentage <= 0 or owner_data.ownership_percentage > 100:
                errors.append("Ownership percentage must be between 0 and 100")
                
        # Validate date ranges if both present
        if owner_data.start_date and owner_data.end_date:
            if owner_data.start_date > owner_data.end_date:
                errors.append("Start date cannot be after end date")
        
        # Log validation result
        if errors:
            logger.warning(f"Owner validation failed for {owner_data.id}: {errors}")
            
            # Publish validation event
            await publish_event(
                "owner_validation_failed",
                {
                    "record_id": owner_data.id,
                    "source_id": owner_data.source_id,
                    "errors": errors,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return False, errors
        
        # Publish validation event
        await publish_event(
            "owner_validation_passed",
            {
                "record_id": owner_data.id,
                "source_id": owner_data.source_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True, None

    async def validate_value(
        self, 
        value_data: CAMAValueSchema,
        property_exists: bool
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a value record.
        
        Args:
            value_data: Value data to validate
            property_exists: Whether the referenced property exists
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if value_data.tax_year is None:
            errors.append("Tax year is required")
            
        # Check property reference
        if not property_exists:
            errors.append(f"Referenced property {value_data.property_id} does not exist")
            
        # Validate tax year
        current_year = datetime.now().year
        if value_data.tax_year is not None:
            if value_data.tax_year < 1900 or value_data.tax_year > current_year + 1:
                errors.append(f"Tax year must be between 1900 and {current_year + 1}")
                
        # Validate value fields
        if value_data.assessed_value is not None and value_data.assessed_value < 0:
            errors.append("Assessed value cannot be negative")
            
        if value_data.market_value is not None and value_data.market_value < 0:
            errors.append("Market value cannot be negative")
            
        if value_data.land_value is not None and value_data.land_value < 0:
            errors.append("Land value cannot be negative")
            
        if value_data.improvement_value is not None and value_data.improvement_value < 0:
            errors.append("Improvement value cannot be negative")
            
        # Validate consistency between values
        if (value_data.land_value is not None and 
            value_data.improvement_value is not None and 
            value_data.market_value is not None):
            # Sum of land and improvement values should be close to market value
            total = value_data.land_value + value_data.improvement_value
            if abs(total - value_data.market_value) > 1.0:  # Allow for small rounding differences
                errors.append("Sum of land and improvement values should equal market value")
        
        # Log validation result
        if errors:
            logger.warning(f"Value validation failed for {value_data.id}: {errors}")
            
            # Publish validation event
            await publish_event(
                "value_validation_failed",
                {
                    "record_id": value_data.id,
                    "source_id": value_data.source_id,
                    "errors": errors,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return False, errors
        
        # Publish validation event
        await publish_event(
            "value_validation_passed",
            {
                "record_id": value_data.id,
                "source_id": value_data.source_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True, None

    async def validate_structure(
        self, 
        structure_data: CAMAStructureSchema,
        property_exists: bool
    ) -> Tuple[bool, Optional[List[str]]]:
        """
        Validate a structure record.
        
        Args:
            structure_data: Structure data to validate
            property_exists: Whether the referenced property exists
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        if not structure_data.structure_type:
            errors.append("Structure type is required")
            
        # Check property reference
        if not property_exists:
            errors.append(f"Referenced property {structure_data.property_id} does not exist")
            
        # Validate square footage if present
        if structure_data.square_footage is not None and structure_data.square_footage <= 0:
            errors.append("Square footage must be greater than 0")
            
        # Validate year built if present
        current_year = datetime.now().year
        if structure_data.year_built is not None:
            if structure_data.year_built < 1700 or structure_data.year_built > current_year:
                errors.append(f"Year built must be between 1700 and {current_year}")
                
        # Validate bedrooms if present
        if structure_data.bedrooms is not None and structure_data.bedrooms < 0:
            errors.append("Number of bedrooms cannot be negative")
            
        # Validate bathrooms if present
        if structure_data.bathrooms is not None and structure_data.bathrooms < 0:
            errors.append("Number of bathrooms cannot be negative")
        
        # Log validation result
        if errors:
            logger.warning(f"Structure validation failed for {structure_data.id}: {errors}")
            
            # Publish validation event
            await publish_event(
                "structure_validation_failed",
                {
                    "record_id": structure_data.id,
                    "source_id": structure_data.source_id,
                    "errors": errors,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return False, errors
        
        # Publish validation event
        await publish_event(
            "structure_validation_passed",
            {
                "record_id": structure_data.id,
                "source_id": structure_data.source_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        return True, None

    async def batch_validate_records(
        self, 
        transformed_records: Dict[str, List]
    ) -> Dict:
        """
        Validate a batch of transformed records.
        
        Args:
            transformed_records: Dictionary containing transformed records by entity type
            
        Returns:
            Dictionary with validation results by entity type
        """
        logger.info("Starting batch validation of records")
        
        # Extract records by type
        properties = transformed_records.get("properties", [])
        owners = transformed_records.get("owners", [])
        values = transformed_records.get("values", [])
        structures = transformed_records.get("structures", [])
        
        # Create sets for quick lookups
        valid_property_ids = set()
        
        # Validation results
        valid_properties = []
        invalid_properties = []
        valid_owners = []
        invalid_owners = []
        valid_values = []
        invalid_values = []
        valid_structures = []
        invalid_structures = []
        
        # First validate all properties
        for property_data in properties:
            is_valid, errors = await self.validate_property(property_data)
            if is_valid:
                valid_properties.append(property_data)
                valid_property_ids.add(property_data.id)
            else:
                invalid_properties.append((property_data, errors))
        
        # Then validate owners, checking property references
        for owner_data in owners:
            property_exists = owner_data.property_id in valid_property_ids
            is_valid, errors = await self.validate_owner(owner_data, property_exists)
            if is_valid:
                valid_owners.append(owner_data)
            else:
                invalid_owners.append((owner_data, errors))
        
        # Validate values, checking property references
        for value_data in values:
            property_exists = value_data.property_id in valid_property_ids
            is_valid, errors = await self.validate_value(value_data, property_exists)
            if is_valid:
                valid_values.append(value_data)
            else:
                invalid_values.append((value_data, errors))
        
        # Validate structures, checking property references
        for structure_data in structures:
            property_exists = structure_data.property_id in valid_property_ids
            is_valid, errors = await self.validate_structure(structure_data, property_exists)
            if is_valid:
                valid_structures.append(structure_data)
            else:
                invalid_structures.append((structure_data, errors))
        
        # Calculate stats
        total_records = len(properties) + len(owners) + len(values) + len(structures)
        valid_records = len(valid_properties) + len(valid_owners) + len(valid_values) + len(valid_structures)
        invalid_records = total_records - valid_records
        
        # Publish validation summary event
        await publish_event(
            "batch_validation_completed",
            {
                "timestamp": datetime.utcnow().isoformat(),
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": invalid_records,
                "validation_rate": round(valid_records / total_records * 100, 2) if total_records > 0 else 0
            }
        )
        
        return {
            "valid": {
                "properties": valid_properties,
                "owners": valid_owners,
                "values": valid_values,
                "structures": valid_structures
            },
            "invalid": {
                "properties": invalid_properties,
                "owners": invalid_owners,
                "values": invalid_values,
                "structures": invalid_structures
            },
            "stats": {
                "total_records": total_records,
                "valid_records": valid_records,
                "invalid_records": invalid_records
            }
        }
