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


@validation_bp.route('/schemas', methods=['GET'])
def get_schemas():
    """
    Get available validation schemas.
    
    Returns:
        List of available validation schemas.
    """
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