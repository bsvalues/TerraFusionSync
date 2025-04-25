"""
Data Validation Schema for TerraFusion SyncService.

This module defines the validation schemas for data synchronization between
PACS and CAMA systems. It uses Pydantic for schema validation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union, Any, Callable
import json

# Instead of using Pydantic which is causing issues, let's create our own simple model class
class BaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self):
        result = {}
        for key, value in self.__dict__.items():
            if not key.startswith('_'):
                if hasattr(value, 'to_dict'):
                    result[key] = value.to_dict()
                elif isinstance(value, list):
                    result[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
                else:
                    result[key] = value
        return result
    
    def to_json(self):
        return json.dumps(self.to_dict())


class ValidationLevel(str, Enum):
    """Validation level for schema validation."""
    STRICT = "strict"       # Fail on any validation error
    LENIENT = "lenient"     # Allow some non-critical validation errors
    LOG_ONLY = "log_only"   # Only log validation errors, don't fail


class ValidationRule(BaseModel):
    """Base class for validation rules."""
    field_name: str
    description: str
    severity: str = "error"  # error, warning, info
    
    def validate(self, value: Any) -> Dict[str, Any]:
        """
        Validate the value against the rule.
        
        Args:
            value: The value to validate
            
        Returns:
            Dict with validation result:
                {
                    "valid": bool,
                    "message": str,
                    "severity": str,
                    "field_name": str,
                    "value": Any
                }
        """
        raise NotImplementedError("Subclasses must implement validate()")


class RequiredFieldRule(ValidationRule):
    """Rule to check if a required field is present and not None."""
    
    def validate(self, value: Any) -> Dict[str, Any]:
        valid = value is not None
        message = f"Required field '{self.field_name}' is missing" if not valid else ""
        
        return {
            "valid": valid,
            "message": message,
            "severity": self.severity,
            "field_name": self.field_name,
            "value": value
        }


class TypeRule(ValidationRule):
    """Rule to check if a field is of the expected type."""
    expected_type: Union[type, List[type]]
    
    def validate(self, value: Any) -> Dict[str, Any]:
        # If value is None and we have multiple types, it's automatically valid
        if value is None:
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Convert single type to list for uniform handling
        expected_types = self.expected_type if isinstance(self.expected_type, list) else [self.expected_type]
        
        valid = any(isinstance(value, t) for t in expected_types)
        type_names = ", ".join(t.__name__ for t in expected_types)
        message = f"Field '{self.field_name}' expected type {type_names}, got {type(value).__name__}" if not valid else ""
        
        return {
            "valid": valid,
            "message": message,
            "severity": self.severity,
            "field_name": self.field_name,
            "value": value
        }


class RangeRule(ValidationRule):
    """Rule to check if a numeric field is within a specified range."""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    
    def validate(self, value: Any) -> Dict[str, Any]:
        # Skip validation if value is None
        if value is None:
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Check if the value is numeric
        if not isinstance(value, (int, float)):
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' must be a number for range validation",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Validate against min_value if specified
        if self.min_value is not None and value < self.min_value:
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' value {value} is less than minimum {self.min_value}",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Validate against max_value if specified
        if self.max_value is not None and value > self.max_value:
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' value {value} is greater than maximum {self.max_value}",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        return {
            "valid": True,
            "message": "",
            "severity": self.severity,
            "field_name": self.field_name,
            "value": value
        }


class PatternRule(ValidationRule):
    """Rule to check if a string field matches a specified regex pattern."""
    pattern: str
    
    def validate(self, value: Any) -> Dict[str, Any]:
        # Skip validation if value is None
        if value is None:
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Check if the value is a string
        if not isinstance(value, str):
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' must be a string for pattern validation",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        import re
        valid = bool(re.match(self.pattern, value))
        message = f"Field '{self.field_name}' value '{value}' does not match pattern '{self.pattern}'" if not valid else ""
        
        return {
            "valid": valid,
            "message": message,
            "severity": self.severity,
            "field_name": self.field_name,
            "value": value
        }


class EnumRule(ValidationRule):
    """Rule to check if a field value is one of a specified set of values."""
    allowed_values: List[Any]
    
    def validate(self, value: Any) -> Dict[str, Any]:
        # Skip validation if value is None
        if value is None:
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        valid = value in self.allowed_values
        message = f"Field '{self.field_name}' value '{value}' is not one of allowed values: {self.allowed_values}" if not valid else ""
        
        return {
            "valid": valid,
            "message": message,
            "severity": self.severity,
            "field_name": self.field_name,
            "value": value
        }


class DateFormatRule(ValidationRule):
    """Rule to check if a string field is a valid date in the specified format."""
    date_format: str
    
    def validate(self, value: Any) -> Dict[str, Any]:
        # Skip validation if value is None
        if value is None:
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        # Check if the value is a string
        if not isinstance(value, str):
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' must be a string for date format validation",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        
        try:
            datetime.strptime(value, self.date_format)
            return {
                "valid": True,
                "message": "",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }
        except ValueError:
            return {
                "valid": False,
                "message": f"Field '{self.field_name}' value '{value}' is not a valid date in format '{self.date_format}'",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }


class CustomRule(ValidationRule):
    """Rule that uses a custom validation function."""
    class Config:
        arbitrary_types_allowed = True
    
    validation_func: Any  # Using Any instead of callable to avoid Pydantic schema generation issues
    
    def validate(self, value: Any) -> Dict[str, Any]:
        try:
            result = self.validation_func(value)
            
            # If the function returns a dict with validation details, use it
            if isinstance(result, dict) and "valid" in result:
                result["field_name"] = self.field_name
                result["severity"] = result.get("severity", self.severity)
                return result
            
            # If the function returns a boolean, use it with default message
            if isinstance(result, bool):
                valid = result
                message = "" if valid else f"Field '{self.field_name}' failed custom validation"
                return {
                    "valid": valid,
                    "message": message,
                    "severity": self.severity,
                    "field_name": self.field_name,
                    "value": value
                }
            
            # If we get here, the function returned something unexpected
            return {
                "valid": False,
                "message": f"Invalid return value from custom validation function for field '{self.field_name}'",
                "severity": "error",
                "field_name": self.field_name,
                "value": value
            }
        except Exception as e:
            # If the function raises an exception, it's a validation error
            return {
                "valid": False,
                "message": f"Custom validation for field '{self.field_name}' failed: {str(e)}",
                "severity": self.severity,
                "field_name": self.field_name,
                "value": value
            }


class ValidationSchema(BaseModel):
    """Base class for validation schemas."""
    schema_name: str
    description: str
    validation_level: ValidationLevel = ValidationLevel.STRICT
    rules: List[ValidationRule]
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the data against the schema.
        
        Args:
            data: The data to validate
            
        Returns:
            Dict with validation results:
                {
                    "valid": bool,
                    "errors": List[Dict],
                    "warnings": List[Dict],
                    "info": List[Dict]
                }
        """
        errors = []
        warnings = []
        info = []
        
        for rule in self.rules:
            field_value = data.get(rule.field_name)
            result = rule.validate(field_value)
            
            if not result["valid"]:
                if result["severity"] == "error":
                    errors.append(result)
                elif result["severity"] == "warning":
                    warnings.append(result)
                else:
                    info.append(result)
        
        # Determine overall validity based on validation level
        valid = True
        if self.validation_level == ValidationLevel.STRICT:
            valid = len(errors) == 0
        elif self.validation_level == ValidationLevel.LENIENT:
            # In lenient mode, only critical errors make the validation fail
            critical_errors = [e for e in errors if e.get("critical", False)]
            valid = len(critical_errors) == 0
        elif self.validation_level == ValidationLevel.LOG_ONLY:
            # In log-only mode, validation always succeeds
            valid = True
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "info": info
        }


