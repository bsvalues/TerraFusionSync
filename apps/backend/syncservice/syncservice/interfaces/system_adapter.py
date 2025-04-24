"""
System adapter interfaces for SyncService.

This module defines the abstract interfaces for source and target system adapters,
allowing for pluggable support of different system types beyond PACS and CAMA.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union


class BaseSystemAdapter(abc.ABC):
    """
    Base abstract class for all system adapters.
    
    This class defines the common interface that all system adapters must implement,
    regardless of whether they are source or target systems.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the system adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters for the system
        """
        self.connection_params = connection_params
        self.session = None
    
    @abc.abstractmethod
    async def connect(self) -> bool:
        """
        Establish a connection to the system.
        
        Returns:
            True if connection was successful, False otherwise
        """
        pass
        
    @abc.abstractmethod
    async def disconnect(self) -> bool:
        """
        Close the connection to the system.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def check_connection(self) -> bool:
        """
        Check if the connection to the system is active.
        
        Returns:
            True if connection is active, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_system_type(self) -> str:
        """
        Get the type of system this adapter connects to.
        
        Returns:
            String identifier for the system type
        """
        pass


class SourceSystemAdapter(BaseSystemAdapter):
    """
    Abstract class for source system adapters.
    
    Source systems are the systems from which data is extracted for synchronization.
    """
    
    @abc.abstractmethod
    async def get_all_records(
        self, 
        entity_type: str,
        batch_size: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get all records of a specific entity type from the source system.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "property", "owner")
            batch_size: Number of records to retrieve in each batch
            **kwargs: Additional filters or parameters
            
        Returns:
            List of records from the source system
        """
        pass
    
    @abc.abstractmethod
    async def get_changed_records(
        self,
        entity_type: str,
        since: datetime,
        batch_size: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get records of a specific entity type that have changed since a given timestamp.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "property", "owner")
            since: Timestamp to filter changes by
            batch_size: Number of records to retrieve in each batch
            **kwargs: Additional filters or parameters
            
        Returns:
            List of changed records from the source system
        """
        pass
    
    @abc.abstractmethod
    async def get_related_records(
        self,
        entity_type: str,
        related_ids: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get related records for a set of entity identifiers.
        
        Args:
            entity_type: Type of related entity to retrieve (e.g., "owner" for properties)
            related_ids: List of IDs to find related records for
            **kwargs: Additional filters or parameters
            
        Returns:
            List of related records from the source system
        """
        pass


class TargetSystemAdapter(BaseSystemAdapter):
    """
    Abstract class for target system adapters.
    
    Target systems are the systems to which transformed data is written during synchronization.
    """
    
    @abc.abstractmethod
    async def write_records(
        self,
        entity_type: str,
        records: List[Dict[str, Any]],
        **kwargs
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Write records to the target system.
        
        Args:
            entity_type: Type of entity to write (e.g., "property", "owner")
            records: List of records to write to the target system
            **kwargs: Additional parameters
            
        Returns:
            Tuple containing count of successfully written records and list of failed records
        """
        pass
    
    @abc.abstractmethod
    async def get_existing_record(
        self,
        entity_type: str,
        source_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get an existing record from the target system by source identifier.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "property", "owner")
            source_id: Source system ID to look up
            **kwargs: Additional parameters
            
        Returns:
            Record if found, None otherwise
        """
        pass
    
    @abc.abstractmethod
    async def update_record(
        self,
        entity_type: str,
        target_id: str,
        record_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Update an existing record in the target system.
        
        Args:
            entity_type: Type of entity to update (e.g., "property", "owner")
            target_id: Target system ID to update
            record_data: Updated record data
            **kwargs: Additional parameters
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    async def delete_record(
        self,
        entity_type: str,
        target_id: str,
        **kwargs
    ) -> bool:
        """
        Delete a record from the target system.
        
        Args:
            entity_type: Type of entity to delete (e.g., "property", "owner")
            target_id: Target system ID to delete
            **kwargs: Additional parameters
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass