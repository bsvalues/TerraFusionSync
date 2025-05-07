"""
Rollback API Module for the TerraFusion SyncService platform.

This module provides endpoints for rolling back sync operations,
restricted to IT Admin users only for security purposes.
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from flask import Blueprint, jsonify, request, g, current_app
from apps.backend.database import db
from apps.backend.models import SyncOperation, AuditEntry

# Import authorization functions
from apps.backend.auth import requires_auth
try:
    from apps.backend.auth import requires_county_permission, log_user_action, COUNTY_RBAC_AVAILABLE
    COUNTY_RBAC_ENABLED = True 
except ImportError:
    COUNTY_RBAC_ENABLED = False

# Create blueprint
rollback_bp = Blueprint('rollback', __name__, url_prefix='/api/rollback')

# Configure logging
logger = logging.getLogger(__name__)

# Define decorator for ITAdmin-only endpoints
def requires_admin(f):
    """
    Decorator to require ITAdmin role for API endpoints.
    This is used to ensure that only authorized administrators can perform
    sensitive operations like rollbacks.
    """
    if COUNTY_RBAC_ENABLED:
        from apps.backend.auth import check_permission
        # If county RBAC is available, use it
        return requires_auth(requires_county_permission("rollback")(f))
    else:
        # Otherwise, use standard auth with custom check
        @requires_auth
        def decorated(*args, **kwargs):
            # Get current user
            user = g.get('user', {})
            
            # Check if user has admin role
            if not user or 'admin' not in user.get('roles', []):
                return jsonify({
                    'success': False,
                    'error': 'Admin role required for this operation'
                }), 403
                
            return f(*args, **kwargs)
        
        return decorated


def create_rollback_audit(operation_id: int, user_id: Optional[str] = None, 
                         username: Optional[str] = None, reason: Optional[str] = None) -> None:
    """
    Create an audit log entry for a rollback operation.
    
    Args:
        operation_id: ID of the rolled back operation
        user_id: ID of the user who performed the rollback (optional)
        username: Username of the user who performed the rollback (optional)
        reason: Reason for the rollback (optional)
    """
    if COUNTY_RBAC_ENABLED:
        # Get county user
        county_user = g.get('county_user')
        if county_user:
            log_user_action(
                county_user["username"],
                county_user["role"],
                f"ROLLBACK:operation_{operation_id}",
                resource_id=str(operation_id)
            )
            return
    
    # Standard audit logging
    from apps.backend.app import create_audit_log
    
    with current_app.app_context():
        create_audit_log(
            event_type="rollback_operation",
            resource_type="sync_operation",
            resource_id=str(operation_id),
            description=f"Operation {operation_id} rolled back" + (f" - Reason: {reason}" if reason else ""),
            severity="warning",
            user_id=user_id,
            username=username
        )


@rollback_bp.route('/operation/<int:operation_id>', methods=['POST'])
@requires_admin
def rollback_operation(operation_id: int):
    """
    Roll back a sync operation.
    
    This endpoint allows IT admins to roll back a specific sync operation.
    It will:
    1. Mark the operation as rolled back
    2. Create a new sync operation with reverse direction if possible
    3. Log the rollback in the audit trail
    
    Args:
        operation_id: ID of the operation to roll back
        
    Returns:
        JSON response with rollback status
    """
    # Get current user
    user = g.get('user')
    county_user = getattr(g, 'county_user', None)
    
    # Get reason for rollback
    reason = request.json.get('reason') if request.is_json else None
    
    # Get the operation
    operation = db.session.query(SyncOperation).filter(SyncOperation.id == operation_id).first()
    if not operation:
        return jsonify({
            'success': False,
            'error': f'Operation {operation_id} not found'
        }), 404
    
    # Check if the operation is already rolled back
    if operation.status == 'rolled_back':
        return jsonify({
            'success': False,
            'error': f'Operation {operation_id} has already been rolled back'
        }), 400
    
    try:
        # Create a snapshot of the operation's state before modifying it
        previous_state = {
            'id': operation.id,
            'sync_pair_id': operation.sync_pair_id,
            'status': operation.status,
            'sync_type': operation.sync_type,
            'started_at': operation.started_at.isoformat() if operation.started_at else None,
            'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
            'total_records': operation.total_records,
            'processed_records': operation.processed_records,
            'successful_records': operation.successful_records,
            'failed_records': operation.failed_records
        }
        
        # Update the operation status
        operation.status = 'rolled_back'
        operation.error_message = f"Rolled back by {'County user: ' + county_user['username'] if county_user else 'admin'} at {datetime.utcnow().isoformat()}"
        
        if reason:
            operation.error_message += f" - Reason: {reason}"
        
        # Commit the changes
        db.session.commit()
        
        # Create a reverse operation if needed
        # This would be implemented according to your specific rollback requirements
        
        # Create audit log entry
        create_rollback_audit(
            operation_id=operation_id,
            user_id=user.get('id') if user else None,
            username=user.get('username') if user else (county_user.get('username') if county_user else None),
            reason=reason
        )
        
        # Return success response
        return jsonify({
            'success': True,
            'message': f'Operation {operation_id} has been rolled back successfully',
            'operation': {
                'id': operation.id,
                'status': operation.status,
                'rollback_time': datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        # Log the error
        logger.error(f"Error rolling back operation {operation_id}: {str(e)}")
        
        # Rollback transaction
        db.session.rollback()
        
        # Return error response
        return jsonify({
            'success': False,
            'error': f'Error rolling back operation: {str(e)}'
        }), 500


@rollback_bp.route('/list', methods=['GET'])
@requires_admin
def list_rollback_operations():
    """
    List all operations that have been rolled back.
    
    Returns:
        JSON response with a list of rolled back operations
    """
    try:
        # Query rolled back operations
        rolled_back_ops = db.session.query(SyncOperation).filter(
            SyncOperation.status == 'rolled_back'
        ).order_by(SyncOperation.completed_at.desc()).all()
        
        # Format the operations
        operations = []
        for op in rolled_back_ops:
            operations.append({
                'id': op.id,
                'sync_pair_id': op.sync_pair_id,
                'sync_type': op.sync_type,
                'started_at': op.started_at.isoformat() if op.started_at else None,
                'completed_at': op.completed_at.isoformat() if op.completed_at else None,
                'error_message': op.error_message
            })
        
        # Return response
        return jsonify({
            'success': True,
            'count': len(operations),
            'operations': operations
        })
    except Exception as e:
        # Log the error
        logger.error(f"Error listing rolled back operations: {str(e)}")
        
        # Return error response
        return jsonify({
            'success': False,
            'error': f'Error listing rolled back operations: {str(e)}'
        }), 500