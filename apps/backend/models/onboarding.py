"""
TerraFusion SyncService - Onboarding Models

This module provides models for the onboarding experience and tutorial progress tracking.
"""

from datetime import datetime
import json

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from apps.backend.database import get_shared_db

db = get_shared_db()

class UserOnboarding(db.Model):
    """
    User onboarding progress model.
    
    Tracks a user's progress through the onboarding process.
    """
    __tablename__ = 'user_onboarding'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Onboarding status
    is_completed = Column(Boolean, default=False)
    current_step = Column(String(50))  # ID of the current onboarding step
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Onboarding data
    progress_data = Column(Text)  # JSON encoded progress data
    
    # Relationships
    user = relationship("User")
    events = relationship("OnboardingEvent", back_populates="onboarding", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<UserOnboarding user_id={self.user_id} completed={self.is_completed}>"
    
    @property
    def progress(self):
        """Get user's progress as a percentage."""
        if self.is_completed:
            return 100
        
        if not self.progress_data:
            return 0
        
        try:
            data = json.loads(self.progress_data)
            completed = data.get('completed_steps', [])
            total = data.get('total_steps', 1)
            
            if total == 0:
                return 0
                
            return round((len(completed) / total) * 100)
        except Exception:
            return 0
    
    @property
    def completed_steps(self):
        """Get list of completed step IDs."""
        if not self.progress_data:
            return []
            
        try:
            data = json.loads(self.progress_data)
            return data.get('completed_steps', [])
        except Exception:
            return []
    
    def mark_step_completed(self, step_id):
        """Mark a step as completed."""
        data = {}
        if self.progress_data:
            try:
                data = json.loads(self.progress_data)
            except Exception:
                data = {}
        
        completed = data.get('completed_steps', [])
        if step_id not in completed:
            completed.append(step_id)
            
        data['completed_steps'] = completed
        self.progress_data = json.dumps(data)
        
        # Create event
        event = OnboardingEvent(
            onboarding_id=self.id,
            event_type='step_completed',
            step_id=step_id
        )
        db.session.add(event)
        
        return True
    
    def complete_onboarding(self):
        """Mark onboarding as completed."""
        self.is_completed = True
        self.completed_at = datetime.utcnow()
        
        # Create event
        event = OnboardingEvent(
            onboarding_id=self.id,
            event_type='onboarding_completed'
        )
        db.session.add(event)
        
        return True

class OnboardingEvent(db.Model):
    """
    Model for onboarding events.
    
    Records interactions and progress during the onboarding process.
    """
    __tablename__ = 'onboarding_events'
    
    id = Column(Integer, primary_key=True)
    onboarding_id = Column(Integer, ForeignKey('user_onboarding.id'), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # e.g., 'step_viewed', 'step_completed', etc.
    step_id = Column(String(50), nullable=True)  # ID of the related step (if applicable)
    
    # Event data
    data = Column(Text, nullable=True)  # JSON encoded event data
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    onboarding = relationship("UserOnboarding", back_populates="events")
    
    def __repr__(self):
        return f"<OnboardingEvent {self.event_type} {self.step_id}>"