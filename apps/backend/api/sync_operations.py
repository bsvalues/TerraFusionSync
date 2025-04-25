"""
Sync Operations API module.

This module provides API endpoints for managing sync operations with self-healing
capabilities. It acts as a bridge between the API Gateway and the SyncService,
forwarding requests while adding monitoring and recovery functionality.
"""

import logging
import requests
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from sqlalchemy.exc import SQLAlchemyError

# Import local modules when available
try:
    from ..models import SyncOperation, SyncPair, AuditEntry, db
    from ..auth import requires_auth, get_current_user
except ImportError:
    from models import SyncOperation, SyncPair, AuditEntry, db
    from app import requires_auth, get_current_user


logger = logging.getLogger(__name__)

# Create Blueprint
sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

# Settings
SYNCSERVICE_BASE_URL = "http://0.0.0.0:8080"


def create_audit_log(
    event_type: str,
    resource_type: str,
    description: str,
    severity: str = "info",
    resource_id: Optional[str] = None,
    operation_id: Optional[int] = None,
    previous_state: Optional[Dict[str, Any]] = None,
    new_state: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    username: Optional[str] = None
) -> AuditEntry:
    """
    Create and save an audit log entry.
    
    Args:
        event_type: Type of event (e.g., 'sync_started', 'sync_completed')
        resource_type: Type of resource (e.g., 'sync_pair', 'operation')
        description: Human-readable description of the event
        severity: Event severity ('info', 'warning', 'error', 'critical')
        resource_id: ID of the resource (if applicable)
        operation_id: ID of the sync operation (if applicable)
        previous_state: JSON representation of previous state for tracking changes
        new_state: JSON representation of new state for tracking changes
        user_id: ID of the user who performed the action (if available)
        username: Username of the user who performed the action (if available)
    
    Returns:
        The created AuditEntry instance
    """
    entry = AuditEntry(
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id else None,
        operation_id=operation_id,
        description=description,
        timestamp=datetime.utcnow(),
        severity=severity,
        previous_state=previous_state if previous_state else {},
        new_state=new_state if new_state else {},
        user_id=user_id or 'system',
        username=username or 'system'
    )
    
    db.session.add(entry)
    db.session.commit()
    return entry


