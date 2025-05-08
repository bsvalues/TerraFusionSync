"""
TerraFusion SyncService - Onboarding Models

This module provides database models for the onboarding system,
tracking user progress through the interactive tutorial.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from apps.backend.database import get_shared_db

db = get_shared_db()

class UserOnboarding(db.Model):
    """
    Model to track user progress through the onboarding tutorial.
    
    Stores which steps the user has completed and their current position.
    Each user can have one onboarding record that persists even after
    the tutorial is completed for future reference.
    """
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    role = Column(String(50), nullable=False)
    current_step = Column(Integer, default=1)
    progress = Column(Text, default='{}')  # JSON string to store step completion details
    tutorial_complete = Column(Boolean, default=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime, nullable=True)
    dismissed = Column(Boolean, default=False)
    
    # Relationship
    user = relationship("User", back_populates="onboarding")
    
    @property
    def progress_dict(self):
        """Get the progress as a Python dictionary."""
        if not self.progress:
            return {}
        return json.loads(self.progress)
    
    def mark_step_complete(self, step_number, step_data=None):
        """
        Mark a step as complete and record completion data.
        
        Args:
            step_number: The step number to mark as complete
            step_data: Optional data to store with the step completion
        
        Returns:
            Boolean indicating success
        """
        if not step_data:
            step_data = {"completed_at": datetime.utcnow().isoformat()}
        
        progress_dict = self.progress_dict
        progress_dict[str(step_number)] = step_data
        self.progress = json.dumps(progress_dict)
        
        # Update current step to the next one if this was the current step
        if self.current_step == step_number:
            self.current_step = step_number + 1
        
        self.last_activity = datetime.utcnow()
        return True
    
    def get_progress_percentage(self):
        """Calculate the percentage of tutorial completion."""
        from apps.backend.onboarding.config import get_tutorial_steps
        
        steps = get_tutorial_steps(self.role)
        if not steps:
            return 0
        
        completed = len(self.progress_dict)
        total = len(steps)
        
        return int((completed / total) * 100) if total > 0 else 0
    
    def mark_tutorial_complete(self):
        """Mark the entire tutorial as completed."""
        self.tutorial_complete = True
        self.completion_date = datetime.utcnow()
        self.last_activity = datetime.utcnow()
    
    def dismiss_tutorial(self):
        """Dismiss the tutorial without completing it."""
        self.dismissed = True
        self.last_activity = datetime.utcnow()
    
    def reset_progress(self):
        """Reset the tutorial progress."""
        self.current_step = 1
        self.progress = '{}'
        self.tutorial_complete = False
        self.completion_date = None
        self.dismissed = False
        self.last_activity = datetime.utcnow()

class OnboardingEvent(db.Model):
    """
    Model to track onboarding-related events for analytics.
    
    Records user interactions with the onboarding system for 
    analytics and improvement purposes.
    """
    __tablename__ = 'onboarding_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    event_type = Column(String(50), nullable=False)  # 'step_view', 'step_complete', 'tutorial_complete', etc.
    step_number = Column(Integer, nullable=True)
    event_data = Column(Text, nullable=True)  # JSON string with additional event data
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User")
    
    @classmethod
    def log_event(cls, user_id, event_type, step_number=None, event_data=None):
        """
        Log an onboarding event.
        
        Args:
            user_id: ID of the user
            event_type: Type of event
            step_number: Optional step number
            event_data: Optional additional data
            
        Returns:
            Created OnboardingEvent instance
        """
        event = cls(
            user_id=user_id,
            event_type=event_type,
            step_number=step_number,
            event_data=json.dumps(event_data) if event_data else None
        )
        db.session.add(event)
        db.session.commit()
        return event