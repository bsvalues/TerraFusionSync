"""
TerraFusion SyncService API module for sync operations.

This module provides the API endpoints for managing sync operations.
"""

import json
from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from ..database import db
from ..models import SyncPair, SyncOperation, AuditEntry

# Create a Blueprint for sync operations API
sync_bp = Blueprint('sync_operations', __name__, url_prefix='/api/sync')

@sync_bp.route('/pairs', methods=['GET', 'POST'])
def get_sync_pairs():
    """
    Get all sync pairs or create a new one.
    
    GET: Returns a list of all sync pairs.
    POST: Creates a new sync pair.
    """
    if request.method == 'GET':
        # Get all sync pairs
        sync_pairs = SyncPair.query.all()
        return jsonify({
            'sync_pairs': [sync_pair.to_dict() for sync_pair in sync_pairs]
        })
    
    # POST: Create a new sync pair
    data = request.json
    
    # Validate required fields
    required_fields = ['name', 'source_system', 'target_system']
    for field in required_fields:
        if field not in data:
            return jsonify({
                'error': f'Missing required field: {field}'
            }), 400
    
    # Create a new sync pair
    sync_pair = SyncPair.create_from_dict(data)
    
    # Save to database
    db.session.add(sync_pair)
    db.session.commit()
    
    # Create audit log
    from app import create_audit_log
    create_audit_log(
        event_type='sync_pair_created',
        resource_type='sync_pair',
        description=f'Sync pair {sync_pair.name} created',
        resource_id=str(sync_pair.id),
        new_state=sync_pair.to_dict()
    )
    
    return jsonify({
        'sync_pair': sync_pair.to_dict()
    }), 201

@sync_bp.route('/pairs/<int:pair_id>', methods=['GET', 'PUT', 'DELETE'])
def get_sync_pair(pair_id):
    """
    Get, update, or delete a specific sync pair.
    
    GET: Returns a specific sync pair.
    PUT: Updates a specific sync pair.
    DELETE: Deletes a specific sync pair.
    """
    # Get the sync pair
    sync_pair = SyncPair.query.get(pair_id)
    if not sync_pair:
        return jsonify({
            'error': f'Sync pair not found: {pair_id}'
        }), 404
    
    if request.method == 'GET':
        # Return the sync pair
        return jsonify({
            'sync_pair': sync_pair.to_dict()
        })
    
    elif request.method == 'PUT':
        # Update the sync pair
        data = request.json
        previous_state = sync_pair.to_dict()
        
        # Update basic fields
        if 'name' in data:
            sync_pair.name = data['name']
        if 'description' in data:
            sync_pair.description = data['description']
        if 'sync_frequency' in data:
            sync_pair.sync_frequency = data['sync_frequency']
        if 'is_active' in data:
            sync_pair.is_active = data['is_active']
        
        # Update source system
        if 'source_system' in data:
            source = data['source_system']
            if 'type' in source:
                sync_pair.source_system_type = source['type']
            if 'name' in source:
                sync_pair.source_system_name = source['name']
            
            # Extract config from source system
            source_config = {k: v for k, v in source.items() 
                            if k not in ("type", "name")}
            if source_config:
                sync_pair.source_system_config = source_config
        
        # Update target system
        if 'target_system' in data:
            target = data['target_system']
            if 'type' in target:
                sync_pair.target_system_type = target['type']
            if 'name' in target:
                sync_pair.target_system_name = target['name']
            
            # Extract config from target system
            target_config = {k: v for k, v in target.items() 
                            if k not in ("type", "name")}
            if target_config:
                sync_pair.target_system_config = target_config
        
        # Update field mappings
        if 'field_mappings' in data:
            sync_pair.field_mappings = data['field_mappings']
        
        # Save to database
        db.session.commit()
        
        # Create audit log
        from app import create_audit_log
        create_audit_log(
            event_type='sync_pair_updated',
            resource_type='sync_pair',
            description=f'Sync pair {sync_pair.name} updated',
            resource_id=str(sync_pair.id),
            previous_state=previous_state,
            new_state=sync_pair.to_dict()
        )
        
        return jsonify({
            'sync_pair': sync_pair.to_dict()
        })
    
    elif request.method == 'DELETE':
        # Delete the sync pair
        previous_state = sync_pair.to_dict()
        name = sync_pair.name
        
        # Check if there are any operations for this sync pair
        operations = SyncOperation.query.filter_by(sync_pair_id=pair_id).all()
        if operations:
            return jsonify({
                'error': f'Cannot delete sync pair {pair_id} because it has associated operations'
            }), 400
        
        # Delete the sync pair
        db.session.delete(sync_pair)
        db.session.commit()
        
        # Create audit log
        from app import create_audit_log
        create_audit_log(
            event_type='sync_pair_deleted',
            resource_type='sync_pair',
            description=f'Sync pair {name} deleted',
            resource_id=str(pair_id),
            previous_state=previous_state
        )
        
        return jsonify({
            'message': f'Sync pair {pair_id} deleted'
        })

