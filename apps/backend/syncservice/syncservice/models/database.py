"""
Database models for the SyncService.

This module defines SQLAlchemy models for entities stored in the database.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    Float, ForeignKey, JSON, Enum, Table
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.ext.asyncio import AsyncSession

from .base import SyncType, SyncStatus, EntityType, SystemType

Base = declarative_base()


class SourceSystem(Base):
    """Model for source systems registered in the SyncService."""
    __tablename__ = "source_systems"
    
    id = Column(String(50), primary_key=True)
    system_name = Column(String(100), nullable=False)
    system_type = Column(Enum(SystemType), nullable=False)
    connection_string = Column(String(500))
    is_enabled = Column(Boolean, default=True)
    description = Column(Text)
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_pairs = relationship("SyncPair", back_populates="source_system")


class TargetSystem(Base):
    """Model for target systems registered in the SyncService."""
    __tablename__ = "target_systems"
    
    id = Column(String(50), primary_key=True)
    system_name = Column(String(100), nullable=False)
    system_type = Column(Enum(SystemType), nullable=False)
    connection_string = Column(String(500))
    is_enabled = Column(Boolean, default=True)
    description = Column(Text)
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sync_pairs = relationship("SyncPair", back_populates="target_system")


class SyncPair(Base):
    """Model for sync pairs between source and target systems."""
    __tablename__ = "sync_pairs"
    
    id = Column(String(50), primary_key=True)
    source_system_id = Column(String(50), ForeignKey("source_systems.id"), nullable=False)
    target_system_id = Column(String(50), ForeignKey("target_systems.id"), nullable=False)
    description = Column(Text)
    is_enabled = Column(Boolean, default=True)
    entity_mappings = Column(JSON)  # Maps entity types between source and target
    field_mapping_path = Column(String(500))
    sync_schedule = Column(String(100))  # Cron expression
    last_full_sync = Column(DateTime)
    last_incremental_sync = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    source_system = relationship("SourceSystem", back_populates="sync_pairs")
    target_system = relationship("TargetSystem", back_populates="sync_pairs")
    sync_operations = relationship("SyncOperationRecord", back_populates="sync_pair")


class SyncOperationRecord(Base):
    """Model for sync operation records."""
    __tablename__ = "sync_operations"
    
    id = Column(String(50), primary_key=True)
    sync_pair_id = Column(String(50), ForeignKey("sync_pairs.id"), nullable=False)
    sync_type = Column(Enum(SyncType), nullable=False)
    entity_types = Column(JSON)  # List of entity types included in this sync
    status = Column(Enum(SyncStatus), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    details = Column(JSON)  # SyncOperationDetails as JSON
    error = Column(Text)
    
    sync_pair = relationship("SyncPair", back_populates="sync_operations")
    entity_stats = relationship("EntitySyncStat", back_populates="sync_operation")


class EntitySyncStat(Base):
    """Model for entity sync statistics."""
    __tablename__ = "entity_sync_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_operation_id = Column(String(50), ForeignKey("sync_operations.id"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    processed_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    
    sync_operation = relationship("SyncOperationRecord", back_populates="entity_stats")


class SystemMetric(Base):
    """Model for system metrics collected during monitoring."""
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    collection_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Add an index on metric_name and collection_time
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class EventLog(Base):
    """Model for event logs."""
    __tablename__ = "event_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_type = Column(String(50), nullable=False)
    event_source = Column(String(100), nullable=False)
    event_data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Add an index on event_type and timestamp
    __table_args__ = (
        {'sqlite_autoincrement': True},
    )


class ValidationRule(Base):
    """Model for validation rules."""
    __tablename__ = "validation_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=False)
    rule_type = Column(String(50), nullable=False)
    rule_params = Column(JSON)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ResolutionRule(Base):
    """Model for conflict resolution rules."""
    __tablename__ = "resolution_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)
    field_name = Column(String(100), nullable=False)
    resolution_strategy = Column(String(50), nullable=False)
    condition_type = Column(String(50))
    condition_params = Column(JSON)
    priority = Column(Integer, default=0)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)