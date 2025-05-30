"""
Validation API for the TerraFusion SyncService.

This module provides API endpoints for validating data against schemas.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from flask import Blueprint, jsonify, request
except ImportError:
    # For type checking or when Flask is not available
    Blueprint = object
    def jsonify(*args, **kwargs): return None
    request = None

from apps.backend.validation import (
    validate, validate_batch, get_validation_engine,
    create_validation_schema, ValidationLevel
)

# Create the blueprint
validation_bp = Blueprint('validation', __name__, url_prefix='/api/validation')
logger = logging.getLogger(__name__)


@validation_bp.route('/schemas', methods=['GET', 'POST'])
def get_or_create_schemas():
    """
    Get available validation schemas or create a new schema.
    
    GET: Returns list of available validation schemas.
    POST: Creates a new validation schema.
    
    Request body for POST:
    {
        "name": "schema_name",
        "description": "Schema description",
        "validation_level": "strict",
        "rules": [
            {
                "field_name": "field1",
                "rule_type": "RequiredFieldRule",
                "description": "Field1 is required",
                "severity": "error"
            },
            ...
        ]
    }
    
    Returns:
        GET: List of available validation schemas.
        POST: Created schema information.
    """
    if request.method == 'GET':
        engine = get_validation_engine()
        schemas = engine.schemas
        
        schema_info = []
        for name, schema in schemas.items():
            schema_info.append({
                "name": name,
                "description": schema.description,
                "validation_level": schema.validation_level,
                "rule_count": len(schema.rules)
            })
        
        return jsonify({
            "schemas": schema_info,
            "timestamp": datetime.utcnow().isoformat()
        })
    elif request.method == 'POST':
        # Create a new schema
        data = request.json
        
        if not data:
            return jsonify({
                "error": "Missing data",
                "message": "Request body must contain schema definition"
            }), 400
        
        # Validate required fields
        required_fields = ['name', 'description', 'rules']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                "error": "Missing fields",
                "message": f"Required fields missing: {', '.join(missing_fields)}"
            }), 400
        
        # Check if schema already exists
        engine = get_validation_engine()
        if data['name'] in engine.schemas:
            return jsonify({
                "error": "Schema already exists",
                "message": f"Validation schema '{data['name']}' already exists"
            }), 409
        
        # Create validation rules
        rules = []
        for rule_data in data['rules']:
            # Validate rule data
            if 'field_name' not in rule_data:
                return jsonify({
                    "error": "Invalid rule",
                    "message": "Each rule must have a field_name"
                }), 400
                
            if 'rule_type' not in rule_data:
                return jsonify({
                    "error": "Invalid rule",
                    "message": "Each rule must have a rule_type"
                }), 400
                
            try:
                # Create the rule based on its type
                if rule_data['rule_type'] == 'RequiredFieldRule':
                    from apps.backend.validation import RequiredFieldRule
                    rule = RequiredFieldRule(
                        field_name=rule_data['field_name'],
                        description=rule_data.get('description', f"{rule_data['field_name']} is required"),
                        severity=rule_data.get('severity', 'error')
                    )
                elif rule_data['rule_type'] == 'TypeRule':
                    from apps.backend.validation import TypeRule
                    
                    # Convert string type names to actual types
                    type_mapping = {
                        'str': str,
                        'int': int,
                        'float': float,
                        'bool': bool,
                        'dict': dict,
                        'list': list
                    }
                    
                    expected_type = rule_data.get('expected_type', 'str')
                    if expected_type in type_mapping:
                        expected_type = type_mapping[expected_type]
                    else:
                        expected_type = str
                    
                    rule = TypeRule(
                        field_name=rule_data['field_name'],
                        expected_type=expected_type,
                        description=rule_data.get('description', f"{rule_data['field_name']} must be a {expected_type.__name__}"),
                        severity=rule_data.get('severity', 'error')
                    )
                elif rule_data['rule_type'] == 'RangeRule':
                    from apps.backend.validation import RangeRule
                    rule = RangeRule(
                        field_name=rule_data['field_name'],
                        min_value=rule_data.get('min_value'),
                        max_value=rule_data.get('max_value'),
                        description=rule_data.get('description', f"{rule_data['field_name']} must be within range"),
                        severity=rule_data.get('severity', 'error')
                    )
                elif rule_data['rule_type'] == 'PatternRule':
                    from apps.backend.validation import PatternRule
                    rule = PatternRule(
                        field_name=rule_data['field_name'],
                        pattern=rule_data.get('pattern', '.*'),
                        description=rule_data.get('description', f"{rule_data['field_name']} must match pattern"),
                        severity=rule_data.get('severity', 'error')
                    )
                elif rule_data['rule_type'] == 'EnumRule':
                    from apps.backend.validation import EnumRule
                    rule = EnumRule(
                        field_name=rule_data['field_name'],
                        allowed_values=rule_data.get('allowed_values', []),
                        description=rule_data.get('description', f"{rule_data['field_name']} must be one of allowed values"),
                        severity=rule_data.get('severity', 'error')
                    )
                elif rule_data['rule_type'] == 'DateFormatRule':
                    from apps.backend.validation import DateFormatRule
                    rule = DateFormatRule(
                        field_name=rule_data['field_name'],
                        date_format=rule_data.get('date_format', '%Y-%m-%d'),
                        description=rule_data.get('description', f"{rule_data['field_name']} must be a valid date"),
                        severity=rule_data.get('severity', 'error')
                    )
                else:
                    return jsonify({
                        "error": "Invalid rule type",
                        "message": f"Rule type '{rule_data['rule_type']}' is not supported"
                    }), 400
                
                rules.append(rule)
            except Exception as e:
                return jsonify({
                    "error": "Rule creation error",
                    "message": f"Error creating rule: {str(e)}"
                }), 400
                
        # Set validation level
        validation_level = data.get('validation_level', 'strict')
        if validation_level not in ['strict', 'moderate', 'relaxed']:
            validation_level = 'strict'
            
        # Create the schema
        try:
            schema = create_validation_schema(
                schema_name=data['name'],
                description=data['description'],
                rules=rules,
                validation_level=ValidationLevel(validation_level)
            )
            
            # Add the schema to the engine
            engine.add_schema(schema)
            
            return jsonify({
                "message": "Schema created successfully",
                "schema": {
                    "name": schema.schema_name,
                    "description": schema.description,
                    "validation_level": schema.validation_level,
                    "rule_count": len(schema.rules)
                },
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            return jsonify({
                "error": "Schema creation error",
                "message": f"Error creating schema: {str(e)}"
            }), 500


@validation_bp.route('/schemas/<schema_name>', methods=['GET'])
def get_schema(schema_name):
    """
    Get details of a specific validation schema.
    
    Args:
        schema_name: Name of the schema to get
    
    Returns:
        Details of the requested schema
    """
    engine = get_validation_engine()
    
    if schema_name not in engine.schemas:
        return jsonify({
            "error": "Schema not found",
            "message": f"Validation schema '{schema_name}' not found"
        }), 404
    
    schema = engine.schemas[schema_name]
    rules = []
    
    for rule in schema.rules:
        rule_info = {
            "field_name": rule.field_name,
            "description": rule.description,
            "severity": rule.severity,
            "rule_type": rule.__class__.__name__
        }
        
        # Add additional properties based on rule type
        if hasattr(rule, 'expected_type'):
            if isinstance(rule.expected_type, list):
                rule_info["expected_types"] = [t.__name__ for t in rule.expected_type]
            else:
                rule_info["expected_type"] = rule.expected_type.__name__
        
        if hasattr(rule, 'min_value'):
            rule_info["min_value"] = rule.min_value
        
        if hasattr(rule, 'max_value'):
            rule_info["max_value"] = rule.max_value
        
        if hasattr(rule, 'pattern'):
            rule_info["pattern"] = rule.pattern
        
        if hasattr(rule, 'allowed_values'):
            rule_info["allowed_values"] = rule.allowed_values
        
        if hasattr(rule, 'date_format'):
            rule_info["date_format"] = rule.date_format
        
        rules.append(rule_info)
    
    return jsonify({
        "name": schema.schema_name,
        "description": schema.description,
        "validation_level": schema.validation_level,
        "rules": rules,
        "timestamp": datetime.utcnow().isoformat()
    })


@validation_bp.route('/validate/<schema_name>', methods=['POST'])
def validate_data(schema_name):
    """
    Validate data against a schema.
    
    Args:
        schema_name: Name of the schema to validate against
    
    Request body:
        JSON data to validate
    
    Returns:
        Validation results
    """
    engine = get_validation_engine()
    
    if schema_name not in engine.schemas:
        return jsonify({
            "error": "Schema not found",
            "message": f"Validation schema '{schema_name}' not found"
        }), 404
    
    # Get data from request
    data = request.json
    if not data:
        return jsonify({
            "error": "Missing data",
            "message": "Request body must contain data to validate"
        }), 400
    
    # Validate data
    try:
        result = validate(data, schema_name)
        
        # Return validation results
        return jsonify({
            "valid": result.valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "info": result.info,
            "schema_name": result.schema_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error validating data: {str(e)}")
        return jsonify({
            "error": "Validation error",
            "message": f"Error validating data: {str(e)}"
        }), 500


@validation_bp.route('/validate-batch/<schema_name>', methods=['POST'])
def validate_data_batch(schema_name):
    """
    Validate a batch of data items against a schema.
    
    Args:
        schema_name: Name of the schema to validate against
    
    Request body:
        List of JSON data items to validate
    
    Returns:
        List of validation results
    """
    engine = get_validation_engine()
    
    if schema_name not in engine.schemas:
        return jsonify({
            "error": "Schema not found",
            "message": f"Validation schema '{schema_name}' not found"
        }), 404
    
    # Get data from request
    data_items = request.json
    if not data_items or not isinstance(data_items, list):
        return jsonify({
            "error": "Invalid data",
            "message": "Request body must contain a list of data items to validate"
        }), 400
    
    # Validate data
    try:
        results = validate_batch(data_items, schema_name)
        
        # Return validation results
        return jsonify({
            "results": [result.to_dict() for result in results],
            "valid_count": sum(1 for result in results if result.valid),
            "invalid_count": sum(1 for result in results if not result.valid),
            "total_count": len(results),
            "schema_name": schema_name,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error validating data batch: {str(e)}")
        return jsonify({
            "error": "Validation error",
            "message": f"Error validating data batch: {str(e)}"
        }), 500


@validation_bp.route('/history', methods=['GET'])
def get_validation_history():
    """
    Get validation history.
    
    Returns:
        List of validation history entries
    """
    engine = get_validation_engine()
    history = engine.get_validation_history()
    
    return jsonify({
        "history": history,
        "count": len(history),
        "timestamp": datetime.utcnow().isoformat()
    })


@validation_bp.route('/history/clear', methods=['POST'])
def clear_validation_history():
    """
    Clear validation history.
    
    Returns:
        Success message
    """
    engine = get_validation_engine()
    engine.clear_validation_history()
    
    return jsonify({
        "message": "Validation history cleared",
        "timestamp": datetime.utcnow().isoformat()
    })