@sync_bp.route('/operations', methods=['GET', 'POST'])
def get_sync_operations():
    """
    Get all sync operations or create a new one.
    
    GET: Returns a list of all sync operations with filtering options.
    POST: Creates a new sync operation.
    """
    if request.method == 'GET':
        # Parse query parameters for filtering
        filters = {}
        
        # Filter by sync pair ID
        if 'sync_pair_id' in request.args:
            filters['sync_pair_id'] = int(request.args['sync_pair_id'])
        
        # Filter by operation type
        if 'operation_type' in request.args:
            filters['operation_type'] = request.args['operation_type']
        
        # Filter by status
        if 'status' in request.args:
            filters['status'] = request.args['status']
        
        # Apply filters
        query = SyncOperation.query
        for key, value in filters.items():
            query = query.filter(getattr(SyncOperation, key) == value)
        
        # Order by ID (most recent first)
        query = query.order_by(SyncOperation.id.desc())
        
        # Apply limit if specified
        if 'limit' in request.args:
            query = query.limit(int(request.args['limit']))
        
        # Execute query
        operations = query.all()
        
        return jsonify({
            'sync_operations': [op.to_dict() for op in operations]
        })
    
    # POST: Create a new sync operation
    data = request.json
    
    # Validate required fields
    if 'sync_pair_id' not in data:
        return jsonify({
            'error': 'Missing required field: sync_pair_id'
        }), 400
    
    if 'operation_type' not in data:
        return jsonify({
            'error': 'Missing required field: operation_type'
        }), 400
    
    # Get the sync pair
    sync_pair = SyncPair.query.get(data['sync_pair_id'])
    if not sync_pair:
        return jsonify({
            'error': f'Sync pair not found: {data["sync_pair_id"]}'
        }), 404
    
    # Create the operation
    operation = SyncOperation.create_from_sync_pair(
        sync_pair=sync_pair,
        operation_type=data['operation_type'],
        triggered_by=data.get('triggered_by', 'api')
    )
    
    # Save to database
    db.session.add(operation)
    db.session.commit()
    
    # Create audit log
    from app import create_audit_log
    create_audit_log(
        event_type='sync_operation_created',
        resource_type='sync_operation',
        description=f'Sync operation {operation.id} created for sync pair {sync_pair.name}',
        resource_id=str(operation.id),
        operation_id=operation.id,
        new_state=operation.to_dict()
    )
    
    # TODO: Trigger the sync operation in the background
    # This would be implemented in a separate module or using a task queue
    
    return jsonify({
        'sync_operation': operation.to_dict()
    }), 201

@sync_bp.route('/operations/<int:operation_id>', methods=['GET', 'PUT'])
def get_sync_operation(operation_id):
    """
    Get or update a specific sync operation.
    
    GET: Returns a specific sync operation.
    PUT: Updates a specific sync operation's status.
    """
    # Get the operation
    operation = SyncOperation.query.get(operation_id)
    if not operation:
        return jsonify({
            'error': f'Sync operation not found: {operation_id}'
        }), 404
    
    if request.method == 'GET':
        # Return the operation
        return jsonify({
            'sync_operation': operation.to_dict()
        })
    
    elif request.method == 'PUT':
        # Update the operation status
        data = request.json
        previous_state = operation.to_dict()
        
        # Check if we're updating status
        if 'status' in data:
            new_status = data['status']
            old_status = operation.status
            
            if new_status == 'running' and old_status == 'pending':
                # Mark as started
                operation.start()
                
                # Create audit log
                from app import create_audit_log
                create_audit_log(
                    event_type='sync_operation_started',
                    resource_type='sync_operation',
                    description=f'Sync operation {operation.id} started',
                    resource_id=str(operation.id),
                    operation_id=operation.id,
                    previous_state=previous_state,
                    new_state=operation.to_dict()
                )
            
            elif new_status == 'completed' and old_status == 'running':
                # Mark as completed
                operation.complete(
                    processed=data.get('processed_records', 0),
                    successful=data.get('successful_records', 0),
                    failed=data.get('failed_records', 0),
                    metrics=data.get('metrics')
                )
                
                # Create audit log
                from app import create_audit_log
                create_audit_log(
                    event_type='sync_operation_completed',
                    resource_type='sync_operation',
                    description=f'Sync operation {operation.id} completed successfully',
                    resource_id=str(operation.id),
                    operation_id=operation.id,
                    previous_state=previous_state,
                    new_state=operation.to_dict()
                )
            
            elif new_status == 'failed' and old_status in ('running', 'pending'):
                # Mark as failed
                operation.fail(
                    error_message=data.get('error_message', 'Unknown error'),
                    processed=data.get('processed_records', 0),
                    successful=data.get('successful_records', 0),
                    failed=data.get('failed_records', 0)
                )
                
                # Create audit log
                from app import create_audit_log
                create_audit_log(
                    event_type='sync_operation_failed',
                    resource_type='sync_operation',
                    description=f'Sync operation {operation.id} failed: {data.get("error_message", "Unknown error")}',
                    resource_id=str(operation.id),
                    operation_id=operation.id,
                    severity='error',
                    previous_state=previous_state,
                    new_state=operation.to_dict()
                )
            
            else:
                return jsonify({
                    'error': f'Invalid status transition: {old_status} -> {new_status}'
                }), 400
        
        # Check if we're adding a log event
        if 'log_event' in data:
            event = data['log_event']
            if 'type' not in event or 'message' not in event:
                return jsonify({
                    'error': 'Log event must include type and message'
                }), 400
            
            # Add the log event
            operation.log_event(
                event_type=event['type'],
                message=event['message'],
                details=event.get('details')
            )
        
        # Save to database
        db.session.commit()
        
        return jsonify({
            'sync_operation': operation.to_dict()
        })

@sync_bp.route('/operations/<int:operation_id>/logs', methods=['GET'])
def get_operation_logs(operation_id):
    """
    Get logs for a specific sync operation.
    """
    # Get the operation
    operation = SyncOperation.query.get(operation_id)
    if not operation:
        return jsonify({
            'error': f'Sync operation not found: {operation_id}'
        }), 404
    
    # Return the logs
    return jsonify({
        'logs': operation.execution_log or []
    })