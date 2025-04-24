"""
System adapter interfaces for the SyncService.

This module defines the interfaces that system adapters must implement to
integrate with the SyncService for data synchronization.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set

from ..models.base import SourceRecord, TargetRecord, ValidationResult


class SourceSystemAdapter(ABC):
    """
    Interface for adapters that connect to source systems.
    
    Source systems are the systems from which data is extracted for synchronization.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish a connection to the source system.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the source system.
        """
        pass
    
    @abstractmethod
    async def get_records(
        self,
        entity_type: str,
        modified_since: Optional[datetime] = None,
        batch_size: int = 100,
        offset: int = 0
    ) -> Tuple[List[SourceRecord], int]:
        """
        Get records from the source system.
        
        Args:
            entity_type: Type of entity to retrieve
            modified_since: Only retrieve records modified since this time
            batch_size: Number of records to retrieve in this batch
            offset: Starting offset for pagination
            
        Returns:
            Tuple containing list of records and total count
        """
        pass
    
    @abstractmethod
    async def get_record_by_id(self, entity_type: str, source_id: str) -> Optional[SourceRecord]:
        """
        Get a specific record by its ID.
        
        Args:
            entity_type: Type of entity to retrieve
            source_id: ID of the record in the source system
            
        Returns:
            Record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_record_count(
        self,
        entity_type: str,
        modified_since: Optional[datetime] = None
    ) -> int:
        """
        Get the count of records of a specific type.
        
        Args:
            entity_type: Type of entity to count
            modified_since: Only count records modified since this time
            
        Returns:
            Count of records
        """
        pass
    
    @abstractmethod
    async def get_supported_entity_types(self) -> List[str]:
        """
        Get the entity types supported by this source system.
        
        Returns:
            List of supported entity types
        """
        pass
    
    @abstractmethod
    async def get_field_mapping(self, entity_type: str) -> Dict[str, str]:
        """
        Get the field mapping for a specific entity type.
        
        This mapping defines how fields in the source system map to the
        normalized field names used by the SyncService.
        
        Args:
            entity_type: Type of entity to get mapping for
            
        Returns:
            Dictionary mapping source field names to normalized field names
        """
        pass
    
    @abstractmethod
    async def get_related_records(
        self,
        entity_type: str,
        parent_entity_type: str,
        parent_id: str
    ) -> List[SourceRecord]:
        """
        Get records related to a specific parent record.
        
        Args:
            entity_type: Type of entity to retrieve
            parent_entity_type: Type of the parent entity
            parent_id: ID of the parent record
            
        Returns:
            List of related records
        """
        pass
    
    @abstractmethod
    async def search_records(
        self,
        entity_type: str,
        criteria: Dict[str, Any],
        batch_size: int = 100,
        offset: int = 0
    ) -> Tuple[List[SourceRecord], int]:
        """
        Search for records matching specific criteria.
        
        Args:
            entity_type: Type of entity to search for
            criteria: Dictionary of field-value pairs to match
            batch_size: Number of records to retrieve in this batch
            offset: Starting offset for pagination
            
        Returns:
            Tuple containing list of records and total count
        """
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the source system.
        
        Returns:
            Dictionary containing system information
        """
        pass


class TargetSystemAdapter(ABC):
    """
    Interface for adapters that connect to target systems.
    
    Target systems are the systems to which data is written during synchronization.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish a connection to the target system.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Close the connection to the target system.
        """
        pass
    
    @abstractmethod
    async def create_record(
        self,
        entity_type: str,
        source_id: str,
        data: Dict[str, Any]
    ) -> str:
        """
        Create a new record in the target system.
        
        Args:
            entity_type: Type of entity to create
            source_id: ID of the record in the source system
            data: Data to be stored in the target system
            
        Returns:
            ID of the created record in the target system
        """
        pass
    
    @abstractmethod
    async def update_record(
        self,
        entity_type: str,
        target_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Update an existing record in the target system.
        
        Args:
            entity_type: Type of entity to update
            target_id: ID of the record in the target system
            data: Data to update in the target system
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def delete_record(
        self,
        entity_type: str,
        target_id: str
    ) -> bool:
        """
        Delete a record from the target system.
        
        Args:
            entity_type: Type of entity to delete
            target_id: ID of the record in the target system
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_record_by_id(
        self,
        entity_type: str,
        target_id: str
    ) -> Optional[TargetRecord]:
        """
        Get a specific record by its ID.
        
        Args:
            entity_type: Type of entity to retrieve
            target_id: ID of the record in the target system
            
        Returns:
            Record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_existing_record(
        self,
        entity_type: str,
        source_id: str
    ) -> Optional[TargetRecord]:
        """
        Get an existing record that was previously synced from the source system.
        
        This method should find a record based on the source system ID that was stored
        during a previous synchronization.
        
        Args:
            entity_type: Type of entity to retrieve
            source_id: ID of the record in the source system
            
        Returns:
            Record if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def validate_record(
        self,
        entity_type: str,
        data: Dict[str, Any]
    ) -> ValidationResult:
        """
        Validate a record before creating or updating it in the target system.
        
        Args:
            entity_type: Type of entity to validate
            data: Data to validate
            
        Returns:
            Validation result object
        """
        pass
    
    @abstractmethod
    async def get_supported_entity_types(self) -> List[str]:
        """
        Get the entity types supported by this target system.
        
        Returns:
            List of supported entity types
        """
        pass
    
    @abstractmethod
    async def get_field_mapping(self, entity_type: str) -> Dict[str, str]:
        """
        Get the field mapping for a specific entity type.
        
        This mapping defines how normalized field names used by the SyncService
        map to field names in the target system.
        
        Args:
            entity_type: Type of entity to get mapping for
            
        Returns:
            Dictionary mapping normalized field names to target field names
        """
        pass
    
    @abstractmethod
    async def bulk_create_records(
        self,
        entity_type: str,
        records: List[Tuple[str, Dict[str, Any]]]
    ) -> List[Tuple[str, str]]:
        """
        Create multiple records in bulk.
        
        Args:
            entity_type: Type of entity to create
            records: List of tuples containing source ID and data
            
        Returns:
            List of tuples containing source ID and corresponding target ID
        """
        pass
    
    @abstractmethod
    async def bulk_update_records(
        self,
        entity_type: str,
        records: List[Tuple[str, Dict[str, Any]]]
    ) -> List[str]:
        """
        Update multiple records in bulk.
        
        Args:
            entity_type: Type of entity to update
            records: List of tuples containing target ID and data
            
        Returns:
            List of target IDs that were successfully updated
        """
        pass
    
    @abstractmethod
    async def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the target system.
        
        Returns:
            Dictionary containing system information
        """
        pass