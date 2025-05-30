"""
Configuration settings for system adapters.

This module provides configuration models for the various source and target systems
supported by the SyncService.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Mapping

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Singleton instance of the configuration
_config_instance = None


class SystemConfig(BaseModel):
    """Base configuration for a system."""
    
    system_id: str = Field(..., description="Unique identifier for this system")
    system_name: str = Field(..., description="Human-readable name for this system")
    system_type: str = Field(..., description="Type of system (pacs, cama, gis, erp)")
    is_enabled: bool = Field(default=True, description="Whether this system is enabled")
    description: Optional[str] = Field(default=None, description="Description of this system")
    connection_params: Dict[str, Any] = Field(..., description="Connection parameters for this system")


class SyncPairConfig(BaseModel):
    """Configuration for a sync pair between source and target systems."""
    
    source_system: str = Field(..., description="ID of the source system")
    target_system: str = Field(..., description="ID of the target system")
    is_enabled: bool = Field(default=True, description="Whether this sync pair is enabled")
    description: Optional[str] = Field(default=None, description="Description of this sync pair")
    entity_mappings: Dict[str, str] = Field(..., description="Mapping of source entity types to target entity types")
    field_mapping_path: Optional[str] = Field(default=None, description="Path to the field mapping YAML file")


class SyncConfig(BaseModel):
    """Overall configuration for the SyncService."""
    
    source_systems: Dict[str, SystemConfig] = Field(default_factory=dict, description="Source systems configuration")
    target_systems: Dict[str, SystemConfig] = Field(default_factory=dict, description="Target systems configuration")
    sync_pairs: Dict[str, SyncPairConfig] = Field(default_factory=dict, description="Sync pairs configuration")


def get_sync_config() -> SyncConfig:
    """
    Get the singleton instance of the sync configuration.
    
    Returns:
        SyncConfig: The sync configuration
    """
    global _config_instance
    
    if _config_instance is None:
        # Create default configuration with PACS, CAMA, GIS, and ERP systems
        _config_instance = SyncConfig(
            source_systems={
                "default_pacs": SystemConfig(
                    system_id="default_pacs",
                    system_name="Default PACS System",
                    system_type="pacs",
                    description="Default Property Assessment and Collection System",
                    connection_params={
                        "driver": os.environ.get("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server"),
                        "host": os.environ.get("SQLSERVER_HOST", "localhost"),
                        "port": int(os.environ.get("SQLSERVER_PORT", "1433")),
                        "database": os.environ.get("SQLSERVER_DATABASE", "PACS"),
                        "user": os.environ.get("SQLSERVER_USER", "sa"),
                        "password": os.environ.get("SQLSERVER_PASSWORD", ""),
                        "debug_mode": os.environ.get("DEBUG_MODE", "False").lower() == "true"
                    }
                ),
                "default_gis": SystemConfig(
                    system_id="default_gis",
                    system_name="Default GIS System",
                    system_type="gis",
                    description="Default Geographic Information System",
                    is_enabled=False,  # Disabled by default
                    connection_params={
                        "base_url": os.environ.get("GIS_BASE_URL", "https://gis.example.com/api"),
                        "api_key": os.environ.get("GIS_API_KEY", ""),
                        "timeout_seconds": int(os.environ.get("GIS_TIMEOUT_SECONDS", "30")),
                        "debug_mode": os.environ.get("DEBUG_MODE", "False").lower() == "true"
                    }
                )
            },
            target_systems={
                "default_cama": SystemConfig(
                    system_id="default_cama",
                    system_name="Default CAMA System",
                    system_type="cama",
                    description="Default Computer-Assisted Mass Appraisal System",
                    connection_params={
                        "host": os.environ.get("POSTGRES_HOST", os.environ.get("PGHOST", "localhost")),
                        "port": int(os.environ.get("POSTGRES_PORT", os.environ.get("PGPORT", "5432"))),
                        "database": os.environ.get("POSTGRES_DATABASE", os.environ.get("PGDATABASE", "postgres")),
                        "user": os.environ.get("POSTGRES_USER", os.environ.get("PGUSER", "postgres")),
                        "password": os.environ.get("POSTGRES_PASSWORD", os.environ.get("PGPASSWORD", "")),
                        "debug_mode": os.environ.get("DEBUG_MODE", "False").lower() == "true"
                    }
                ),
                "default_erp": SystemConfig(
                    system_id="default_erp",
                    system_name="Default ERP System",
                    system_type="erp",
                    description="Default Enterprise Resource Planning System",
                    is_enabled=False,  # Disabled by default
                    connection_params={
                        "base_url": os.environ.get("ERP_BASE_URL", "https://erp.example.com/api"),
                        "tenant_id": os.environ.get("ERP_TENANT_ID", "default"),
                        "api_key": os.environ.get("ERP_API_KEY", ""),
                        "username": os.environ.get("ERP_USERNAME", ""),
                        "password": os.environ.get("ERP_PASSWORD", ""),
                        "timeout_seconds": int(os.environ.get("ERP_TIMEOUT_SECONDS", "30")),
                        "debug_mode": os.environ.get("DEBUG_MODE", "False").lower() == "true"
                    }
                )
            },
            sync_pairs={
                "pacs_to_cama": SyncPairConfig(
                    source_system="default_pacs",
                    target_system="default_cama",
                    description="Sync data from PACS to CAMA",
                    entity_mappings={
                        "property": "property",
                        "owner": "owner",
                        "assessment": "assessment",
                        "building": "improvement",
                        "land": "land"
                    },
                    field_mapping_path="syncservice/config/field_mapping_pacs_cama.yaml"
                ),
                "gis_to_cama": SyncPairConfig(
                    source_system="default_gis",
                    target_system="default_cama",
                    is_enabled=False,  # Disabled by default
                    description="Sync GIS data to CAMA",
                    entity_mappings={
                        "parcel": "land",
                        "structure": "improvement",
                        "zone": "zoning"
                    },
                    field_mapping_path="syncservice/config/field_mapping_gis_cama.yaml"
                ),
                "pacs_to_erp": SyncPairConfig(
                    source_system="default_pacs",
                    target_system="default_erp",
                    is_enabled=False,  # Disabled by default
                    description="Sync financial data from PACS to ERP",
                    entity_mappings={
                        "transaction": "financial_transaction",
                        "payment": "payment",
                        "account": "ledger_account"
                    },
                    field_mapping_path="syncservice/config/field_mapping_pacs_erp.yaml"
                )
            }
        )
    
    return _config_instance


def get_source_system_config(system_id: str) -> Optional[SystemConfig]:
    """
    Get configuration for a source system.
    
    Args:
        system_id: ID of the source system
        
    Returns:
        SystemConfig if found, None otherwise
    """
    config = get_sync_config()
    return config.source_systems.get(system_id)


def get_target_system_config(system_id: str) -> Optional[SystemConfig]:
    """
    Get configuration for a target system.
    
    Args:
        system_id: ID of the target system
        
    Returns:
        SystemConfig if found, None otherwise
    """
    config = get_sync_config()
    return config.target_systems.get(system_id)


def get_sync_pair_config(pair_id: str) -> Optional[SyncPairConfig]:
    """
    Get configuration for a sync pair.
    
    Args:
        pair_id: ID of the sync pair
        
    Returns:
        SyncPairConfig if found, None otherwise
    """
    config = get_sync_config()
    return config.sync_pairs.get(pair_id)