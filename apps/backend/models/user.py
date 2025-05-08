"""
TerraFusion SyncService - User Models

This module provides database models for user management.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from apps.backend.database import get_shared_db

db = get_shared_db()

class User(UserMixin, db.Model):
    """
    User model for authentication and user management.
    
    Stores user credentials, roles, and profile information.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    role = Column(String(50), nullable=False, default='Staff')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0)
    is_ldap_user = Column(Boolean, default=False)
    
    # Relationships
    onboarding = relationship("UserOnboarding", back_populates="user", uselist=False)
    
    def set_password(self, password):
        """Set hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def record_login(self):
        """Record a successful login."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
    
    @property
    def full_name(self):
        """Get full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username