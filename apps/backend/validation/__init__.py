"""
Validation package for TerraFusion SyncService.

This package provides validation functionality for data synchronization
between PACS and CAMA systems.
"""

from apps.backend.validation.schema import (
    ValidationLevel,
    ValidationRule,
    RequiredFieldRule,
    TypeRule,
    RangeRule,
    PatternRule,
    EnumRule,
    DateFormatRule,
    CustomRule,
    ValidationSchema,
    PACSImageSchema,
    CAMAPropertySchema,
    create_validation_schema
)

from apps.backend.validation.engine import (
    ValidationEngine,
    ValidationResult,
    get_validation_engine,
    validate,
    validate_batch,
    register_schema,
    add_schema
)

__all__ = [
    # Schema classes
    'ValidationLevel',
    'ValidationRule',
    'RequiredFieldRule',
    'TypeRule',
    'RangeRule',
    'PatternRule',
    'EnumRule',
    'DateFormatRule',
    'CustomRule',
    'ValidationSchema',
    'PACSImageSchema',
    'CAMAPropertySchema',
    'create_validation_schema',
    
    # Engine classes and functions
    'ValidationEngine',
    'ValidationResult',
    'get_validation_engine',
    'validate',
    'validate_batch',
    'register_schema',
    'add_schema'
]