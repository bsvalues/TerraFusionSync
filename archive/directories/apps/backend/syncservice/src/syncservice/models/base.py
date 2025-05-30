"""
Base model definitions for the SyncService.

This module provides base classes and common utilities for data models.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

# Create SQLAlchemy base
SQLAlchemyBase = declarative_base()


class BaseDBModel(SQLAlchemyBase):
    """Abstract base model for all database tables."""
    
    __abstract__ = True
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BasePydanticModel(BaseModel):
    """Base Pydantic model with common configuration."""
    
    class Config:
        """Pydantic model configuration."""
        arbitrary_types_allowed = True
        from_attributes = True
        populate_by_name = True


class SyncRecord(BasePydanticModel):
    """Base model for records that can be synchronized between systems."""
    
    id: str = Field(..., description="Unique identifier for the record")
    source_id: str = Field(..., description="ID from the source system")
    source_system: str = Field(..., description="Name of the source system")
    last_modified: datetime = Field(..., description="Last modification timestamp")
    data: Dict[str, Any] = Field(..., description="Record data payload")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class SyncResult(BasePydanticModel):
    """Model representing the result of a sync operation."""
    
    success: bool = Field(..., description="Whether the operation was successful")
    count: int = Field(..., description="Number of records processed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Operation timestamp")
    error: Optional[str] = Field(default=None, description="Error message if operation failed")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional result details")


class ConflictRecord(BasePydanticModel):
    """Model representing a conflict between source and target data."""
    
    record_id: str = Field(..., description="ID of the record with conflict")
    source_value: Any = Field(..., description="Value from source system")
    target_value: Any = Field(..., description="Value from target system")
    field_name: str = Field(..., description="Name of the field with conflict")
    resolution_strategy: Optional[str] = Field(default=None, description="Strategy for resolving the conflict")
    
    @field_validator("resolution_strategy")
    @classmethod
    def validate_resolution_strategy(cls, v: Optional[str]) -> Optional[str]:
        """Validate that resolution strategy is one of the allowed values."""
        if v is not None and v not in ["source_wins", "target_wins", "merge", "manual"]:
            raise ValueError("Resolution strategy must be one of: source_wins, target_wins, merge, manual")
        return v


class AuditEvent(BasePydanticModel):
    """Model for audit trail events."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event ID")
    event_type: str = Field(..., description="Type of event")
    component: str = Field(..., description="Component that generated the event")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    record_id: Optional[str] = Field(default=None, description="ID of the affected record")
    user_id: Optional[str] = Field(default=None, description="ID of the user who triggered the event")
    details: Dict[str, Any] = Field(default_factory=dict, description="Event details")
