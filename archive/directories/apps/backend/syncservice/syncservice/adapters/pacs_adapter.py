"""
PACS system adapter for the SyncService.

This module provides a concrete implementation of the source system adapter
interface for PACS (Property Assessment & Collection System) data.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pyodbc
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from syncservice.interfaces.system_adapter import SourceSystemAdapter
from syncservice.utils.database import execute_source_query

logger = logging.getLogger(__name__)


class PACSAdapter(SourceSystemAdapter):
    """
    Source system adapter for PACS (Property Assessment & Collection System).
    
    This adapter provides connectivity and data access methods for PACS systems,
    which store property assessment and tax information.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the PACS adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters for the PACS system
        """
        super().__init__(connection_params)
        self.engine = None
        self.session_factory = None
    
    async def connect(self) -> bool:
        """
        Establish a connection to the PACS system.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Create connection string
            conn_str = (
                f"DRIVER={{{self.connection_params.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                f"SERVER={self.connection_params.get('host', 'localhost')},"
                f"{self.connection_params.get('port', 1433)};"
                f"DATABASE={self.connection_params.get('database', 'PACS')};"
                f"UID={self.connection_params.get('user')};"
                f"PWD={self.connection_params.get('password')}"
            )
            
            # Create engine
            self.engine = create_async_engine(
                f"mssql+pyodbc:///?odbc_connect={conn_str}",
                future=True,
                echo=self.connection_params.get('debug_mode', False)
            )
            
            # Create session factory
            self.session_factory = sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            return await self.check_connection()
        except Exception as e:
            logger.error(f"Failed to connect to PACS: {str(e)}")
            return False
        
    async def disconnect(self) -> bool:
        """
        Close the connection to the PACS system.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            if self.engine:
                await self.engine.dispose()
                self.engine = None
                self.session_factory = None
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from PACS: {str(e)}")
            return False
    
    async def check_connection(self) -> bool:
        """
        Check if the connection to the PACS system is active.
        
        Returns:
            True if connection is active, False otherwise
        """
        try:
            if not self.engine:
                return False
                
            async with self.session_factory() as session:
                result = await session.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Failed to check PACS connection: {str(e)}")
            return False
    
    def get_system_type(self) -> str:
        """
        Get the type of system this adapter connects to.
        
        Returns:
            String identifier for the system type
        """
        return "pacs"
    
    async def get_all_records(
        self, 
        entity_type: str,
        batch_size: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get all records of a specific entity type from the PACS system.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "property", "owner")
            batch_size: Number of records to retrieve in each batch
            **kwargs: Additional filters or parameters
            
        Returns:
            List of records from the PACS system
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "Property",
                "owner": "PropertyOwner",
                "value": "PropertyValue",
                "structure": "Structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            # Build query
            query = f"SELECT * FROM {table_name} WHERE IsActive = 1"
            
            # Add filters
            if kwargs.get('filters'):
                for field, value in kwargs.get('filters').items():
                    if isinstance(value, str):
                        query += f" AND {field} = '{value}'"
                    else:
                        query += f" AND {field} = {value}"
            
            # Add limit
            query += f" ORDER BY LastModified DESC OFFSET 0 ROWS FETCH NEXT {batch_size} ROWS ONLY"
            
            # Execute query
            return await execute_source_query(query)
        except Exception as e:
            logger.error(f"Failed to get {entity_type} records from PACS: {str(e)}")
            return []
    
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
            List of changed records from the PACS system
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "Property",
                "owner": "PropertyOwner",
                "value": "PropertyValue",
                "structure": "Structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            # Format timestamp for SQL Server
            since_str = since.strftime("%Y-%m-%d %H:%M:%S")
            
            # Build query
            query = f"SELECT * FROM {table_name} WHERE LastModified >= '{since_str}' AND IsActive = 1"
            
            # Add filters
            if kwargs.get('filters'):
                for field, value in kwargs.get('filters').items():
                    if isinstance(value, str):
                        query += f" AND {field} = '{value}'"
                    else:
                        query += f" AND {field} = {value}"
            
            # Add limit
            query += f" ORDER BY LastModified DESC OFFSET 0 ROWS FETCH NEXT {batch_size} ROWS ONLY"
            
            # Execute query
            return await execute_source_query(query)
        except Exception as e:
            logger.error(f"Failed to get changed {entity_type} records from PACS: {str(e)}")
            return []
    
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
            List of related records from the PACS system
        """
        try:
            if not related_ids:
                return []
                
            # Map entity types to table names and relation fields
            relation_mapping = {
                "owner": {
                    "table": "PropertyOwner",
                    "relation_field": "PropertyID"
                },
                "value": {
                    "table": "PropertyValue",
                    "relation_field": "PropertyID"
                },
                "structure": {
                    "table": "Structure",
                    "relation_field": "PropertyID"
                },
                "property": {
                    "table": "Property",
                    "relation_field": "PropertyID"
                }
            }
            
            relation_info = relation_mapping.get(entity_type.lower())
            if not relation_info:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            # Build query
            placeholders = ", ".join([f"'{id}'" for id in related_ids])
            query = f"SELECT * FROM {relation_info['table']} WHERE {relation_info['relation_field']} IN ({placeholders}) AND IsActive = 1"
            
            # Execute query
            return await execute_source_query(query)
        except Exception as e:
            logger.error(f"Failed to get related {entity_type} records from PACS: {str(e)}")
            return []