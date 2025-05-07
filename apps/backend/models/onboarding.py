"""
Onboarding models for TerraFusion SyncService.

This module defines models related to user onboarding and interactive tutorials.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from apps.backend.database import db

class UserOnboarding(db.Model):
    """
    Model to track user onboarding and tutorial progress.
    
    Stores information about which tutorials a user has completed,
    their current progress, and preferences.
    """
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    role = Column(String(50), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Progress tracking
    onboarding_completed = Column(Boolean, default=False)
    current_step = Column(Integer, default=1)
    total_steps = Column(Integer, default=5)  # Default tutorial has 5 steps
    
    # Tutorial data
    tutorial_data = Column(JSON, default={})
    
    # User preferences
    dismissed = Column(Boolean, default=False)
    show_tooltips = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<UserOnboarding(user_id='{self.user_id}', role='{self.role}', completed={self.onboarding_completed})>"
    
    def mark_step_completed(self, step_number):
        """Mark a specific tutorial step as completed."""
        if not self.tutorial_data:
            self.tutorial_data = {}
            
        if 'steps' not in self.tutorial_data:
            self.tutorial_data['steps'] = {}
            
        self.tutorial_data['steps'][str(step_number)] = {
            'completed': True,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        self.current_step = step_number + 1
        
        # Check if all steps are completed
        if self.current_step > self.total_steps:
            self.mark_onboarding_completed()
    
    def mark_onboarding_completed(self):
        """Mark the entire onboarding process as completed."""
        self.onboarding_completed = True
        self.completed_at = datetime.utcnow()
    
    def dismiss_onboarding(self):
        """User has dismissed the onboarding tutorial."""
        self.dismissed = True
        
    def get_progress_percentage(self):
        """Get the percentage of tutorial completion."""
        if not self.total_steps:
            return 100
        return int((self.current_step - 1) / self.total_steps * 100)