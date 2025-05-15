"""
TerraFusion Platform - Audit Logging

This module provides functions for creating and managing audit logs.
"""
import datetime
import logging
from typing import Optional, Dict, Any, List, Union

from flask import request, g

from app import db
from auth.models import AuditLog

logger = logging.getLogger(__name__)


def create_audit_log(
    event_type: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    description: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
    username: Optional[str] = None,
    severity: str = 'info'
) -> Optional[AuditLog]:
    """
    Create an audit log entry.
    
    Args:
        event_type: Type of event (e.g., 'user_login', 'data_export')
        resource_type: Type of resource (e.g., 'user', 'county', 'export')
        resource_id: ID of the resource
        description: Human-readable description of the event
        details: Additional details as a dictionary
        user_id: ID of the user who performed the action
        username: Username of the user who performed the action
        severity: Event severity ('info', 'warning', 'error')
        
    Returns:
        AuditLog object if successful, None otherwise
    """
    try:
        # Try to get user info from request token payload if not provided
        if (not user_id or not username) and hasattr(request, 'token_payload'):
            token_payload = getattr(request, 'token_payload', None)
            if token_payload:
                user_id = user_id or token_payload.get('sub')
                username = username or token_payload.get('username')
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=int(user_id) if user_id and user_id.isdigit() else None,
            username=username,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request and request.user_agent else None,
            severity=severity,
            created_at=datetime.datetime.utcnow()
        )
        
        # Add to database
        db.session.add(audit_log)
        db.session.commit()
        
        logger.info(f"Audit log created: {event_type} by {username or 'unknown'}")
        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {str(e)}")
        db.session.rollback()
        return None


def get_audit_logs(
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    event_type: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    severity: Optional[str] = None,
    start_date: Optional[datetime.datetime] = None,
    end_date: Optional[datetime.datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[AuditLog]:
    """
    Get audit logs filtered by various criteria.
    
    Args:
        user_id: Filter by user ID
        username: Filter by username
        event_type: Filter by event type
        resource_type: Filter by resource type
        resource_id: Filter by resource ID
        severity: Filter by severity
        start_date: Filter by start date
        end_date: Filter by end date
        limit: Maximum number of logs to return
        offset: Offset for pagination
        
    Returns:
        List of AuditLog objects
    """
    query = AuditLog.query
    
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    
    if username:
        query = query.filter(AuditLog.username == username)
    
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    
    if resource_id:
        query = query.filter(AuditLog.resource_id == resource_id)
    
    if severity:
        query = query.filter(AuditLog.severity == severity)
    
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    
    # Order by created_at descending (newest first)
    query = query.order_by(AuditLog.created_at.desc())
    
    # Apply limit and offset
    query = query.limit(limit).offset(offset)
    
    return query.all()


def get_audit_log_by_id(audit_log_id: int) -> Optional[AuditLog]:
    """
    Get an audit log by its ID.
    
    Args:
        audit_log_id: ID of the audit log
        
    Returns:
        AuditLog object if found, None otherwise
    """
    return AuditLog.query.get(audit_log_id)