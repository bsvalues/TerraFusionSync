"""
API blueprint for sync operations.

This module provides API endpoints for managing sync operations,
including creating, updating, and monitoring sync jobs.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.exc import SQLAlchemyError

# Import models
from apps.backend.models import SyncOperation, SyncPair, AuditEntry, db

# Import authentication
from apps.backend.auth import requires_auth

logger = logging.getLogger(__name__)

# Create blueprint
sync_bp = Blueprint('sync_operations', __name__, url_prefix='/api/sync')


# Helper functions
def create_audit_entry(
    event_type: str,
    resource_type: str,
    description: str,
    resource_id: Optional[str] = None,
    operation_id: Optional[int] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    severity: str = 'info',
    user=None,
    correlation_id: Optional[str] = None
):
    """Create an audit log entry for sync operations."""
    try:
        # Get the current authenticated user if available
        user_id = None
        username = None
        if user:
            user_id = user.get('id')
            username = user.get('username')
        
        # Create the audit entry
        audit_entry = AuditEntry(
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            operation_id=operation_id,
            description=description,
            previous_state=previous_state,
            new_state=new_state,
            severity=severity,
            user_id=user_id,
            username=username,
            correlation_id=correlation_id,
            timestamp=datetime.utcnow()
        )
        
        # Save to database
        db.session.add(audit_entry)
        db.session.commit()
        
        return audit_entry
    except Exception as e:
        logger.error(f"Failed to create audit entry: {str(e)}")
        db.session.rollback()
        return None


# API Routes

@sync_bp.route('/pairs', methods=['GET'])
@requires_auth
def get_sync_pairs():
    """
    Get all configured sync pairs.
    
    Returns a list of all configured sync pairs with their configuration.
    
    Returns:
        JSON response with sync pairs data
    """
    try:
        # Get query parameters
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        
        # Query sync pairs
        query = SyncPair.query
        if active_only:
            query = query.filter_by(active=True)
            
        sync_pairs = query.all()
        
        # Convert to dictionary format
        result = [pair.to_dict() for pair in sync_pairs]
        
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sync pairs: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch sync pairs',
            'message': str(e)
        }), 500


@sync_bp.route('/pairs/<pair_id>', methods=['GET', 'PUT'])
@requires_auth
def get_sync_pair(pair_id):
    """
    Get or update a specific sync pair by ID.
    
    Args:
        pair_id: ID of the sync pair
        
    Returns:
        JSON response with sync pair data
    """
    try:
        # Get the sync pair
        sync_pair = SyncPair.query.get(pair_id)
        
        if not sync_pair:
            return jsonify({
                'success': False,
                'error': 'Sync pair not found',
                'message': f'No sync pair found with ID {pair_id}'
            }), 404
        
        # Handle GET request
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'data': sync_pair.to_dict()
            }), 200
        
        # Handle PUT request (update)
        if request.method == 'PUT':
            data = request.json
            
            # Get current state for audit log
            previous_state = sync_pair.to_dict()
            
            # Update fields
            if 'name' in data:
                sync_pair.name = data['name']
            if 'source_system' in data:
                sync_pair.source_system = data['source_system']
            if 'target_system' in data:
                sync_pair.target_system = data['target_system']
            if 'entities' in data:
                sync_pair.entities = data['entities']
            if 'mappings' in data:
                sync_pair.mappings = data['mappings']
            if 'active' in data:
                sync_pair.active = data['active']
            
            # Save changes
            db.session.commit()
            
            # Create audit log
            user = current_app.get_current_user()
            create_audit_entry(
                event_type='sync_pair_updated',
                resource_type='sync_pair',
                resource_id=pair_id,
                description=f'Sync pair {sync_pair.name} was updated',
                previous_state=previous_state,
                new_state=sync_pair.to_dict(),
                user=user
            )
            
            return jsonify({
                'success': True,
                'data': sync_pair.to_dict(),
                'message': 'Sync pair updated successfully'
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing sync pair {pair_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to process sync pair',
            'message': str(e)
        }), 500


@sync_bp.route('/pairs', methods=['POST'])
@requires_auth
def create_sync_pair():
    """
    Create a new sync pair.
    
    Returns:
        JSON response with created sync pair data
    """
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['id', 'name', 'source_system', 'target_system']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required field',
                    'message': f'Field {field} is required'
                }), 400
        
        # Check if a sync pair with the ID already exists
        existing_pair = SyncPair.query.get(data['id'])
        if existing_pair:
            return jsonify({
                'success': False,
                'error': 'Duplicate ID',
                'message': f'A sync pair with ID {data["id"]} already exists'
            }), 409
        
        # Create new sync pair
        sync_pair = SyncPair(
            id=data['id'],
            name=data['name']
        )
        
        # Set additional properties
        sync_pair.source_system = data['source_system']
        sync_pair.target_system = data['target_system']
        sync_pair.entities = data.get('entities', [])
        sync_pair.mappings = data.get('mappings', [])
        sync_pair.active = data.get('active', True)
        
        # Save to database
        db.session.add(sync_pair)
        db.session.commit()
        
        # Create audit log
        user = current_app.get_current_user()
        create_audit_entry(
            event_type='sync_pair_created',
            resource_type='sync_pair',
            resource_id=sync_pair.id,
            description=f'Sync pair {sync_pair.name} was created',
            new_state=sync_pair.to_dict(),
            user=user
        )
        
        return jsonify({
            'success': True,
            'data': sync_pair.to_dict(),
            'message': 'Sync pair created successfully'
        }), 201
        
    except SQLAlchemyError as e:
        logger.error(f"Database error creating sync pair: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Database error',
            'message': str(e)
        }), 500
        
    except Exception as e:
        logger.error(f"Error creating sync pair: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to create sync pair',
            'message': str(e)
        }), 500


@sync_bp.route('/pairs/<pair_id>', methods=['DELETE'])
@requires_auth
def delete_sync_pair(pair_id):
    """
    Delete a sync pair by ID.
    
    Args:
        pair_id: ID of the sync pair to delete
        
    Returns:
        JSON response with result of the operation
    """
    try:
        # Get the sync pair
        sync_pair = SyncPair.query.get(pair_id)
        
        if not sync_pair:
            return jsonify({
                'success': False,
                'error': 'Sync pair not found',
                'message': f'No sync pair found with ID {pair_id}'
            }), 404
        
        # Check if there are active operations using this pair
        active_operations = SyncOperation.query.filter_by(
            sync_pair_id=pair_id
        ).filter(
            SyncOperation.status.in_(['pending', 'scheduled', 'running'])
        ).count()
        
        if active_operations > 0:
            return jsonify({
                'success': False,
                'error': 'Active operations exist',
                'message': f'Cannot delete sync pair with {active_operations} active operations'
            }), 409
        
        # Store state for audit log
        previous_state = sync_pair.to_dict()
        
        # Delete the sync pair
        db.session.delete(sync_pair)
        db.session.commit()
        
        # Create audit log
        user = current_app.get_current_user()
        create_audit_entry(
            event_type='sync_pair_deleted',
            resource_type='sync_pair',
            resource_id=pair_id,
            description=f'Sync pair {sync_pair.name} was deleted',
            previous_state=previous_state,
            user=user
        )
        
        return jsonify({
            'success': True,
            'message': 'Sync pair deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting sync pair {pair_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to delete sync pair',
            'message': str(e)
        }), 500


@sync_bp.route('/operations', methods=['GET', 'POST'])
@requires_auth
def get_sync_operations():
    """
    Get all sync operations, with optional filtering or start a new operation.
    
    For GET requests, returns a list of sync operations with their status.
    For POST requests, creates a new sync operation.
    
    Returns:
        JSON response with sync operations data
    """
    # Handle GET request
    if request.method == 'GET':
        try:
            # Get query parameters
            sync_pair_id = request.args.get('sync_pair_id')
            status = request.args.get('status')
            operation_type = request.args.get('operation_type')
            limit = request.args.get('limit', 100, type=int)
            offset = request.args.get('offset', 0, type=int)
            
            # Build query
            query = SyncOperation.query
            
            if sync_pair_id:
                query = query.filter_by(sync_pair_id=sync_pair_id)
            if status:
                query = query.filter_by(status=status)
            if operation_type:
                query = query.filter_by(operation_type=operation_type)
                
            # Order by creation time, newest first
            query = query.order_by(SyncOperation.created_at.desc())
            
            # Apply pagination
            query = query.limit(limit).offset(offset)
            
            # Execute query
            operations = query.all()
            
            # Get total count
            total_count = SyncOperation.query.count()
            
            # Convert to dictionary format
            result = [op.to_dict() for op in operations]
            
            return jsonify({
                'success': True,
                'data': result,
                'count': len(result),
                'total': total_count,
                'limit': limit,
                'offset': offset
            }), 200
            
        except Exception as e:
            logger.error(f"Error fetching sync operations: {str(e)}")
            return jsonify({
                'success': False,
                'error': 'Failed to fetch sync operations',
                'message': str(e)
            }), 500
    
    # Handle POST request (create new operation)
    elif request.method == 'POST':
        try:
            data = request.json
            
            # Validate required fields
            required_fields = ['sync_pair_id', 'operation_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'success': False,
                        'error': 'Missing required field',
                        'message': f'Field {field} is required'
                    }), 400
            
            # Check if the sync pair exists
            sync_pair = SyncPair.query.get(data['sync_pair_id'])
            if not sync_pair:
                return jsonify({
                    'success': False,
                    'error': 'Sync pair not found',
                    'message': f'No sync pair found with ID {data["sync_pair_id"]}'
                }), 404
            
            # Check if the sync pair is active
            if not sync_pair.active:
                return jsonify({
                    'success': False,
                    'error': 'Sync pair inactive',
                    'message': f'Sync pair {data["sync_pair_id"]} is not active'
                }), 409
            
            # Create new operation
            operation = SyncOperation(
                sync_pair_id=data['sync_pair_id']
            )
            
            # Set additional properties
            operation.operation_type = data['operation_type']
            operation.status = data.get('status', 'pending')
            operation.priority = data.get('priority', 0)
            operation.created_at = datetime.utcnow()
            
            # Get scheduled time if provided
            if 'scheduled_at' in data:
                scheduled_at = datetime.fromisoformat(data['scheduled_at'])
                operation.scheduled_at = scheduled_at
            
            # Get user information
            user = current_app.get_current_user()
            if user:
                operation.user_id = user.get('id')
                operation.username = user.get('username')
            
            # Save to database
            db.session.add(operation)
            db.session.commit()
            
            # Create audit log
            create_audit_entry(
                event_type='sync_operation_created',
                resource_type='sync_operation',
                resource_id=str(operation.id),
                operation_id=operation.id,
                description=f'{operation.operation_type} sync operation created for pair {operation.sync_pair_id}',
                new_state=operation.to_dict(),
                user=user
            )
            
            return jsonify({
                'success': True,
                'data': operation.to_dict(),
                'message': 'Sync operation created successfully'
            }), 201
            
        except Exception as e:
            logger.error(f"Error creating sync operation: {str(e)}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': 'Failed to create sync operation',
                'message': str(e)
            }), 500


@sync_bp.route('/operations/<operation_id>', methods=['GET', 'PUT'])
@requires_auth
def get_sync_operation(operation_id):
    """
    Get or update a sync operation by ID.
    
    Args:
        operation_id: ID of the sync operation
        
    Returns:
        JSON response with sync operation data
    """
    try:
        # Get the sync operation
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({
                'success': False,
                'error': 'Sync operation not found',
                'message': f'No sync operation found with ID {operation_id}'
            }), 404
        
        # Handle GET request
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'data': operation.to_dict()
            }), 200
        
        # Handle PUT request (update)
        if request.method == 'PUT':
            data = request.json
            
            # Get current state for audit log
            previous_state = operation.to_dict()
            
            # Update fields
            if 'status' in data:
                operation.status = data['status']
            if 'priority' in data:
                operation.priority = data['priority']
            if 'scheduled_at' in data:
                operation.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
            
            # Save changes
            db.session.commit()
            
            # Create audit log
            user = current_app.get_current_user()
            create_audit_entry(
                event_type='sync_operation_updated',
                resource_type='sync_operation',
                resource_id=str(operation.id),
                operation_id=operation.id,
                description=f'Sync operation {operation.id} was updated',
                previous_state=previous_state,
                new_state=operation.to_dict(),
                user=user
            )
            
            return jsonify({
                'success': True,
                'data': operation.to_dict(),
                'message': 'Sync operation updated successfully'
            }), 200
            
    except Exception as e:
        logger.error(f"Error processing sync operation {operation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to process sync operation',
            'message': str(e)
        }), 500


@sync_bp.route('/operations/<operation_id>/cancel', methods=['POST'])
@requires_auth
def cancel_sync_operation(operation_id):
    """
    Cancel a pending or running sync operation.
    
    Args:
        operation_id: ID of the sync operation to cancel
        
    Returns:
        JSON response with result of the operation
    """
    try:
        # Get the sync operation
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({
                'success': False,
                'error': 'Sync operation not found',
                'message': f'No sync operation found with ID {operation_id}'
            }), 404
        
        # Check if the operation can be cancelled
        if operation.status not in ['pending', 'scheduled', 'running']:
            return jsonify({
                'success': False,
                'error': 'Cannot cancel operation',
                'message': f'Operation with status {operation.status} cannot be cancelled'
            }), 409
        
        # Get current state for audit log
        previous_state = operation.to_dict()
        
        # Update status
        operation.status = 'cancelled'
        operation.completed_at = datetime.utcnow()
        
        # Save changes
        db.session.commit()
        
        # Create audit log
        user = current_app.get_current_user()
        create_audit_entry(
            event_type='sync_operation_cancelled',
            resource_type='sync_operation',
            resource_id=str(operation.id),
            operation_id=operation.id,
            description=f'Sync operation {operation.id} was cancelled',
            previous_state=previous_state,
            new_state=operation.to_dict(),
            user=user
        )
        
        return jsonify({
            'success': True,
            'data': operation.to_dict(),
            'message': 'Sync operation cancelled successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error cancelling sync operation {operation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to cancel sync operation',
            'message': str(e)
        }), 500


@sync_bp.route('/operations/<operation_id>/retry', methods=['POST'])
@requires_auth
def retry_sync_operation(operation_id):
    """
    Retry a failed sync operation.
    
    Args:
        operation_id: ID of the sync operation to retry
        
    Returns:
        JSON response with new operation data
    """
    try:
        # Get the original sync operation
        original_operation = SyncOperation.query.get(operation_id)
        
        if not original_operation:
            return jsonify({
                'success': False,
                'error': 'Sync operation not found',
                'message': f'No sync operation found with ID {operation_id}'
            }), 404
        
        # Check if the operation can be retried
        if original_operation.status != 'failed':
            return jsonify({
                'success': False,
                'error': 'Cannot retry operation',
                'message': f'Only failed operations can be retried, current status: {original_operation.status}'
            }), 409
        
        # Create new operation based on the original
        new_operation = SyncOperation(
            sync_pair_id=original_operation.sync_pair_id
        )
        
        # Copy properties
        new_operation.operation_type = original_operation.operation_type
        new_operation.status = 'pending'
        new_operation.priority = original_operation.priority
        new_operation.created_at = datetime.utcnow()
        
        # Track retry information
        retry_count = 1
        if original_operation.retry_count:
            try:
                retry_count = int(original_operation.retry_count) + 1
            except (ValueError, TypeError):
                retry_count = 1
        new_operation.retry_count = str(retry_count)
        
        # Get user information
        user = current_app.get_current_user()
        if user:
            new_operation.user_id = user.get('id')
            new_operation.username = user.get('username')
        
        # Save to database
        db.session.add(new_operation)
        db.session.commit()
        
        # Create audit log
        create_audit_entry(
            event_type='sync_operation_retried',
            resource_type='sync_operation',
            resource_id=str(new_operation.id),
            operation_id=new_operation.id,
            description=f'Retry of failed operation {original_operation.id}',
            new_state=new_operation.to_dict(),
            user=user
        )
        
        return jsonify({
            'success': True,
            'data': new_operation.to_dict(),
            'original_operation_id': original_operation.id,
            'message': 'Sync operation retry created successfully'
        }), 201
        
    except Exception as e:
        logger.error(f"Error retrying sync operation {operation_id}: {str(e)}")
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': 'Failed to retry sync operation',
            'message': str(e)
        }), 500


@sync_bp.route('/stats', methods=['GET'])
@requires_auth
def get_sync_stats():
    """
    Get statistics about sync operations.
    
    Returns:
        JSON response with statistics data
    """
    try:
        # Calculate basic statistics
        total_operations = SyncOperation.query.count()
        completed_operations = SyncOperation.query.filter_by(status='completed').count()
        failed_operations = SyncOperation.query.filter_by(status='failed').count()
        success_rate = 0
        if total_operations > 0:
            success_rate = (completed_operations / total_operations) * 100
        
        # Get counts by operation type
        operation_types = {}
        for op_type in ['full', 'incremental', 'delta', 'validation', 'repair']:
            count = SyncOperation.query.filter_by(operation_type=op_type).count()
            operation_types[op_type] = count
        
        # Get counts by status
        status_counts = {}
        for status in ['pending', 'scheduled', 'running', 'completed', 'failed', 'cancelled']:
            count = SyncOperation.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Calculate statistics by sync pair
        sync_pair_stats = []
        sync_pairs = SyncPair.query.all()
        for pair in sync_pairs:
            pair_operations = SyncOperation.query.filter_by(sync_pair_id=pair.id).count()
            pair_completed = SyncOperation.query.filter_by(sync_pair_id=pair.id, status='completed').count()
            pair_failed = SyncOperation.query.filter_by(sync_pair_id=pair.id, status='failed').count()
            pair_success_rate = 0
            if pair_operations > 0:
                pair_success_rate = (pair_completed / pair_operations) * 100
            
            sync_pair_stats.append({
                'sync_pair_id': pair.id,
                'name': pair.name,
                'total_operations': pair_operations,
                'completed_operations': pair_completed,
                'failed_operations': pair_failed,
                'success_rate': pair_success_rate
            })
        
        return jsonify({
            'success': True,
            'data': {
                'total_operations': total_operations,
                'completed_operations': completed_operations,
                'failed_operations': failed_operations,
                'success_rate': success_rate,
                'by_operation_type': operation_types,
                'by_status': status_counts,
                'by_sync_pair': sync_pair_stats
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating sync statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate sync statistics',
            'message': str(e)
        }), 500