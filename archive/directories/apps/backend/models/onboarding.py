"""
Onboarding Database Models

This module defines the database models used to track user onboarding progress.
"""

from datetime import datetime
from typing import List, Optional

import sqlalchemy as sa
from sqlalchemy.orm import relationship

from apps.backend.database import get_shared_db

# Get the shared database instance
db = get_shared_db()


class UserOnboarding(db.Model):
    """
    Tracks a user's overall onboarding progress.
    
    Each user has at most one UserOnboarding record.
    """
    __tablename__ = 'user_onboarding'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), unique=True, nullable=False)
    user = relationship("User", back_populates="onboarding")
    
    tutorial_id = sa.Column(sa.String(50), nullable=False)  # ID of the tutorial assigned to the user
    started_at = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    last_step_id = sa.Column(sa.String(50), nullable=True)  # ID of the last step accessed
    
    # Relationships
    completed_steps = relationship("OnboardingEvent", back_populates="user_onboarding")
    
    @property
    def is_complete(self) -> bool:
        """Check if onboarding is complete."""
        return self.completed_at is not None
    
    @property
    def completed_step_ids(self) -> List[str]:
        """Get IDs of completed steps."""
        return [event.step_id for event in self.completed_steps if event.step_id]
    
    def get_progress_percentage(self, total_steps: int) -> int:
        """
        Calculate the onboarding progress as a percentage.
        
        Args:
            total_steps: Total number of steps in the tutorial
            
        Returns:
            Progress percentage (0-100)
        """
        if self.is_complete:
            return 100
            
        if total_steps <= 0:
            return 0
            
        completed = len(self.completed_step_ids)
        return min(int((completed / total_steps) * 100), 100)
    
    def mark_step_complete(self, step_id: str) -> "OnboardingEvent":
        """
        Mark a step as completed.
        
        Args:
            step_id: The ID of the completed step
            
        Returns:
            The created OnboardingEvent
        """
        # Check if step already completed
        for event in self.completed_steps:
            if event.step_id == step_id:
                # Already completed, return existing event
                return event
                
        # Create new event
        event = OnboardingEvent(
            user_onboarding_id=self.id,
            step_id=step_id,
            event_type="step_completed",
            timestamp=datetime.utcnow()
        )
        
        # Update last step
        self.last_step_id = step_id
        
        # Add to session
        db.session.add(event)
        db.session.commit()
        
        return event
    
    def mark_complete(self) -> None:
        """Mark the entire onboarding as complete."""
        self.completed_at = datetime.utcnow()
        
        # Create completion event
        event = OnboardingEvent(
            user_onboarding_id=self.id,
            event_type="onboarding_completed",
            timestamp=datetime.utcnow()
        )
        
        db.session.add(event)
        db.session.commit()
    
    def reset_progress(self) -> None:
        """Reset onboarding progress."""
        # Clear existing events
        OnboardingEvent.query.filter_by(user_onboarding_id=self.id).delete()
        
        # Reset fields
        self.completed_at = None
        self.last_step_id = None
        self.started_at = datetime.utcnow()
        
        # Create reset event
        event = OnboardingEvent(
            user_onboarding_id=self.id,
            event_type="onboarding_reset",
            timestamp=datetime.utcnow()
        )
        
        db.session.add(event)
        db.session.commit()
    
    @classmethod
    def get_for_user(cls, user_id: int, tutorial_id: str) -> Optional["UserOnboarding"]:
        """
        Get or create an onboarding record for a user.
        
        Args:
            user_id: The user's ID
            tutorial_id: The ID of the tutorial to assign
            
        Returns:
            The UserOnboarding instance
        """
        # Try to find existing record
        onboarding = cls.query.filter_by(user_id=user_id).first()
        
        if onboarding:
            return onboarding
            
        # Create new record
        onboarding = cls(
            user_id=user_id,
            tutorial_id=tutorial_id
        )
        
        # Create started event
        event = OnboardingEvent(
            user_onboarding=onboarding,
            event_type="onboarding_started",
            timestamp=datetime.utcnow()
        )
        
        db.session.add(onboarding)
        db.session.add(event)
        db.session.commit()
        
        return onboarding


class OnboardingEvent(db.Model):
    """
    Tracks onboarding events for a user.
    
    Each event represents an action or milestone in the onboarding process.
    """
    __tablename__ = 'onboarding_event'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_onboarding_id = sa.Column(sa.Integer, sa.ForeignKey('user_onboarding.id'), nullable=False)
    user_onboarding = relationship("UserOnboarding", back_populates="completed_steps")
    
    event_type = sa.Column(sa.String(50), nullable=False)  # e.g., "step_completed", "onboarding_started"
    step_id = sa.Column(sa.String(50), nullable=True)  # Optional, only for step completion events
    timestamp = sa.Column(sa.DateTime, default=datetime.utcnow, nullable=False)
    event_data = sa.Column(sa.JSON, nullable=True)  # Optional additional data
    
    def __repr__(self) -> str:
        return f"<OnboardingEvent {self.event_type} at {self.timestamp}>"