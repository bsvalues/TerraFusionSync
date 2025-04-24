"""
System configuration for SyncService.

This module provides a configuration mechanism for specifying source and target systems
and their connection parameters.
"""

import os
from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class SystemConfig(BaseModel):
    """
    Configuration for a system connection.
    
    This model defines the connection parameters for a source or target system.
    """
    
    system_type: str = Field(..., description="Type of system (e.g., pacs, cama, gis, erp)")
    system_name: str = Field(..., description="Name of the system instance")
    connection_params: Dict[str, Any] = Field(..., description="Connection parameters")
    is_enabled: bool = Field(default=True, description="Whether this system is enabled")
    description: Optional[str] = Field(default=None, description="Description of the system")


class SourceSystemConfig(SystemConfig):
    """
    Configuration for a source system.
    
    This extends the base system configuration with source-specific settings.
    """
    
    entity_types: List[str] = Field(default=[], description="Entity types available in this source system")
    batch_size: int = Field(default=100, description="Batch size for fetching records")
    include_inactive: bool = Field(default=False, description="Whether to include inactive/archived records")


class TargetSystemConfig(SystemConfig):
    """
    Configuration for a target system.
    
    This extends the base system configuration with target-specific settings.
    """
    
    entity_types: List[str] = Field(default=[], description="Entity types available in this target system")
    upsert_mode: bool = Field(default=True, description="Whether to use upsert mode (update if exists, insert otherwise)")
    allow_delete: bool = Field(default=False, description="Whether to allow deletion of records")


class SyncPairConfig(BaseModel):
    """
    Configuration for a sync pair.
    
    This model defines a mapping between a source and target system for synchronization.
    """
    
    pair_id: str = Field(..., description="Unique identifier for this sync pair")
    source_system: str = Field(..., description="Name of the source system")
    target_system: str = Field(..., description="Name of the target system")
    is_enabled: bool = Field(default=True, description="Whether this sync pair is enabled")
    entity_mappings: Dict[str, str] = Field(..., description="Mapping of entity types from source to target")
    field_mapping_path: Optional[str] = Field(default=None, description="Path to field mapping configuration")
    description: Optional[str] = Field(default=None, description="Description of the sync pair")


class SyncConfig(BaseModel):
    """
    Configuration for the SyncService.
    
    This model defines the overall configuration for the SyncService, including all
    source systems, target systems, and sync pairs.
    """
    
    source_systems: Dict[str, SourceSystemConfig] = Field(default_factory=dict, description="Source system configurations")
    target_systems: Dict[str, TargetSystemConfig] = Field(default_factory=dict, description="Target system configurations")
    sync_pairs: Dict[str, SyncPairConfig] = Field(default_factory=dict, description="Sync pair configurations")