@sync_bp.route('/operations', methods=['GET'])
@requires_auth
def get_operations():
    """
    Get all sync operations with optional filtering.
    
    Query parameters:
        - pair_id: Filter by sync pair ID
        - status: Filter by operation status
        - limit: Maximum number of operations to return (default: 100)
        - offset: Number of operations to skip (default: 0)
    """
    # Get query parameters
    pair_id = request.args.get('pair_id')
    status = request.args.get('status')
    limit = min(int(request.args.get('limit', 100)), 1000)
    offset = int(request.args.get('offset', 0))
    
    try:
        # First query the local database for operations
        query = SyncOperation.query.order_by(SyncOperation.started_at.desc())
        
        if pair_id:
            query = query.filter(SyncOperation.sync_pair_id == pair_id)
        
        if status:
            query = query.filter(SyncOperation.status == status)
        
        # Get operations with pagination
        operations = query.offset(offset).limit(limit).all()
        
        # Then get the latest operations from SyncService to ensure we have up-to-date data
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if pair_id:
                params['pair_id'] = pair_id
            
            if status:
                params['status'] = status
                
            # Query the SyncService for the latest operations
            response = requests.get(
                f"{SYNCSERVICE_BASE_URL}/sync-operations", 
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                syncservice_operations = response.json()
                
                # Merge with local operations or update local database
                # This would be implemented in a production system
                pass
                
        except requests.RequestException as e:
            # Log the error, but continue with local data
            logger.warning(f"Could not fetch latest operations from SyncService: {str(e)}")
        
        # Convert to dictionaries for the API response
        result = []
        for op in operations:
            result.append({
                "id": op.id,
                "sync_pair_id": op.sync_pair_id,
                "operation_type": op.operation_type,
                "status": op.status,
                "started_at": op.started_at.isoformat() if op.started_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "records_processed": op.details.records_processed if op.details else 0,
                "records_succeeded": op.details.records_succeeded if op.details else 0,
                "records_failed": op.details.records_failed if op.details else 0,
                "duration_seconds": op.details.duration_seconds if op.details else 0,
                "retry_count": op.retry_count or 0
            })
        
        return jsonify(result)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching operations: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_operations: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500


@sync_bp.route('/operations/<int:operation_id>', methods=['GET'])
@requires_auth
def get_operation(operation_id):
    """
    Get details for a specific sync operation.
    
    Args:
        operation_id: ID of the operation to retrieve
    """
    try:
        # First check local database
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            # If not found locally, check with SyncService
            try:
                response = requests.get(
                    f"{SYNCSERVICE_BASE_URL}/sync-operations/{operation_id}",
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Return the data from SyncService
                    return jsonify(response.json())
                elif response.status_code == 404:
                    return jsonify({"error": "Operation not found"}), 404
                else:
                    logger.warning(f"SyncService returned status {response.status_code} for operation {operation_id}")
            except requests.RequestException as e:
                logger.warning(f"Could not fetch operation {operation_id} from SyncService: {str(e)}")
            
            return jsonify({"error": "Operation not found"}), 404
        
        # Convert to dictionary for the API response
        result = {
            "id": operation.id,
            "sync_pair_id": operation.sync_pair_id,
            "operation_type": operation.operation_type,
            "status": operation.status,
            "started_at": operation.started_at.isoformat() if operation.started_at else None,
            "completed_at": operation.completed_at.isoformat() if operation.completed_at else None,
            "retry_count": operation.retry_count or 0,
            "last_error": operation.last_error,
            "details": {}
        }
        
        if operation.details:
            result["details"] = {
                "records_processed": operation.details.records_processed,
                "records_succeeded": operation.details.records_succeeded,
                "records_failed": operation.details.records_failed,
                "records_skipped": operation.details.records_skipped,
                "duration_seconds": operation.details.duration_seconds,
                "entity_stats": operation.details.entity_stats,
                "error_details": operation.details.error_details
            }
        
        return jsonify(result)
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching operation {operation_id}: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in get_operation: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500


@sync_bp.route('/operations', methods=['POST'])
@requires_auth
def start_operation():
    """
    Start a new sync operation.
    
    Request body:
        - sync_pair_id: ID of the sync pair to use
        - operation_type: Type of operation ('full', 'incremental')
        - parameters: Additional parameters for the operation (optional)
    """
    user = get_current_user()
    data = request.json
    
    if not data:
        return jsonify({"error": "Missing request body"}), 400
    
    sync_pair_id = data.get('sync_pair_id')
    operation_type = data.get('operation_type')
    parameters = data.get('parameters', {})
    
    if not sync_pair_id:
        return jsonify({"error": "Missing sync_pair_id parameter"}), 400
    
    if not operation_type or operation_type not in ['full', 'incremental', 'delta']:
        return jsonify({"error": "Invalid or missing operation_type parameter"}), 400
    
    try:
        # First check if the sync pair exists
        sync_pair = SyncPair.query.get(sync_pair_id)
        
        if not sync_pair:
            return jsonify({"error": "Sync pair not found"}), 404
        
        # Create audit log for operation start
        create_audit_log(
            event_type="sync_operation_requested",
            resource_type="sync_operation",
            description=f"{operation_type.capitalize()} sync operation requested for pair {sync_pair.name}",
            severity="info",
            resource_id=str(sync_pair_id),
            user_id=str(user.id) if hasattr(user, 'id') else None,
            username=user.username if hasattr(user, 'username') else None,
            new_state={
                "sync_pair_id": sync_pair_id,
                "operation_type": operation_type,
                "parameters": parameters
            }
        )
        
        # Forward the request to SyncService with self-healing integration
        try:
            response = requests.post(
                f"{SYNCSERVICE_BASE_URL}/sync-operations",
                json={
                    "sync_pair_id": sync_pair_id,
                    "operation_type": operation_type,
                    "parameters": parameters,
                    "source_system": sync_pair.source_system,
                    "target_system": sync_pair.target_system,
                    "enable_self_healing": True,
                    "retry_strategy": {
                        "max_attempts": 3,
                        "backoff_factor": 2
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200 or response.status_code == 201:
                operation_data = response.json()
                
                # Create local record for the operation
                operation = SyncOperation(
                    id=operation_data.get('id'),
                    sync_pair_id=sync_pair_id,
                    operation_type=operation_type,
                    status="queued",
                    created_at=datetime.utcnow(),
                    source_system=sync_pair.source_system,
                    target_system=sync_pair.target_system
                )
                
                db.session.add(operation)
                db.session.commit()
                
                # Create audit log for successful start
                create_audit_log(
                    event_type="sync_operation_started",
                    resource_type="sync_operation",
                    description=f"{operation_type.capitalize()} sync operation started for pair {sync_pair.name}",
                    severity="info",
                    resource_id=str(sync_pair_id),
                    operation_id=operation.id,
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None
                )
                
                return jsonify({
                    "success": True,
                    "operation_id": operation.id,
                    "status": "queued",
                    "message": f"{operation_type.capitalize()} sync operation started for pair {sync_pair.name}"
                })
            else:
                # Log the error
                error_data = response.json() if response.text else {"error": "Unknown error"}
                
                create_audit_log(
                    event_type="sync_operation_failed",
                    resource_type="sync_operation",
                    description=f"Failed to start {operation_type} sync operation for pair {sync_pair.name}",
                    severity="error",
                    resource_id=str(sync_pair_id),
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None,
                    new_state=error_data
                )
                
                return jsonify({
                    "success": False,
                    "error": f"SyncService returned status {response.status_code}",
                    "details": error_data
                }), response.status_code
                
        except requests.RequestException as e:
            logger.error(f"Error starting operation with SyncService: {str(e)}")
            
            create_audit_log(
                event_type="sync_operation_failed",
                resource_type="sync_operation",
                description=f"Error communicating with SyncService to start {operation_type} operation",
                severity="error",
                resource_id=str(sync_pair_id),
                user_id=str(user.id) if hasattr(user, 'id') else None,
                username=user.username if hasattr(user, 'username') else None,
                new_state={"error": str(e)}
            )
            
            return jsonify({
                "success": False,
                "error": "Could not communicate with SyncService",
                "details": str(e)
            }), 503
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while starting operation: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in start_operation: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500


@sync_bp.route('/operations/<int:operation_id>/cancel', methods=['POST'])
@requires_auth
def cancel_operation(operation_id):
    """
    Cancel a running sync operation.
    
    Args:
        operation_id: ID of the operation to cancel
    """
    user = get_current_user()
    
    try:
        # First check if the operation exists locally
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({"error": "Operation not found"}), 404
        
        if operation.status not in ['queued', 'running']:
            return jsonify({"error": "Operation cannot be cancelled (not running or queued)"}), 400
        
        # Create audit log for cancel attempt
        create_audit_log(
            event_type="sync_operation_cancel_requested",
            resource_type="sync_operation",
            description=f"Cancel requested for operation {operation_id}",
            severity="info",
            resource_id=str(operation.sync_pair_id),
            operation_id=operation.id,
            user_id=str(user.id) if hasattr(user, 'id') else None,
            username=user.username if hasattr(user, 'username') else None
        )
        
        # Forward the cancel request to SyncService
        try:
            response = requests.post(
                f"{SYNCSERVICE_BASE_URL}/sync-operations/{operation_id}/cancel",
                timeout=10
            )
            
            if response.status_code == 200:
                # Update local record
                operation.status = "cancelled"
                operation.completed_at = datetime.utcnow()
                db.session.commit()
                
                # Create audit log for successful cancel
                create_audit_log(
                    event_type="sync_operation_cancelled",
                    resource_type="sync_operation",
                    description=f"Operation {operation_id} was successfully cancelled",
                    severity="info",
                    resource_id=str(operation.sync_pair_id),
                    operation_id=operation.id,
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None
                )
                
                return jsonify({
                    "success": True,
                    "operation_id": operation.id,
                    "status": "cancelled",
                    "message": f"Operation {operation_id} was successfully cancelled"
                })
            else:
                # Log the error
                error_data = response.json() if response.text else {"error": "Unknown error"}
                
                create_audit_log(
                    event_type="sync_operation_cancel_failed",
                    resource_type="sync_operation",
                    description=f"Failed to cancel operation {operation_id}",
                    severity="warning",
                    resource_id=str(operation.sync_pair_id),
                    operation_id=operation.id,
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None,
                    new_state=error_data
                )
                
                return jsonify({
                    "success": False,
                    "error": f"SyncService returned status {response.status_code}",
                    "details": error_data
                }), response.status_code
                
        except requests.RequestException as e:
            logger.error(f"Error cancelling operation with SyncService: {str(e)}")
            
            create_audit_log(
                event_type="sync_operation_cancel_failed",
                resource_type="sync_operation",
                description=f"Error communicating with SyncService to cancel operation {operation_id}",
                severity="error",
                resource_id=str(operation.sync_pair_id),
                operation_id=operation.id,
                user_id=str(user.id) if hasattr(user, 'id') else None,
                username=user.username if hasattr(user, 'username') else None,
                new_state={"error": str(e)}
            )
            
            return jsonify({
                "success": False,
                "error": "Could not communicate with SyncService",
                "details": str(e)
            }), 503
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while cancelling operation: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in cancel_operation: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500


@sync_bp.route('/operations/<int:operation_id>/retry', methods=['POST'])
@requires_auth
def retry_operation(operation_id):
    """
    Retry a failed sync operation.
    
    Args:
        operation_id: ID of the operation to retry
    """
    user = get_current_user()
    
    try:
        # First check if the operation exists locally
        operation = SyncOperation.query.get(operation_id)
        
        if not operation:
            return jsonify({"error": "Operation not found"}), 404
        
        if operation.status != 'failed':
            return jsonify({"error": "Only failed operations can be retried"}), 400
        
        # Create audit log for retry attempt
        create_audit_log(
            event_type="sync_operation_retry_requested",
            resource_type="sync_operation",
            description=f"Retry requested for operation {operation_id}",
            severity="info",
            resource_id=str(operation.sync_pair_id),
            operation_id=operation.id,
            user_id=str(user.id) if hasattr(user, 'id') else None,
            username=user.username if hasattr(user, 'username') else None
        )
        
        # Forward the retry request to SyncService
        try:
            response = requests.post(
                f"{SYNCSERVICE_BASE_URL}/sync-operations/{operation_id}/retry",
                json={
                    "enable_self_healing": True,
                    "retry_strategy": {
                        "max_attempts": 3,
                        "backoff_factor": 2
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200:
                # Get the new operation data (which may be a new operation ID)
                operation_data = response.json()
                new_operation_id = operation_data.get('operation_id', operation_id)
                
                # Update local record or create a new one
                if new_operation_id == operation_id:
                    # Update existing operation
                    operation.status = "queued"
                    operation.retry_count = (operation.retry_count or 0) + 1
                    operation.completed_at = None
                    operation.last_error = None
                    db.session.commit()
                else:
                    # Create a new operation record
                    new_operation = SyncOperation(
                        id=new_operation_id,
                        sync_pair_id=operation.sync_pair_id,
                        operation_type=operation.operation_type,
                        status="queued",
                        created_at=datetime.utcnow(),
                        source_system=operation.source_system,
                        target_system=operation.target_system,
                        retry_count=1
                    )
                    db.session.add(new_operation)
                    db.session.commit()
                
                # Create audit log for successful retry
                create_audit_log(
                    event_type="sync_operation_retried",
                    resource_type="sync_operation",
                    description=f"Operation {operation_id} was successfully retried (new ID: {new_operation_id})",
                    severity="info",
                    resource_id=str(operation.sync_pair_id),
                    operation_id=new_operation_id,
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None
                )
                
                return jsonify({
                    "success": True,
                    "original_operation_id": operation_id,
                    "operation_id": new_operation_id,
                    "status": "queued",
                    "message": f"Operation {operation_id} was successfully retried"
                })
            else:
                # Log the error
                error_data = response.json() if response.text else {"error": "Unknown error"}
                
                create_audit_log(
                    event_type="sync_operation_retry_failed",
                    resource_type="sync_operation",
                    description=f"Failed to retry operation {operation_id}",
                    severity="warning",
                    resource_id=str(operation.sync_pair_id),
                    operation_id=operation.id,
                    user_id=str(user.id) if hasattr(user, 'id') else None,
                    username=user.username if hasattr(user, 'username') else None,
                    new_state=error_data
                )
                
                return jsonify({
                    "success": False,
                    "error": f"SyncService returned status {response.status_code}",
                    "details": error_data
                }), response.status_code
                
        except requests.RequestException as e:
            logger.error(f"Error retrying operation with SyncService: {str(e)}")
            
            create_audit_log(
                event_type="sync_operation_retry_failed",
                resource_type="sync_operation",
                description=f"Error communicating with SyncService to retry operation {operation_id}",
                severity="error",
                resource_id=str(operation.sync_pair_id),
                operation_id=operation.id,
                user_id=str(user.id) if hasattr(user, 'id') else None,
                username=user.username if hasattr(user, 'username') else None,
                new_state={"error": str(e)}
            )
            
            return jsonify({
                "success": False,
                "error": "Could not communicate with SyncService",
                "details": str(e)
            }), 503
        
    except SQLAlchemyError as e:
        logger.error(f"Database error while retrying operation: {str(e)}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in retry_operation: {str(e)}")
        return jsonify({"error": "Server error occurred"}), 500