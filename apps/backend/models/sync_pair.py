"""
TerraFusion SyncService model for SyncPairs.

This module defines the SyncPair model, representing a configured synchronization
between a source and target system.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from .base import Base


class SyncPair(Base):
    """
    SyncPair model representing a configured synchronization between systems.
    
    A SyncPair defines the source and target systems, along with field mappings
    and transformation rules for data synchronization.
    """
    __tablename__ = 'sync_pairs'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Source system information
    source_system_type = Column(String(50), nullable=False)
    source_system_name = Column(String(255), nullable=False)
    source_system_config = Column(JSON, nullable=True)
    
    # Target system information
    target_system_type = Column(String(50), nullable=False)
    target_system_name = Column(String(255), nullable=False)
    target_system_config = Column(JSON, nullable=True)
    
    # Field mappings and transformations
    field_mappings = Column(JSON, nullable=True)
    
    # Sync configuration
    sync_frequency = Column(String(50), nullable=True)  # manual, hourly, daily, etc.
    last_sync_time = Column(DateTime, nullable=True)
    next_sync_time = Column(DateTime, nullable=True)
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SyncPair {self.id}: {self.name} ({self.source_system_type} -> {self.target_system_type})>"
    
    @property
    def source_system(self):
        """
        Get source system configuration as a dictionary.
        
        Returns:
            Dict containing source system configuration
        """
        if not self.source_system_config:
            return {
                "type": self.source_system_type,
                "name": self.source_system_name
            }
        
        if isinstance(self.source_system_config, str):
            config = json.loads(self.source_system_config)
        else:
            config = self.source_system_config
        
        return {
            "type": self.source_system_type,
            "name": self.source_system_name,
            **config
        }
    
    @property
    def target_system(self):
        """
        Get target system configuration as a dictionary.
        
        Returns:
            Dict containing target system configuration
        """
        if not self.target_system_config:
            return {
                "type": self.target_system_type,
                "name": self.target_system_name
            }
        
        if isinstance(self.target_system_config, str):
            config = json.loads(self.target_system_config)
        else:
            config = self.target_system_config
        
        return {
            "type": self.target_system_type,
            "name": self.target_system_name,
            **config
        }
    
    @property
    def mappings(self):
        """
        Get field mappings as a list of dictionaries.
        
        Returns:
            List of field mapping dictionaries
        """
        if not self.field_mappings:
            return []
        
        if isinstance(self.field_mappings, str):
            return json.loads(self.field_mappings)
        
        return self.field_mappings
    
    def to_dict(self):
        """
        Convert the SyncPair to a dictionary representation.
        
        Returns:
            Dictionary representation of the SyncPair
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "source_system": self.source_system,
            "target_system": self.target_system,
            "field_mappings": self.mappings,
            "sync_frequency": self.sync_frequency,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "next_sync_time": self.next_sync_time.isoformat() if self.next_sync_time else None,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def create_from_dict(cls, data):
        """
        Create a new SyncPair instance from a dictionary.
        
        Args:
            data: Dictionary containing SyncPair data
            
        Returns:
            New SyncPair instance
        """
        source_system = data.get("source_system", {})
        target_system = data.get("target_system", {})
        
        instance = cls(
            name=data.get("name"),
            description=data.get("description"),
            source_system_type=source_system.get("type"),
            source_system_name=source_system.get("name"),
            target_system_type=target_system.get("type"),
            target_system_name=target_system.get("name"),
            sync_frequency=data.get("sync_frequency")
        )
        
        # Extract config from source system
        source_config = {k: v for k, v in source_system.items() 
                        if k not in ("type", "name")}
        if source_config:
            instance.source_system_config = source_config
        
        # Extract config from target system
        target_config = {k: v for k, v in target_system.items() 
                        if k not in ("type", "name")}
        if target_config:
            instance.target_system_config = target_config
        
        # Set field mappings
        if "field_mappings" in data:
            instance.field_mappings = data["field_mappings"]
        
        return instance