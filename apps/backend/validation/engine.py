"""
Data Validation Engine for TerraFusion SyncService.

This module provides the validation engine that applies validation schemas
to data being synchronized between PACS and CAMA systems.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime

from apps.backend.validation.schema import (
    ValidationSchema, ValidationLevel,
    PACSImageSchema, CAMAPropertySchema,
    create_validation_schema
)

logger = logging.getLogger(__name__)


class ValidationEngine:
    """
    Engine for validating data against schemas.
    
    This class handles the validation of data against schemas, including
    reporting validation errors and handling validation failures.
    """
    
    def __init__(self, schemas: Dict[str, ValidationSchema] = None):
        """
        Initialize the validation engine.
        
        Args:
            schemas: Dictionary of validation schemas, keyed by schema name
        """
        self.schemas = schemas if schemas is not None else {}
        self._load_default_schemas()
        self.validation_history = []
        
    def _load_default_schemas(self):
        """Load default schemas if not provided."""
        if "pacs_image" not in self.schemas:
            self.schemas["pacs_image"] = PACSImageSchema()
        
        if "cama_property" not in self.schemas:
            self.schemas["cama_property"] = CAMAPropertySchema()
    
    def register_schema(self, schema: ValidationSchema):
        """
        Register a validation schema with the engine.
        
        Args:
            schema: The validation schema to register
        """
        self.schemas[schema.schema_name] = schema
        logger.info(f"Registered validation schema: {schema.schema_name}")
        
    def add_schema(self, schema: ValidationSchema):
        """
        Add a validation schema to the engine.
        
        This is an alias for register_schema to maintain API compatibility.
        
        Args:
            schema: The validation schema to add
        """
        self.register_schema(schema)
    
    def validate(self, data: Dict[str, Any], schema_name: str) -> Dict[str, Any]:
        """
        Validate data against a schema.
        
        Args:
            data: The data to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            Dict with validation results:
                {
                    "valid": bool,
                    "errors": List[Dict],
                    "warnings": List[Dict],
                    "info": List[Dict],
                    "schema_name": str,
                    "timestamp": str
                }
                
        Raises:
            ValueError: If the schema is not found
        """
        if schema_name not in self.schemas:
            raise ValueError(f"Schema not found: {schema_name}")
        
        schema = self.schemas[schema_name]
        
        start_time = time.time()
        results = schema.validate(data)
        end_time = time.time()
        
        # Add metadata to results
        results["schema_name"] = schema_name
        results["timestamp"] = datetime.utcnow().isoformat()
        results["validation_time"] = end_time - start_time
        
        # Log validation results
        self._log_validation_results(results, data)
        
        # Add to history
        self.validation_history.append({
            "schema_name": schema_name,
            "timestamp": results["timestamp"],
            "valid": results["valid"],
            "error_count": len(results["errors"]),
            "warning_count": len(results["warnings"]),
            "info_count": len(results["info"])
        })
        
        # Trim history if it gets too long
        if len(self.validation_history) > 100:
            self.validation_history = self.validation_history[-100:]
        
        return results
    
    def validate_batch(self, data_items: List[Dict[str, Any]], schema_name: str) -> List[Dict[str, Any]]:
        """
        Validate a batch of data items against a schema.
        
        Args:
            data_items: List of data items to validate
            schema_name: The name of the schema to validate against
            
        Returns:
            List of validation results, one for each data item
        """
        return [self.validate(item, schema_name) for item in data_items]
    
    def validate_multi_schema(self, data: Dict[str, Any], schema_names: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Validate data against multiple schemas.
        
        Args:
            data: The data to validate
            schema_names: List of schema names to validate against
            
        Returns:
            Dict of validation results, keyed by schema name
        """
        return {name: self.validate(data, name) for name in schema_names}
    
    def _log_validation_results(self, results: Dict[str, Any], data: Dict[str, Any]):
        """
        Log validation results.
        
        Args:
            results: Validation results to log
            data: The data that was validated
        """
        schema_name = results["schema_name"]
        valid = results["valid"]
        error_count = len(results["errors"])
        warning_count = len(results["warnings"])
        info_count = len(results["info"])
        
        if valid:
            logger.info(f"Validation passed for schema '{schema_name}': {error_count} errors, {warning_count} warnings, {info_count} info")
        else:
            logger.warning(f"Validation failed for schema '{schema_name}': {error_count} errors, {warning_count} warnings, {info_count} info")
            
            # Log errors
            for error in results["errors"]:
                logger.error(f"Validation error in field '{error['field_name']}': {error['message']}")
            
            # Log warnings
            for warning in results["warnings"]:
                logger.warning(f"Validation warning in field '{warning['field_name']}': {warning['message']}")
    
    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get the validation history."""
        return self.validation_history
    
    def clear_validation_history(self):
        """Clear the validation history."""
        self.validation_history = []


class ValidationResult:
    """
    Class to represent a validation result.
    
    This class provides methods for handling and formatting validation results.
    """
    
    def __init__(self, results: Dict[str, Any]):
        """
        Initialize the validation result.
        
        Args:
            results: The validation results from ValidationEngine.validate()
        """
        self.results = results
        self.valid = results["valid"]
        self.errors = results["errors"]
        self.warnings = results["warnings"]
        self.info = results["info"]
        self.schema_name = results["schema_name"]
        self.timestamp = results["timestamp"]
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """Get validation errors."""
        return self.errors
    
    def get_warnings(self) -> List[Dict[str, Any]]:
        """Get validation warnings."""
        return self.warnings
    
    def get_info(self) -> List[Dict[str, Any]]:
        """Get validation info."""
        return self.info
    
    def get_all_issues(self) -> List[Dict[str, Any]]:
        """Get all validation issues (errors, warnings, and info)."""
        return self.errors + self.warnings + self.info
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the validation results.
        
        Returns:
            Dict with validation summary
        """
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "info_count": len(self.info),
            "schema_name": self.schema_name,
            "timestamp": self.timestamp
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.results
    
    def format_as_text(self) -> str:
        """
        Format validation results as text.
        
        Returns:
            String representation of validation results
        """
        lines = []
        lines.append(f"Validation results for schema '{self.schema_name}':")
        lines.append(f"Timestamp: {self.timestamp}")
        lines.append(f"Valid: {self.valid}")
        lines.append("")
        
        if self.errors:
            lines.append("Errors:")
            for error in self.errors:
                lines.append(f"  - Field '{error['field_name']}': {error['message']}")
            lines.append("")
        
        if self.warnings:
            lines.append("Warnings:")
            for warning in self.warnings:
                lines.append(f"  - Field '{warning['field_name']}': {warning['message']}")
            lines.append("")
        
        if self.info:
            lines.append("Information:")
            for info in self.info:
                lines.append(f"  - Field '{info['field_name']}': {info['message']}")
        
        return "\n".join(lines)
    
    def format_as_html(self) -> str:
        """
        Format validation results as HTML.
        
        Returns:
            HTML representation of validation results
        """
        html = []
        html.append(f"<h3>Validation results for schema '{self.schema_name}'</h3>")
        html.append(f"<p>Timestamp: {self.timestamp}</p>")
        html.append(f"<p>Valid: {self.valid}</p>")
        
        if self.errors:
            html.append("<h4>Errors:</h4>")
            html.append("<ul class='error-list'>")
            for error in self.errors:
                html.append(f"<li>Field '{error['field_name']}': {error['message']}</li>")
            html.append("</ul>")
        
        if self.warnings:
            html.append("<h4>Warnings:</h4>")
            html.append("<ul class='warning-list'>")
            for warning in self.warnings:
                html.append(f"<li>Field '{warning['field_name']}': {warning['message']}</li>")
            html.append("</ul>")
        
        if self.info:
            html.append("<h4>Information:</h4>")
            html.append("<ul class='info-list'>")
            for info in self.info:
                html.append(f"<li>Field '{info['field_name']}': {info['message']}</li>")
            html.append("</ul>")
        
        return "".join(html)


