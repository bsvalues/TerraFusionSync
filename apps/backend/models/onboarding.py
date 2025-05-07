"""
User Onboarding Model Definition

This module contains the data model for tracking user onboarding progress.
"""

import json
from datetime import datetime

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base

from apps.backend.database import db

class UserOnboarding(db.Model):
    """
    User onboarding tracking model.
    
    This model stores the user's progress through the onboarding tutorial.
    """
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(64), unique=True, nullable=False, index=True)
    current_step = Column(Integer, default=1, nullable=False)
    tutorial_complete = Column(Boolean, default=False, nullable=False)
    tutorial_dismissed = Column(Boolean, default=False, nullable=False)
    progress = Column(Text, default='{}', nullable=False)  # JSON string of step completion status
    completion_date = Column(DateTime, nullable=True)
    dismissed_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    @property
    def progress_dict(self):
        """
        Get the progress as a dictionary.
        
        Returns:
            dict: The progress dictionary
        """
        try:
            return json.loads(self.progress)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def get_progress_percentage(self):
        """
        Calculate the percentage of completed steps.
        
        Returns:
            int: Percentage of completed steps (0-100)
        """
        if self.tutorial_complete:
            return 100
            
        progress_data = self.progress_dict
        steps_completed = len(progress_data.keys())
        
        # Calculate percentage based on current available roles
        # Assuming at most 5 steps for any role (the maximum in our current configuration)
        if steps_completed > 0:
            return min(round(steps_completed / 5 * 100), 100)
        return 0
    
    def __repr__(self):
        return f"<UserOnboarding(user_id='{self.user_id}', current_step={self.current_step}, complete={self.tutorial_complete})>"