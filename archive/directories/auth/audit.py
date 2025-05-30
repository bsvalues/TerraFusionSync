"""
TerraFusion Platform - Authentication Audit Logging

This module provides functions for logging authentication-related events.
"""
import logging
import uuid
from typing import Dict, Any, Optional

from flask import request, g, session

from auth.models import AuditLog

logger = logging.getLogger(__name__)

# Authentication event types
EVENT_LOGIN_SUCCESS = 'login_success'
EVENT_LOGIN_FAILURE = 'login_failure'
EVENT_LOGOUT = 'logout'
EVENT_PASSWORD_CHANGE = 'password_change'
EVENT_PASSWORD_RESET = 'password_reset'
EVENT_USER_CREATED = 'user_created'
EVENT_USER_UPDATED = 'user_updated'
EVENT_USER_DELETED = 'user_deleted'
EVENT_TOKEN_CREATED = 'token_created'
EVENT_TOKEN_REFRESHED = 'token_refreshed'
EVENT_TOKEN_REVOKED = 'token_revoked'
EVENT_ACCESS_DENIED = 'access_denied'

def log_auth_event(
    event_type: str,
    user_id: Optional[int] = None,
    description: Optional[str] = None,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    severity: str = 'INFO',
    correlation_id: Optional[str] = None
) -> AuditLog:
    """
    Log an authentication-related event.
    
    Args:
        event_type: Authentication event type
        user_id: ID of the user (if available)
        description: Human-readable description of the event
        resource_id: ID of the resource being acted upon (if applicable)
        details: Additional details about the event
        severity: Event severity ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
        correlation_id: ID for correlating related events
        
    Returns:
        The created AuditLog instance
    """
    # Get user ID from session or g if not provided
    if user_id is None:
        if hasattr(g, 'current_user') and g.current_user:
            user_id = g.current_user.get('user_id')
        elif 'user_id' in session:
            user_id = session.get('user_id')
    
    # Generate correlation ID if not provided
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    
    # Get IP address and user agent from request
    ip_address = request.remote_addr
    user_agent = request.user_agent.string if request.user_agent else None
    
    # Create the audit log entry
    return AuditLog.create(
        event_type=event_type,
        resource_type='auth',
        action='authentication',
        user_id=user_id,
        resource_id=resource_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details,
        severity=severity,
        correlation_id=correlation_id
    )

def log_login_success(user_id: int, username: str) -> AuditLog:
    """
    Log a successful login event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        
    Returns:
        The created AuditLog instance
    """
    return log_auth_event(
        event_type=EVENT_LOGIN_SUCCESS,
        user_id=user_id,
        description=f"User {username} logged in successfully",
        details={'username': username},
        severity='INFO'
    )

def log_login_failure(username: str, reason: str) -> AuditLog:
    """
    Log a failed login attempt.
    
    Args:
        username: Username that was attempted
        reason: Reason for the failure
        
    Returns:
        The created AuditLog instance
    """
    return log_auth_event(
        event_type=EVENT_LOGIN_FAILURE,
        description=f"Failed login attempt for user {username}: {reason}",
        details={'username': username, 'reason': reason},
        severity='WARNING'
    )

def log_logout(user_id: int, username: str) -> AuditLog:
    """
    Log a logout event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        
    Returns:
        The created AuditLog instance
    """
    return log_auth_event(
        event_type=EVENT_LOGOUT,
        user_id=user_id,
        description=f"User {username} logged out",
        details={'username': username},
        severity='INFO'
    )

def log_access_denied(
    user_id: Optional[int], 
    username: Optional[str], 
    resource_type: str, 
    resource_id: Optional[str], 
    reason: str
) -> AuditLog:
    """
    Log an access denied event.
    
    Args:
        user_id: ID of the user (if authenticated)
        username: Username of the user (if authenticated)
        resource_type: Type of resource being accessed
        resource_id: ID of the resource (if applicable)
        reason: Reason for denying access
        
    Returns:
        The created AuditLog instance
    """
    description = f"Access denied to {resource_type}"
    if resource_id:
        description += f" {resource_id}"
    
    if username:
        description += f" for user {username}"
    
    description += f": {reason}"
    
    return log_auth_event(
        event_type=EVENT_ACCESS_DENIED,
        user_id=user_id,
        description=description,
        resource_id=resource_id,
        details={
            'username': username,
            'resource_type': resource_type,
            'reason': reason
        },
        severity='WARNING'
    )

def log_token_created(user_id: int, username: str, token_type: str) -> AuditLog:
    """
    Log a token creation event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        token_type: Type of token created ('access' or 'refresh')
        
    Returns:
        The created AuditLog instance
    """
    return log_auth_event(
        event_type=EVENT_TOKEN_CREATED,
        user_id=user_id,
        description=f"{token_type.capitalize()} token created for user {username}",
        details={'username': username, 'token_type': token_type},
        severity='INFO'
    )

def log_token_refreshed(user_id: int, username: str) -> AuditLog:
    """
    Log a token refresh event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        
    Returns:
        The created AuditLog instance
    """
    return log_auth_event(
        event_type=EVENT_TOKEN_REFRESHED,
        user_id=user_id,
        description=f"Access token refreshed for user {username}",
        details={'username': username},
        severity='INFO'
    )

def log_password_change(user_id: int, username: str, is_reset: bool = False) -> AuditLog:
    """
    Log a password change event.
    
    Args:
        user_id: ID of the user
        username: Username of the user
        is_reset: Whether this was a password reset (vs. change)
        
    Returns:
        The created AuditLog instance
    """
    event_type = EVENT_PASSWORD_RESET if is_reset else EVENT_PASSWORD_CHANGE
    action_type = "reset" if is_reset else "changed"
    
    return log_auth_event(
        event_type=event_type,
        user_id=user_id,
        description=f"Password {action_type} for user {username}",
        details={'username': username, 'is_reset': is_reset},
        severity='INFO'
    )