# Default configuration
DEFAULT_CONFIG = SyncConfig(
    source_systems={
        "default_pacs": SourceSystemConfig(
            system_type="pacs",
            system_name="default_pacs",
            description="Default PACS source system",
            connection_params={
                "driver": os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server"),
                "host": os.getenv("SQLSERVER_HOST", "localhost"),
                "port": int(os.getenv("SQLSERVER_PORT", "1433")),
                "database": os.getenv("SQLSERVER_DATABASE", "PACS"),
                "user": os.getenv("SQLSERVER_USER", "sa"),
                "password": os.getenv("SQLSERVER_PASSWORD", ""),
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
            },
            entity_types=["property", "owner", "value", "structure"]
        ),
        "sample_gis": SourceSystemConfig(
            system_type="gis",
            system_name="sample_gis",
            description="Sample GIS source system",
            connection_params={
                "api_url": os.getenv("GIS_API_URL", "https://gis-api.example.com/v1"),
                "api_key": os.getenv("GIS_API_KEY", ""),
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
            },
            entity_types=["parcel", "zoning", "district", "boundary"],
            is_enabled=False  # Disabled by default until API key is configured
        )
    },
    target_systems={
        "default_cama": TargetSystemConfig(
            system_type="cama",
            system_name="default_cama",
            description="Default CAMA target system",
            connection_params={
                "host": os.getenv("PGHOST", "localhost"),
                "port": int(os.getenv("PGPORT", "5432")),
                "database": os.getenv("PGDATABASE", "postgres"),
                "user": os.getenv("PGUSER", "postgres"),
                "password": os.getenv("PGPASSWORD", ""),
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
            },
            entity_types=["property", "owner", "value", "structure"]
        ),
        "sample_erp": TargetSystemConfig(
            system_type="erp",
            system_name="sample_erp",
            description="Sample ERP target system",
            connection_params={
                "api_url": os.getenv("ERP_API_URL", "https://erp-api.example.com/v1"),
                "api_key": os.getenv("ERP_API_KEY", ""),
                "tenant_id": os.getenv("ERP_TENANT_ID", "default"),
                "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true"
            },
            entity_types=["asset", "financial", "property", "tax"],
            is_enabled=False  # Disabled by default until API key is configured
        )
    },
    sync_pairs={
        "default_pacs_to_cama": SyncPairConfig(
            pair_id="default_pacs_to_cama",
            source_system="default_pacs",
            target_system="default_cama",
            description="Default PACS to CAMA sync",
            entity_mappings={
                "property": "property",
                "owner": "owner", 
                "value": "value",
                "structure": "structure"
            },
            field_mapping_path="syncservice/field_mapping.yaml"
        ),
        "gis_to_cama": SyncPairConfig(
            pair_id="gis_to_cama",
            source_system="sample_gis",
            target_system="default_cama",
            description="GIS to CAMA sync for spatial data",
            entity_mappings={
                "parcel": "property",
                "zoning": "property",
                "district": "property"
            },
            field_mapping_path="syncservice/field_mapping_gis.yaml",
            is_enabled=False  # Disabled by default until GIS system is configured
        ),
        "pacs_to_erp": SyncPairConfig(
            pair_id="pacs_to_erp",
            source_system="default_pacs",
            target_system="sample_erp",
            description="PACS to ERP sync for financial data",
            entity_mappings={
                "property": "property",
                "value": "financial"
            },
            field_mapping_path="syncservice/field_mapping_erp.yaml",
            is_enabled=False  # Disabled by default until ERP system is configured
        )
    }
)


# Functions to get configuration

def get_sync_config() -> SyncConfig:
    """
    Get the current sync configuration.
    
    This function returns the current configuration for the SyncService.
    
    Returns:
        Current sync configuration
    """
    # In a real implementation, this would load from disk or database
    # For now, just return the default configuration
    return DEFAULT_CONFIG


def get_source_system_config(system_name: str) -> Optional[SourceSystemConfig]:
    """
    Get configuration for a specific source system.
    
    Args:
        system_name: Name of the source system
        
    Returns:
        Source system configuration if found, None otherwise
    """
    sync_config = get_sync_config()
    return sync_config.source_systems.get(system_name)


def get_target_system_config(system_name: str) -> Optional[TargetSystemConfig]:
    """
    Get configuration for a specific target system.
    
    Args:
        system_name: Name of the target system
        
    Returns:
        Target system configuration if found, None otherwise
    """
    sync_config = get_sync_config()
    return sync_config.target_systems.get(system_name)


def get_sync_pair_config(pair_id: str) -> Optional[SyncPairConfig]:
    """
    Get configuration for a specific sync pair.
    
    Args:
        pair_id: ID of the sync pair
        
    Returns:
        Sync pair configuration if found, None otherwise
    """
    sync_config = get_sync_config()
    return sync_config.sync_pairs.get(pair_id)


def get_enabled_sync_pairs() -> List[SyncPairConfig]:
    """
    Get all enabled sync pairs.
    
    Returns:
        List of enabled sync pair configurations
    """
    sync_config = get_sync_config()
    return [pair for pair in sync_config.sync_pairs.values() if pair.is_enabled]