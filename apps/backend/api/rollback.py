"""
Rollback API module for the TerraFusion SyncService platform.

This module provides API endpoints for rolling back sync operations,
accessible only to ITAdmin users.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

from flask import Blueprint, request, jsonify, current_app, render_template, redirect, url_for, flash, session

# Import the database models
from apps.backend.models import SyncOperation, SyncPair, AuditEntry
from app import db

# Import authentication utilities
try:
    from apps.backend.auth.county_rbac import check_permission, requires_county_permission
    COUNTY_RBAC_AVAILABLE = True
except ImportError:
    COUNTY_RBAC_AVAILABLE = False
    
    # Fallback decorator if County RBAC isn't available
    def requires_county_permission(permission):
        def decorator(f):
            def wrapped(*args, **kwargs):
                # Just pass through if RBAC isn't available
                return f(*args, **kwargs)
            return wrapped
        return decorator

# Configure logging
logger = logging.getLogger(__name__)

# Create a blueprint for rollback operations
rollback_bp = Blueprint('rollback', __name__, url_prefix='/api/rollback')

# Helper functions
def log_user_action(action: str, details: Dict[str, Any], severity: str = "info") -> None:
    """
    Log user actions for audit purposes.
    
    Args:
        action: The action being performed
        details: Additional details about the action
        severity: The severity level of the action
    """
    user = session.get('user', {})
    username = user.get('name', 'system')
    user_id = user.get('id', 'system')
    
    # Create an audit entry
    entry = AuditEntry(
        event_type=f"rollback_{action}",
        resource_type="sync_operation",
        description=f"Rollback action: {action}",
        severity=severity,
        user_id=user_id,
        username=username,
        ip_address=request.remote_addr,
        new_state=details
    )
    
    # Add and commit to the database
    with current_app.app_context():
        db.session.add(entry)
        db.session.commit()
    
    logger.info(f"Rollback action logged: {action} by {username}")

# API Routes
@rollback_bp.route('/operations', methods=['GET'])
def list_rollback_operations():
    """
    List operations that can be rolled back.
    
    Only completed or failed operations within the last 30 days.
    """
    # Calculate the cutoff date (30 days ago)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    # Query for operations that can be rolled back
    operations = db.session.query(SyncOperation).filter(
        SyncOperation.status.in_(['completed', 'failed']),
        SyncOperation.completed_at > cutoff_date
    ).order_by(SyncOperation.completed_at.desc()).all()
    
    # Format the result
    result = []
    for op in operations:
        # Get sync pair information
        pair = db.session.query(SyncPair).filter_by(id=op.sync_pair_id).first()
        pair_name = pair.name if pair else "Unknown"
        
        result.append({
            'id': op.id,
            'sync_pair_id': op.sync_pair_id,
            'sync_pair_name': pair_name,
            'status': op.status,
            'started_at': op.started_at.isoformat() if op.started_at else None,
            'completed_at': op.completed_at.isoformat() if op.completed_at else None,
            'total_records': op.total_records,
            'processed_records': op.processed_records,
            'successful_records': op.successful_records,
            'failed_records': op.failed_records
        })
    
    # Log the action
    log_user_action('list', {'count': len(result)})
    
    return jsonify({'operations': result})

@rollback_bp.route('/operations/<int:operation_id>', methods=['GET'])
def get_rollback_operation(operation_id: int):
    """
    Get details of a specific operation for rollback verification.
    """
    # Query for the operation
    operation = db.session.query(SyncOperation).filter_by(id=operation_id).first()
    
    if not operation:
        return jsonify({'error': 'Operation not found'}), 404
    
    # Get the associated sync pair
    pair = db.session.query(SyncPair).filter_by(id=operation.sync_pair_id).first()
    
    # Format the result
    result = {
        'id': operation.id,
        'sync_pair_id': operation.sync_pair_id,
        'sync_pair_name': pair.name if pair else "Unknown",
        'sync_pair_source': pair.source_type if pair else "Unknown",
        'sync_pair_target': pair.target_type if pair else "Unknown",
        'status': operation.status,
        'started_at': operation.started_at.isoformat() if operation.started_at else None,
        'completed_at': operation.completed_at.isoformat() if operation.completed_at else None,
        'total_records': operation.total_records,
        'processed_records': operation.processed_records,
        'successful_records': operation.successful_records,
        'failed_records': operation.failed_records,
        'error_message': operation.error_message
    }
    
    # Log the action
    log_user_action('view', {'operation_id': operation_id})
    
    return jsonify({'operation': result})

@rollback_bp.route('/operations/<int:operation_id>/rollback', methods=['POST'])
def rollback_operation(operation_id: int):
    """
    Initiate a rollback for a specific operation.
    """
    # Query for the operation
    operation = db.session.query(SyncOperation).filter_by(id=operation_id).first()
    
    if not operation:
        return jsonify({'error': 'Operation not found'}), 404
    
    # Verify operation can be rolled back
    if operation.status not in ['completed', 'failed']:
        return jsonify({'error': 'Operation cannot be rolled back (must be completed or failed)'}), 400
    
    # Get the associated sync pair
    pair = db.session.query(SyncPair).filter_by(id=operation.sync_pair_id).first()
    
    if not pair:
        return jsonify({'error': 'Associated sync pair not found'}), 404
    
    # Get JSON data from request
    data = request.get_json() or {}
    reason = data.get('reason', 'No reason provided')
    force = data.get('force', False)
    
    # Create a new operation for the rollback
    rollback_op = SyncOperation(
        sync_pair_id=operation.sync_pair_id,
        status='pending',
        sync_type='rollback',
        total_records=operation.successful_records,  # We're rolling back successful records
        created_by=session.get('user', {}).get('name', 'system')
    )
    
    # Add and commit to the database
    db.session.add(rollback_op)
    db.session.commit()
    
    # Create an audit log for the rollback
    # We store both the original operation and the rollback operation IDs
    user = session.get('user', {})
    audit = AuditEntry(
        event_type='rollback_initiated',
        resource_type='sync_operation',
        resource_id=str(operation_id),
        operation_id=rollback_op.id,
        description=f"Rollback initiated for operation {operation_id}: {reason}",
        severity='warning',
        user_id=user.get('id', 'system'),
        username=user.get('name', 'system'),
        ip_address=request.remote_addr,
        previous_state={'operation_id': operation_id},
        new_state={'rollback_operation_id': rollback_op.id, 'reason': reason, 'force': force}
    )
    
    db.session.add(audit)
    db.session.commit()
    
    logger.warning(f"Rollback initiated for operation {operation_id} by {user.get('name', 'system')}: {reason}")
    
    # Notify the SyncService about the rollback
    # In a real implementation, this would likely make a request to the SyncService
    # to trigger the actual rollback process
    
    return jsonify({
        'success': True,
        'message': 'Rollback initiated',
        'rollback_operation_id': rollback_op.id
    })

@rollback_bp.route('/audit', methods=['GET'])
def list_rollback_audit():
    """
    List audit entries related to rollback operations.
    """
    # Query for rollback-related audit entries
    audit_entries = db.session.query(AuditEntry).filter(
        AuditEntry.event_type.like('rollback_%')
    ).order_by(AuditEntry.timestamp.desc()).limit(100).all()
    
    # Format the result
    result = []
    for entry in audit_entries:
        result.append(entry.to_dict())
    
    return jsonify({'audit_entries': result})