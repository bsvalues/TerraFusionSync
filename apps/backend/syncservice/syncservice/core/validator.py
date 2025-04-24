"""
Validator module for the SyncService.

This module is responsible for validating data before it is written to target systems,
ensuring that it meets the required structure and constraints.
"""

import logging
import re
import yaml
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Callable, Union, Tuple

from ..models.base import TransformedRecord, ValidationResult

logger = logging.getLogger(__name__)


# Type for validation functions
ValidatorFunc = Callable[[Any, Dict[str, Any]], Tuple[bool, Optional[str]]]


class Validator:
    """
    Component responsible for validating data before writing to target systems.
    
    This component ensures that data meets the required structure and constraints
    before it is written to target systems.
    """
    
    def __init__(self, validation_rules_path: Optional[str] = None):
        """
        Initialize the Validator.
        
        Args:
            validation_rules_path: Path to the validation rules configuration file
        """
        self.validation_rules_path = validation_rules_path
        self.validation_rules = {}
        self.validators = {}
        
        # Load validation rules if path provided
        if validation_rules_path:
            self.load_validation_rules()
        
        # Register default validators
        self.register_default_validators()
    
    def load_validation_rules(self):
        """
        Load validation rules from a YAML file.
        
        The validation rules define constraints and requirements for fields
        in different entity types.
        """
        try:
            if not os.path.exists(self.validation_rules_path):
                logger.warning(f"Validation rules file not found: {self.validation_rules_path}")
                return
            
            with open(self.validation_rules_path, 'r') as f:
                config = yaml.safe_load(f)
            
            self.validation_rules = config.get('validation_rules', {})
            
            logger.info(f"Loaded validation rules for {len(self.validation_rules)} entity types")
            
        except Exception as e:
            logger.error(f"Error loading validation rules: {str(e)}")
            raise
    
    def register_default_validators(self):
        """
        Register default validator functions.
        
        These functions can be referenced in the validation rules configuration
        to validate field values.
        """
        # Required field validator
        self.register_validator('required', self._validate_required)
        
        # Type validators
        self.register_validator('type_string', self._validate_string)
        self.register_validator('type_integer', self._validate_integer)
        self.register_validator('type_float', self._validate_float)
        self.register_validator('type_boolean', self._validate_boolean)
        self.register_validator('type_date', self._validate_date)
        self.register_validator('type_email', self._validate_email)
        
        # Length validators
        self.register_validator('min_length', self._validate_min_length)
        self.register_validator('max_length', self._validate_max_length)
        
        # Range validators
        self.register_validator('min_value', self._validate_min_value)
        self.register_validator('max_value', self._validate_max_value)
        
        # Pattern validator
        self.register_validator('pattern', self._validate_pattern)
        
        # Enumeration validator
        self.register_validator('enum', self._validate_enum)
        
        # Relationship validator
        self.register_validator('relationship', self._validate_relationship)
    
    def register_validator(self, name: str, func: ValidatorFunc):
        """
        Register a validator function.
        
        Args:
            name: Name of the validator
            func: Validator function
        """
        self.validators[name] = func
        logger.debug(f"Registered validator: {name}")
    
    def _validate_required(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is not None or empty.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return False, "Value is required but was None"
        
        if isinstance(value, (str, list, dict)) and len(value) == 0:
            return False, "Value is required but was empty"
        
        return True, None
    
    def _validate_string(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a string.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if not isinstance(value, str):
            return False, f"Value must be a string but was {type(value).__name__}"
        
        return True, None
    
    def _validate_integer(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is an integer.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if not isinstance(value, int) or isinstance(value, bool):
            return False, f"Value must be an integer but was {type(value).__name__}"
        
        return True, None
    
    def _validate_float(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a float.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, f"Value must be a number but was {type(value).__name__}"
        
        return True, None
    
    def _validate_boolean(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a boolean.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if not isinstance(value, bool):
            return False, f"Value must be a boolean but was {type(value).__name__}"
        
        return True, None
    
    def _validate_date(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a date or can be parsed as a date.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if isinstance(value, datetime):
            return True, None
        
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True, None
            except (ValueError, TypeError):
                return False, f"Value must be a valid date string but was '{value}'"
        
        return False, f"Value must be a date but was {type(value).__name__}"
    
    def _validate_email(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is a valid email address.
        
        Args:
            value: Value to validate
            params: Validation parameters
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        if not isinstance(value, str):
            return False, f"Email must be a string but was {type(value).__name__}"
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            return False, f"'{value}' is not a valid email address"
        
        return True, None
    
    def _validate_min_length(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value has at least a minimum length.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'min_length'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        min_length = params.get('min_length', 0)
        
        if not isinstance(value, (str, list, dict)):
            return False, f"Cannot check length of {type(value).__name__}"
        
        if len(value) < min_length:
            return False, f"Length must be at least {min_length} but was {len(value)}"
        
        return True, None
    
    def _validate_max_length(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value does not exceed a maximum length.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'max_length'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        max_length = params.get('max_length', float('inf'))
        
        if not isinstance(value, (str, list, dict)):
            return False, f"Cannot check length of {type(value).__name__}"
        
        if len(value) > max_length:
            return False, f"Length must not exceed {max_length} but was {len(value)}"
        
        return True, None
    
    def _validate_min_value(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is at least a minimum value.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'min_value'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        min_value = params.get('min_value', float('-inf'))
        
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, f"Cannot compare {type(value).__name__} to minimum value"
        
        if value < min_value:
            return False, f"Value must be at least {min_value} but was {value}"
        
        return True, None
    
    def _validate_max_value(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value does not exceed a maximum value.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'max_value'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        max_value = params.get('max_value', float('inf'))
        
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return False, f"Cannot compare {type(value).__name__} to maximum value"
        
        if value > max_value:
            return False, f"Value must not exceed {max_value} but was {value}"
        
        return True, None
    
    def _validate_pattern(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value matches a regular expression pattern.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'pattern'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        pattern = params.get('pattern')
        if not pattern:
            return False, "No pattern specified for pattern validation"
        
        if not isinstance(value, str):
            return False, f"Pattern validation requires a string but got {type(value).__name__}"
        
        if not re.match(pattern, value):
            return False, f"Value '{value}' does not match pattern '{pattern}'"
        
        return True, None
    
    def _validate_enum(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a value is one of a set of allowed values.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'allowed_values'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        allowed_values = params.get('allowed_values', [])
        if not allowed_values:
            return False, "No allowed values specified for enum validation"
        
        if value not in allowed_values:
            return False, f"Value must be one of {allowed_values} but was '{value}'"
        
        return True, None
    
    def _validate_relationship(self, value: Any, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate that a relationship field refers to a valid entity.
        
        Note: This is a stub implementation. In a real system, this would check
        against a database or other source of truth.
        
        Args:
            value: Value to validate
            params: Validation parameters including 'entity_type'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if value is None:
            return True, None
        
        entity_type = params.get('entity_type')
        if not entity_type:
            return False, "No entity type specified for relationship validation"
        
        # In a real implementation, this would check if the referenced entity exists
        logger.info(f"Relationship validation for {entity_type} with ID {value} "
                    f"would be performed here")
        
        return True, None
    
    def validate_field(
        self,
        field_name: str,
        value: Any,
        validation_rules: Dict[str, Any]
    ) -> List[str]:
        """
        Validate a single field.
        
        Args:
            field_name: Name of the field
            value: Field value to validate
            validation_rules: Rules to apply
            
        Returns:
            List of validation error messages, empty if valid
        """
        errors = []
        
        for rule_name, rule_params in validation_rules.items():
            if rule_name not in self.validators:
                logger.warning(f"Unknown validator: {rule_name}")
                continue
            
            validator_func = self.validators[rule_name]
            is_valid, error = validator_func(value, rule_params)
            
            if not is_valid and error:
                errors.append(f"Field '{field_name}': {error}")
        
        return errors
    
    def validate_record(
        self,
        entity_type: str,
        data: Dict[str, Any],
        entity_id: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate a record against the rules for its entity type.
        
        Args:
            entity_type: Type of entity to validate
            data: Record data to validate
            entity_id: ID of the entity, if known
            
        Returns:
            Validation result
        """
        logger.debug(f"Validating {entity_type} record {entity_id or 'unknown'}")
        
        # Get validation rules for this entity type
        entity_rules = self.validation_rules.get(entity_type, {})
        if not entity_rules:
            logger.warning(f"No validation rules found for {entity_type}")
            # If no rules defined, consider it valid
            return ValidationResult(
                is_valid=True,
                entity_type=entity_type,
                entity_id=entity_id or "unknown"
            )
        
        # Initialize validation result
        errors = []
        warnings = []
        
        # Validate each field against its rules
        for field_name, field_rules in entity_rules.items():
            field_value = data.get(field_name)
            
            # Validate required fields
            if field_rules.get('required', False) and field_name not in data:
                errors.append(f"Field '{field_name}' is required but missing")
                continue
            
            # Skip validation for missing optional fields
            if field_name not in data:
                continue
            
            # Validate field against rules
            field_errors = self.validate_field(field_name, field_value, field_rules)
            errors.extend(field_errors)
        
        # Create and return validation result
        return ValidationResult(
            is_valid=len(errors) == 0,
            entity_type=entity_type,
            entity_id=entity_id or "unknown",
            errors=errors,
            warnings=warnings
        )
    
    async def batch_validate_records(
        self,
        entity_type: str,
        records: List[Union[TransformedRecord, Dict[str, Any]]]
    ) -> List[ValidationResult]:
        """
        Validate multiple records in a batch.
        
        Args:
            entity_type: Type of entity to validate
            records: List of records to validate
            
        Returns:
            List of validation results
        """
        logger.info(f"Batch validating {len(records)} {entity_type} records")
        
        validation_results = []
        
        for record in records:
            # Extract record data and ID
            if isinstance(record, TransformedRecord):
                data = record.target_data
                entity_id = record.source_id
            else:
                data = record.get('data', {})
                entity_id = record.get('id') or record.get('source_id')
            
            # Validate the record
            result = self.validate_record(
                entity_type=entity_type,
                data=data,
                entity_id=entity_id
            )
            
            validation_results.append(result)
        
        # Log validation summary
        valid_count = sum(1 for r in validation_results if r.is_valid)
        invalid_count = len(validation_results) - valid_count
        logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid")
        
        return validation_results