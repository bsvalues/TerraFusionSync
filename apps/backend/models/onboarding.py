"""
Onboarding models for TerraFusion SyncService.

This module provides database models for user onboarding and tutorial progress.
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship

from apps.backend.database import db

class UserOnboarding(db.Model):
    """User onboarding progress tracking."""
    
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), nullable=False, unique=True, index=True)
    current_step = Column(Integer, default=1)
    tutorial_complete = Column(Boolean, default=False)
    tutorial_dismissed = Column(Boolean, default=False)
    progress = Column(Text, default='{}')  # JSON string for step progress
    completion_date = Column(DateTime, nullable=True)
    dismissed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def progress_dict(self):
        """Get the progress as a dictionary."""
        if not self.progress:
            return {}
        try:
            return json.loads(self.progress)
        except json.JSONDecodeError:
            return {}
    
    def get_progress_percentage(self):
        """Calculate the percentage of tutorial completion."""
        if self.tutorial_complete:
            return 100
        
        # Get total completed steps
        completed_steps = len([step for step in self.progress_dict.values() 
                            if step.get('completed', False)])
        
        # Calculate percentage based on current step (subtract 1 since current step is not complete)
        if completed_steps == 0:
            return 0
        
        # Use max of completed steps or current step - 1
        completed = max(completed_steps, self.current_step - 1)
        
        # Get steps from configuration based on role (default to 3 steps if not found)
        # This is a rough approximation since we don't know the role here
        total_steps = 5  # Reasonable default
        
        return min(int((completed / total_steps) * 100), 100)
    
    def __repr__(self):
        return f"<UserOnboarding id={self.id} user_id={self.user_id} current_step={self.current_step} complete={self.tutorial_complete}>"