# Singleton instance of the validation engine
_validation_engine = None

def get_validation_engine() -> ValidationEngine:
    """
    Get the singleton validation engine instance.
    
    Returns:
        ValidationEngine: The validation engine
    """
    global _validation_engine
    if _validation_engine is None:
        _validation_engine = ValidationEngine()
    return _validation_engine

def validate(data: Dict[str, Any], schema_name: str) -> ValidationResult:
    """
    Validate data against a schema.
    
    Args:
        data: The data to validate
        schema_name: The name of the schema to validate against
        
    Returns:
        ValidationResult: The validation result
    """
    engine = get_validation_engine()
    results = engine.validate(data, schema_name)
    return ValidationResult(results)

def validate_batch(data_items: List[Dict[str, Any]], schema_name: str) -> List[ValidationResult]:
    """
    Validate a batch of data items against a schema.
    
    Args:
        data_items: List of data items to validate
        schema_name: The name of the schema to validate against
        
    Returns:
        List of ValidationResult objects, one for each data item
    """
    engine = get_validation_engine()
    results = engine.validate_batch(data_items, schema_name)
    return [ValidationResult(result) for result in results]

def register_schema(schema: ValidationSchema):
    """
    Register a validation schema with the engine.
    
    Args:
        schema: The validation schema to register
    """
    engine = get_validation_engine()
    engine.register_schema(schema)
    
def add_schema(schema: ValidationSchema):
    """
    Add a validation schema to the engine.
    
    This is an alias for register_schema to maintain API compatibility.
    
    Args:
        schema: The validation schema to add
    """
    register_schema(schema)