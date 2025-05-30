"""
System adapters for the SyncService.

This package contains concrete implementations of the system adapter interfaces for
various source and target systems. Each adapter provides connectivity and data access
for a specific system type.
"""

from typing import Dict, List, Optional, Type

from syncservice.interfaces.system_adapter import SourceSystemAdapter, TargetSystemAdapter

# Registry of available source and target system adapters
_source_adapters: Dict[str, Type[SourceSystemAdapter]] = {}
_target_adapters: Dict[str, Type[TargetSystemAdapter]] = {}

def register_source_adapter(system_type: str, adapter_class: Type[SourceSystemAdapter]) -> None:
    """
    Register a source system adapter class for a specific system type.
    
    Args:
        system_type: String identifier for the system type
        adapter_class: Adapter class implementation
    """
    _source_adapters[system_type] = adapter_class


def register_target_adapter(system_type: str, adapter_class: Type[TargetSystemAdapter]) -> None:
    """
    Register a target system adapter class for a specific system type.
    
    Args:
        system_type: String identifier for the system type
        adapter_class: Adapter class implementation
    """
    _target_adapters[system_type] = adapter_class


def get_source_adapter_class(system_type: str) -> Optional[Type[SourceSystemAdapter]]:
    """
    Get the source system adapter class for a specific system type.
    
    Args:
        system_type: String identifier for the system type
        
    Returns:
        Source adapter class if registered, None otherwise
    """
    return _source_adapters.get(system_type)


def get_target_adapter_class(system_type: str) -> Optional[Type[TargetSystemAdapter]]:
    """
    Get the target system adapter class for a specific system type.
    
    Args:
        system_type: String identifier for the system type
        
    Returns:
        Target adapter class if registered, None otherwise
    """
    return _target_adapters.get(system_type)


def get_available_source_systems() -> List[str]:
    """
    Get a list of all registered source system types.
    
    Returns:
        List of source system type identifiers
    """
    return list(_source_adapters.keys())


def get_available_target_systems() -> List[str]:
    """
    Get a list of all registered target system types.
    
    Returns:
        List of target system type identifiers
    """
    return list(_target_adapters.keys())


# Import adapters
from syncservice.adapters.pacs_adapter import PACSAdapter
from syncservice.adapters.cama_adapter import CAMAAdapter
from syncservice.adapters.gis_adapter import GISAdapter
from syncservice.adapters.erp_adapter import ERPAdapter

# Register source adapters
register_source_adapter("pacs", PACSAdapter)
register_source_adapter("gis", GISAdapter)

# Register target adapters
register_target_adapter("cama", CAMAAdapter)
register_target_adapter("erp", ERPAdapter)