# Predefined validation schemas for PACS data
class PACSImageSchema(ValidationSchema):
    """Validation schema for PACS image data."""
    schema_name: str = "pacs_image"
    description: str = "Validation schema for PACS image data"
    
    rules: List[ValidationRule] = [
        RequiredFieldRule(
            field_name="image_id",
            description="Unique identifier for the image",
            severity="error"
        ),
        RequiredFieldRule(
            field_name="study_id",
            description="ID of the study the image belongs to",
            severity="error"
        ),
        RequiredFieldRule(
            field_name="patient_id",
            description="ID of the patient",
            severity="error"
        ),
        TypeRule(
            field_name="image_type",
            description="Type of the image",
            expected_type=str,
            severity="error"
        ),
        EnumRule(
            field_name="modality",
            description="Imaging modality",
            allowed_values=["CT", "MR", "US", "XR", "CR", "MG", "RF", "PET", "NM", "DX", "PR", "ES", "SR"],
            severity="error"
        ),
        DateFormatRule(
            field_name="acquisition_date",
            description="Date when the image was acquired",
            date_format="%Y-%m-%d",
            severity="error"
        ),
        PatternRule(
            field_name="accession_number",
            description="Accession number of the study",
            pattern=r"^[A-Z0-9]{6,20}$",
            severity="warning"
        )
    ]


# Predefined validation schemas for CAMA data
class CAMAPropertySchema(ValidationSchema):
    """Validation schema for CAMA property data."""
    schema_name: str = "cama_property"
    description: str = "Validation schema for CAMA property data"
    
    rules: List[ValidationRule] = [
        RequiredFieldRule(
            field_name="property_id",
            description="Unique identifier for the property",
            severity="error"
        ),
        RequiredFieldRule(
            field_name="parcel_id",
            description="ID of the parcel",
            severity="error"
        ),
        TypeRule(
            field_name="property_type",
            description="Type of the property",
            expected_type=str,
            severity="error"
        ),
        EnumRule(
            field_name="property_class",
            description="Property classification",
            allowed_values=["RESIDENTIAL", "COMMERCIAL", "INDUSTRIAL", "AGRICULTURAL", "SPECIAL"],
            severity="error"
        ),
        RangeRule(
            field_name="assessed_value",
            description="Assessed value of the property",
            min_value=0,
            severity="error"
        ),
        DateFormatRule(
            field_name="assessment_date",
            description="Date of the assessment",
            date_format="%Y-%m-%d",
            severity="error"
        ),
        PatternRule(
            field_name="tax_district",
            description="Tax district code",
            pattern=r"^[A-Z]{2}\d{2}$",
            severity="warning"
        )
    ]


# Factory function to create validation schemas
def create_validation_schema(schema_type: str, **kwargs) -> ValidationSchema:
    """
    Create a validation schema based on the schema type.
    
    Args:
        schema_type: Type of the schema to create
        **kwargs: Additional parameters for the schema
    
    Returns:
        ValidationSchema: The created validation schema
    
    Raises:
        ValueError: If the schema type is unknown
    """
    schema_map = {
        "pacs_image": PACSImageSchema,
        "cama_property": CAMAPropertySchema
    }
    
    if schema_type not in schema_map:
        raise ValueError(f"Unknown schema type: {schema_type}")
    
    schema_class = schema_map[schema_type]
    
    # Override default rules if provided
    if "rules" in kwargs:
        return schema_class(rules=kwargs.pop("rules"), **kwargs)
    
    # Otherwise, use the default rules
    return schema_class(**kwargs)