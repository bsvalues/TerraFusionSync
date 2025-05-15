"""
TerraFusion Platform - Authentication Models

This module provides the database models for the TerraFusion Platform authentication system.
"""
import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship

from app import db


class User(db.Model):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(256), nullable=True)  # Nullable for LDAP users
    
    # User profile
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    display_name = Column(String(100), nullable=True)
    
    # Role and permissions
    role = Column(String(20), nullable=False, default='Staff')
    active = Column(Boolean, nullable=False, default=True)
    
    # Auth-specific fields
    auth_type = Column(String(20), nullable=False, default='local')  # 'local' or 'ldap'
    county_ids = Column(JSON, nullable=True)  # List of county IDs the user has access to
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow,
                       onupdate=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    audit_logs = relationship('AuditLog', back_populates='user', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user object to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'display_name': self.display_name,
            'role': self.role,
            'active': self.active,
            'auth_type': self.auth_type,
            'county_ids': self.county_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }


class AuditLog(db.Model):
    """Audit log for tracking user actions."""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    username = Column(String(50), nullable=True)
    
    # Audit details
    event_type = Column(String(50), nullable=False)  # e.g., 'user_login', 'data_export'
    resource_type = Column(String(50), nullable=True)  # e.g., 'user', 'county', 'export'
    resource_id = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional details as JSON
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(256), nullable=True)
    severity = Column(String(20), nullable=False, default='info')  # 'info', 'warning', 'error'
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='audit_logs')
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.event_type}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'description': self.description,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }