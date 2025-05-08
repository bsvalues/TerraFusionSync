"""
TerraFusion SyncService - User Model

This module provides the User model for authentication and authorization.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from apps.backend.database import get_shared_db

db = get_shared_db()

class User(db.Model, UserMixin):
    """
    User model for authentication and authorization.
    
    This model represents a user in the system, with authentication
    details and role information.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    
    # User information
    first_name = Column(String(64))
    last_name = Column(String(64))
    role = Column(String(20), default='Staff')  # ITAdmin, Assessor, Staff, Auditor
    
    # LDAP information
    is_ldap_user = Column(Boolean, default=False)
    ldap_dn = Column(String(256))  # LDAP Distinguished Name
    
    # Account status
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Settings and preferences
    settings = Column(Text)  # JSON encoded user settings
    
    # Onboarding relationship
    onboarding = relationship("UserOnboarding", uselist=False, back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"
    
    def set_password(self, password):
        """Set user password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def has_permission(self, permission):
        """
        Check if user has a specific permission.
        
        Permissions are based on roles:
        - ITAdmin: full access to all features
        - Assessor: view and approve sync operations
        - Staff: upload data only
        - Auditor: view only
        
        Args:
            permission: The permission to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Map permissions to roles
        permission_map = {
            # All users can view the dashboard
            'dashboard_view': ['ITAdmin', 'Assessor', 'Staff', 'Auditor'],
            
            # Sync operation permissions
            'sync_view': ['ITAdmin', 'Assessor', 'Staff', 'Auditor'],
            'sync_create': ['ITAdmin', 'Assessor'],
            'sync_edit': ['ITAdmin', 'Assessor'],
            'sync_approve': ['ITAdmin', 'Assessor'],
            'sync_rollback': ['ITAdmin'],
            
            # Data upload permissions
            'data_upload': ['ITAdmin', 'Staff', 'Assessor'],
            'data_approve': ['ITAdmin', 'Assessor'],
            
            # Admin permissions
            'admin_access': ['ITAdmin'],
            'system_config': ['ITAdmin'],
            
            # Audit permissions
            'audit_view': ['ITAdmin', 'Auditor'],
            'metrics_view': ['ITAdmin'],
        }
        
        # ITAdmin has all permissions
        if self.role == 'ITAdmin':
            return True
        
        # Check if user's role is in the list of roles for the permission
        return self.role in permission_map.get(permission, [])