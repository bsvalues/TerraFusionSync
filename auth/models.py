"""
TerraFusion Platform - Authentication Models

This module provides database models for users, sessions, and authentication.
"""
import datetime
import logging
import secrets
import uuid
from typing import List, Dict, Any, Optional

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

# Use the db instance from app.py
from app import db

logger = logging.getLogger(__name__)

class User(db.Model):
    """
    User model representing system users.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    role = Column(String(32), nullable=False, default='Staff')
    county_access = Column(JSON, nullable=False, default=list)
    active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, nullable=True)
    
    # Relationships
    audit_logs = relationship('AuditLog', back_populates='user', lazy='dynamic')
    refresh_tokens = relationship('RefreshToken', back_populates='user', lazy='dynamic')
    
    def __init__(self, username: str, email: str, password: str, role: str = 'Staff', 
                 first_name: Optional[str] = None, last_name: Optional[str] = None,
                 county_access: Optional[List[str]] = None) -> None:
        """
        Initialize a new user.
        
        Args:
            username: Unique username
            email: User's email address
            password: Plain text password to be hashed
            role: User role (default: 'Staff')
            first_name: User's first name
            last_name: User's last name
            county_access: List of county IDs the user has access to
        """
        self.username = username
        self.email = email
        self.set_password(password)
        self.role = role
        self.first_name = first_name
        self.last_name = last_name
        self.county_access = county_access if county_access is not None else []
        self.created_at = datetime.datetime.utcnow()
        self.updated_at = datetime.datetime.utcnow()
        self.password_changed_at = datetime.datetime.utcnow()
    
    def set_password(self, password: str) -> None:
        """
        Set a hashed password for the user.
        
        Args:
            password: Plain text password to be hashed
        """
        self.password_hash = generate_password_hash(password)
        self.password_changed_at = datetime.datetime.utcnow()
    
    def check_password(self, password: str) -> bool:
        """
        Check if the provided password matches the stored hash.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if the password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def record_login(self) -> None:
        """Record a successful login by updating the last_login_at timestamp."""
        self.last_login_at = datetime.datetime.utcnow()
        db.session.commit()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the user to a dictionary.
        
        Returns:
            Dictionary representation of the user
        """
        return {
            'id': self.id,
            'uuid': self.uuid,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'county_access': self.county_access,
            'active': self.active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
    
    def __repr__(self) -> str:
        """String representation of the user."""
        return f"<User {self.username} ({self.id})>"


class RefreshToken(db.Model):
    """
    Refresh token for JWT authentication.
    """
    __tablename__ = 'refresh_tokens'
    
    id = Column(Integer, primary_key=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='refresh_tokens')
    
    def __init__(self, user_id: int, expires_at: datetime.datetime) -> None:
        """
        Initialize a new refresh token.
        
        Args:
            user_id: ID of the user
            expires_at: Expiration timestamp
        """
        self.token = secrets.token_urlsafe(64)
        self.user_id = user_id
        self.expires_at = expires_at
        self.revoked = False
        self.created_at = datetime.datetime.utcnow()
    
    def is_valid(self) -> bool:
        """
        Check if the token is valid (not expired and not revoked).
        
        Returns:
            True if the token is valid, False otherwise
        """
        now = datetime.datetime.utcnow()
        return not self.revoked and now < self.expires_at
    
    def revoke(self) -> None:
        """Mark the token as revoked."""
        self.revoked = True
        db.session.commit()
    
    @classmethod
    def get_by_token(cls, token: str) -> Optional["RefreshToken"]:
        """
        Find a refresh token by its value.
        
        Args:
            token: Token value to search for
            
        Returns:
            RefreshToken instance or None if not found
        """
        return cls.query.filter_by(token=token).first()
    
    @classmethod
    def revoke_all_for_user(cls, user_id: int) -> None:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            user_id: ID of the user
        """
        cls.query.filter_by(user_id=user_id, revoked=False).update({'revoked': True})
        db.session.commit()
        
    def __repr__(self) -> str:
        """String representation of the refresh token."""
        return f"<RefreshToken {self.id} for user {self.user_id}>"


class AuditLog(db.Model):
    """
    Audit log for tracking user actions and system events.
    """
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.utcnow, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(String(128), nullable=True, index=True)
    action = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(255), nullable=True)
    county_id = Column(String(64), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    severity = Column(String(32), nullable=False, default='INFO')
    correlation_id = Column(String(64), nullable=True, index=True)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    def __init__(self, event_type: str, resource_type: str, action: str, user_id: Optional[int] = None,
                 resource_id: Optional[str] = None, description: Optional[str] = None,
                 ip_address: Optional[str] = None, user_agent: Optional[str] = None,
                 county_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None,
                 severity: str = 'INFO', correlation_id: Optional[str] = None) -> None:
        """
        Initialize a new audit log entry.
        
        Args:
            event_type: Type of event (e.g., 'login', 'data_sync', 'config_change')
            resource_type: Type of resource being acted upon
            action: Action performed (e.g., 'create', 'update', 'delete')
            user_id: ID of the user who performed the action (if applicable)
            resource_id: ID of the resource being acted upon (if applicable)
            description: Human-readable description of the event
            ip_address: IP address of the user
            user_agent: User agent string
            county_id: ID of the county (if applicable)
            details: Additional details about the event (as JSON)
            severity: Severity of the event ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
            correlation_id: ID for correlating related events
        """
        self.uuid = str(uuid.uuid4())
        self.user_id = user_id
        self.timestamp = datetime.datetime.utcnow()
        self.event_type = event_type
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.action = action
        self.description = description
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.county_id = county_id
        self.details = details
        self.severity = severity
        self.correlation_id = correlation_id
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the audit log entry to a dictionary.
        
        Returns:
            Dictionary representation of the audit log entry
        """
        username = self.user.username if self.user else None
        
        return {
            'id': self.id,
            'uuid': self.uuid,
            'user_id': self.user_id,
            'username': username,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'action': self.action,
            'description': self.description,
            'ip_address': self.ip_address,
            'county_id': self.county_id,
            'details': self.details,
            'severity': self.severity,
            'correlation_id': self.correlation_id
        }
    
    @classmethod
    def create(cls, **kwargs) -> 'AuditLog':
        """
        Create and save a new audit log entry.
        
        Args:
            **kwargs: Audit log fields
            
        Returns:
            The created AuditLog instance
        """
        log = cls(**kwargs)
        db.session.add(log)
        db.session.commit()
        return log
    
    def __repr__(self) -> str:
        """String representation of the audit log entry."""
        return f"<AuditLog {self.id}: {self.event_type} {self.action} on {self.resource_type} by user {self.user_id}>"