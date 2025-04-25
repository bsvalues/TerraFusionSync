"""
API endpoints for sync operations in the TerraFusion SyncService platform.

This module provides API routes for creating, monitoring, and managing
sync operations between different systems.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

from apps.backend.models import db, SyncOperation, SyncPair

logger = logging.getLogger(__name__)

# Create a blueprint for sync operations
sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')


@sync_bp.route('/operations', methods=['GET'])
def get_operations():
    """
    Get a list of sync operations with optional filtering.
    
    Query parameters:
        - status: Filter by operation status
        - sync_pair_id: Filter by sync pair ID
        - offset: Pagination offset (default: 0)
        - limit: Pagination limit (default: 20)
    """
    try:
        # Parse query parameters
        status = request.args.get('status')
        sync_pair_id = request.args.get('sync_pair_id')
        offset = int(request.args.get('offset', 0))
        limit = min(int(request.args.get('limit', 20)), 100)  # Prevent excessive queries
        
        # Build query
        query = SyncOperation.query
        
        # Apply filters
        if status:
            query = query.filter(SyncOperation.status == status)
        if sync_pair_id:
            query = query.filter(SyncOperation.sync_pair_id == sync_pair_id)
        
        # Count total matching records
        total_count = query.count()
        
        # Apply pagination and get results
        operations = query.order_by(SyncOperation.created_at.desc()) \
                         .offset(offset) \
                         .limit(limit) \
                         .all()
        
        # Convert to dict representations
        result = {
            'operations': [op.to_dict() for op in operations],
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total_count
            }
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting operations: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/operations/<int:operation_id>', methods=['GET'])
def get_operation(operation_id):
    """
    Get a specific sync operation by ID.
    
    Args:
        operation_id: ID of the operation to retrieve
    """
    try:
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({'error': 'Operation not found'}), 404
        
        return jsonify(operation.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting operation {operation_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/operations', methods=['POST'])
def create_operation():
    """
    Create a new sync operation.
    
    Request body:
        - sync_pair_id: ID of the sync pair to use
        - operation_type: Type of operation (default: full_sync)
        - configuration: Custom configuration for this operation
        - scheduled_at: ISO-8601 timestamp to schedule the operation
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'sync_pair_id' not in data:
            return jsonify({'error': 'sync_pair_id is required'}), 400
        
        # Check if the sync pair exists
        sync_pair = SyncPair.query.get(data['sync_pair_id'])
        if not sync_pair:
            return jsonify({'error': f"Sync pair {data['sync_pair_id']} not found"}), 404
        
        # Parse the scheduled time if provided
        scheduled_at = None
        if 'scheduled_at' in data and data['scheduled_at']:
            try:
                scheduled_at = datetime.fromisoformat(data['scheduled_at'].replace('Z', '+00:00'))
            except ValueError:
                return jsonify({'error': 'Invalid scheduled_at format. Use ISO-8601.'}), 400
        
        # Create the operation
        operation = SyncOperation(
            sync_pair_id=data['sync_pair_id'],
            operation_type=data.get('operation_type', 'full_sync'),
            status='pending',
            configuration=data.get('configuration'),
            scheduled_at=scheduled_at,
            correlation_id=data.get('correlation_id', str(uuid.uuid4()))
        )
        
        db.session.add(operation)
        db.session.commit()
        
        logger.info(f"Created sync operation {operation.id} for pair {operation.sync_pair_id}")
        
        # Return the created operation
        return jsonify(operation.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating operation: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error creating operation: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/operations/<int:operation_id>/cancel', methods=['POST'])
def cancel_operation(operation_id):
    """
    Cancel a pending or scheduled sync operation.
    
    Args:
        operation_id: ID of the operation to cancel
    """
    try:
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({'error': 'Operation not found'}), 404
        
        # Only allow cancellation of pending or scheduled operations
        if operation.status not in ['pending', 'scheduled']:
            return jsonify({'error': f"Cannot cancel operation with status '{operation.status}'"}), 400
        
        # Update the status
        operation.status = 'cancelled'
        db.session.commit()
        
        logger.info(f"Cancelled sync operation {operation.id}")
        
        return jsonify(operation.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error cancelling operation {operation_id}: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error cancelling operation {operation_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/pairs', methods=['GET'])
def get_sync_pairs():
    """
    Get a list of all sync pairs.
    
    Query parameters:
        - source_type: Filter by source system type
        - target_type: Filter by target system type
        - enabled: Filter by enabled status (true/false)
    """
    try:
        # Parse query parameters
        source_type = request.args.get('source_type')
        target_type = request.args.get('target_type')
        enabled_str = request.args.get('enabled')
        
        # Build query
        query = SyncPair.query
        
        # Apply filters
        if source_type:
            query = query.filter(SyncPair.source_system_type == source_type)
        if target_type:
            query = query.filter(SyncPair.target_system_type == target_type)
        if enabled_str is not None:
            enabled = enabled_str.lower() == 'true'
            query = query.filter(SyncPair.sync_enabled == enabled)
        
        # Get results
        sync_pairs = query.all()
        
        # Convert to dict representations
        result = {
            'sync_pairs': [sp.to_dict() for sp in sync_pairs]
        }
        
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error getting sync pairs: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/pairs/<string:pair_id>', methods=['GET'])
def get_sync_pair(pair_id):
    """
    Get a specific sync pair by ID.
    
    Args:
        pair_id: ID of the sync pair to retrieve
    """
    try:
        sync_pair = SyncPair.query.get(pair_id)
        
        if not sync_pair:
            return jsonify({'error': 'Sync pair not found'}), 404
        
        return jsonify(sync_pair.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting sync pair {pair_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/pairs', methods=['POST'])
def create_sync_pair():
    """
    Create a new sync pair.
    
    Request body:
        - id: Unique ID for the sync pair (optional, generated if not provided)
        - name: Name of the sync pair
        - source_system_type: Type of the source system
        - target_system_type: Type of the target system
        - description: Description of the sync pair (optional)
        - source_system: Configuration for the source system (optional)
        - target_system: Configuration for the target system (optional)
        - mappings: Field mappings between source and target (optional)
        - sync_interval_minutes: Interval for automatic syncs (optional)
        - sync_schedule: Cron-style schedule for syncs (optional)
        - sync_enabled: Whether syncs are enabled (optional, default: true)
        - change_detection_method: Method to detect changes (optional)
        - incremental_key: Key for incremental syncs (optional)
        - conflict_resolution: Strategy for resolving conflicts (optional)
        - validation_rules: Rules for validating data (optional)
        - data_encryption: Whether to encrypt data (optional)
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'source_system_type', 'target_system_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"{field} is required"}), 400
        
        # Generate ID if not provided
        pair_id = data.get('id', str(uuid.uuid4()))
        
        # Check if ID already exists
        existing_pair = SyncPair.query.get(pair_id)
        if existing_pair:
            return jsonify({'error': f"Sync pair with ID {pair_id} already exists"}), 409
        
        # Create the sync pair
        sync_pair = SyncPair(
            id=pair_id,
            name=data['name'],
            source_system_type=data['source_system_type'],
            target_system_type=data['target_system_type'],
            description=data.get('description'),
            source_system=data.get('source_system'),
            target_system=data.get('target_system'),
            mappings=data.get('mappings'),
            sync_interval_minutes=data.get('sync_interval_minutes'),
            sync_schedule=data.get('sync_schedule'),
            sync_enabled=data.get('sync_enabled', True),
            change_detection_method=data.get('change_detection_method', 'full_scan'),
            incremental_key=data.get('incremental_key'),
            conflict_resolution=data.get('conflict_resolution', 'source_wins'),
            validation_rules=data.get('validation_rules'),
            data_encryption=data.get('data_encryption', False)
        )
        
        db.session.add(sync_pair)
        db.session.commit()
        
        logger.info(f"Created sync pair {sync_pair.id}: {sync_pair.name}")
        
        # Return the created sync pair
        return jsonify(sync_pair.to_dict()), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error creating sync pair: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error creating sync pair: {str(e)}")
        return jsonify({'error': str(e)}), 500


@sync_bp.route('/pairs/<string:pair_id>', methods=['PUT'])
def update_sync_pair(pair_id):
    """
    Update an existing sync pair.
    
    Args:
        pair_id: ID of the sync pair to update
    """
    try:
        sync_pair = SyncPair.query.get(pair_id)
        
        if not sync_pair:
            return jsonify({'error': 'Sync pair not found'}), 404
        
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Update fields
        updatable_fields = [
            'name', 'description', 'source_system', 'target_system',
            'mappings', 'sync_interval_minutes', 'sync_schedule',
            'sync_enabled', 'change_detection_method', 'incremental_key',
            'conflict_resolution', 'validation_rules', 'data_encryption'
        ]
        
        for field in updatable_fields:
            if field in data:
                setattr(sync_pair, field, data[field])
        
        # Update the updated_at and updated_by fields
        sync_pair.updated_at = datetime.utcnow()
        # TODO: Add authentication to get the current user
        # sync_pair.updated_by = current_user.id
        
        db.session.commit()
        
        logger.info(f"Updated sync pair {sync_pair.id}")
        
        return jsonify(sync_pair.to_dict()), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating sync pair {pair_id}: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        logger.error(f"Error updating sync pair {pair_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500