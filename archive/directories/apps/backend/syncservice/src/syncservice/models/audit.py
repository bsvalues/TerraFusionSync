"""
Models for the audit functionality.

This module defines the database models and schema for audit records.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from syncservice.models.base import BaseDBModel, BasePydanticModel, SQLAlchemyBase


class SyncAudit(BaseDBModel):
    """SQLAlchemy model for sync_audit table."""
    
    __tablename__ = "sync_audit"
    
    operation_type = Column(String(50), nullable=False, index=True)
    operation_timestamp = Column(DateTime, nullable=False, index=True)
    source_system = Column(String(50), nullable=False)
    target_system = Column(String(50), nullable=False)
    record_count = Column(Integer, nullable=False)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)
    initiated_by = Column(String(100), nullable=True)


class AuditLogEntry(BaseDBModel):
    """SQLAlchemy model for detailed audit log entries."""
    
    __tablename__ = "audit_log"
    
    event_type = Column(String(50), nullable=False, index=True)
    component = Column(String(100), nullable=False)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    record_id = Column(String(100), nullable=True, index=True)
    user_id = Column(String(100), nullable=True)
    details = Column(JSON, nullable=True)
    sync_audit_id = Column(UUID(as_uuid=True), ForeignKey("sync_audit.id"), nullable=True)


class SyncConflict(BaseDBModel):
    """SQLAlchemy model for tracking sync conflicts."""
    
    __tablename__ = "sync_conflicts"
    
    record_id = Column(String(100), nullable=False, index=True)
    source_value = Column(JSON, nullable=True)
    target_value = Column(JSON, nullable=True)
    field_name = Column(String(100), nullable=False)
    resolution_strategy = Column(String(50), nullable=True)
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    

# Pydantic models for API interactions
class AuditLogEntryCreate(BasePydanticModel):
    """Schema for creating a new audit log entry."""
    
    event_type: str
    component: str
    event_timestamp: datetime = datetime.utcnow()
    record_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    sync_audit_id: Optional[str] = None


class AuditLogEntryResponse(BasePydanticModel):
    """Schema for returning an audit log entry."""
    
    id: str
    event_type: str
    component: str
    event_timestamp: datetime
    record_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class SyncAuditCreate(BasePydanticModel):
    """Schema for creating a new sync audit record."""
    
    operation_type: str
    source_system: str = "PACS"
    target_system: str = "CAMA"
    record_count: int
    success: bool
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    initiated_by: Optional[str] = None


class SyncAuditResponse(BasePydanticModel):
    """Schema for returning a sync audit record."""
    
    id: str
    operation_type: str
    operation_timestamp: datetime
    source_system: str
    target_system: str
    record_count: int
    success: bool
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    initiated_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConflictRecordCreate(BasePydanticModel):
    """Schema for creating a new conflict record."""
    
    record_id: str
    source_value: Any
    target_value: Any
    field_name: str
    resolution_strategy: Optional[str] = None


class ConflictRecordResponse(BasePydanticModel):
    """Schema for returning a conflict record."""
    
    id: str
    record_id: str
    source_value: Any
    target_value: Any
    field_name: str
    resolution_strategy: Optional[str]
    resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class BulkAuditResponse(BasePydanticModel):
    """Schema for returning multiple audit records."""
    
    total: int
    items: List[AuditLogEntryResponse]
