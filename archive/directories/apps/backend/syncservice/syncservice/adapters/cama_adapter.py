"""
CAMA system adapter for the SyncService.

This module provides a concrete implementation of the target system adapter
interface for CAMA (Computer-Assisted Mass Appraisal) data.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from syncservice.interfaces.system_adapter import TargetSystemAdapter
from syncservice.utils.database import execute_target_query

logger = logging.getLogger(__name__)


class CAMAAdapter(TargetSystemAdapter):
    """
    Target system adapter for CAMA (Computer-Assisted Mass Appraisal).
    
    This adapter provides connectivity and data access methods for CAMA systems,
    which store property assessment information and valuation data.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the CAMA adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters for the CAMA system
        """
        super().__init__(connection_params)
        self.engine = None
        self.session_factory = None
    
    async def connect(self) -> bool:
        """
        Establish a connection to the CAMA system.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Create connection URL
            db_url = (
                f"postgresql+asyncpg://"
                f"{self.connection_params.get('user', 'postgres')}:"
                f"{self.connection_params.get('password', '')}@"
                f"{self.connection_params.get('host', 'localhost')}:"
                f"{self.connection_params.get('port', 5432)}/"
                f"{self.connection_params.get('database', 'postgres')}"
            )
            
            # Create engine
            self.engine = create_async_engine(
                db_url,
                echo=self.connection_params.get('debug_mode', False),
                pool_pre_ping=True,
                pool_recycle=300
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
            logger.error(f"Failed to connect to CAMA: {str(e)}")
            return False
        
    async def disconnect(self) -> bool:
        """
        Close the connection to the CAMA system.
        
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
            logger.error(f"Failed to disconnect from CAMA: {str(e)}")
            return False
    
    async def check_connection(self) -> bool:
        """
        Check if the connection to the CAMA system is active.
        
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
            logger.error(f"Failed to check CAMA connection: {str(e)}")
            return False
    
    def get_system_type(self) -> str:
        """
        Get the type of system this adapter connects to.
        
        Returns:
            String identifier for the system type
        """
        return "cama"
    
    async def write_records(
        self,
        entity_type: str,
        records: List[Dict[str, Any]],
        **kwargs
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Write records to the CAMA system.
        
        Args:
            entity_type: Type of entity to write (e.g., "property", "owner")
            records: List of records to write to the CAMA system
            **kwargs: Additional parameters
            
        Returns:
            Tuple containing count of successfully written records and list of failed records
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "cama_property",
                "owner": "cama_owner",
                "value": "cama_value",
                "structure": "cama_structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return 0, records
                
            success_count = 0
            failed_records = []
            
            for record in records:
                try:
                    # Check if record already exists
                    existing_record = await self.get_existing_record(entity_type, record.get('source_id'))
                    
                    if existing_record:
                        # Update existing record
                        success = await self.update_record(entity_type, existing_record.get('id'), record)
                        if success:
                            success_count += 1
                        else:
                            failed_records.append(record)
                    else:
                        # Create new record
                        
                        # Generate UUID for new record
                        if 'id' not in record:
                            record['id'] = str(uuid.uuid4())
                            
                        # Set creation timestamp
                        if 'created_at' not in record:
                            record['created_at'] = datetime.utcnow()
                            
                        # Set update timestamp
                        record['updated_at'] = datetime.utcnow()
                        
                        # Build column names and values
                        columns = ', '.join(record.keys())
                        placeholders = ', '.join([f"'{value}'" if isinstance(value, str) else str(value) for value in record.values()])
                        
                        # Build query
                        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
                        
                        # Execute query
                        result = await execute_target_query(query)
                        
                        if result is not None:
                            success_count += 1
                        else:
                            failed_records.append(record)
                except Exception as e:
                    logger.error(f"Failed to write {entity_type} record to CAMA: {str(e)}")
                    failed_records.append(record)
            
            return success_count, failed_records
        except Exception as e:
            logger.error(f"Failed to write {entity_type} records to CAMA: {str(e)}")
            return 0, records
    
    async def get_existing_record(
        self,
        entity_type: str,
        source_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get an existing record from the CAMA system by source identifier.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "property", "owner")
            source_id: Source system ID to look up
            **kwargs: Additional parameters
            
        Returns:
            Record if found, None otherwise
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "cama_property",
                "owner": "cama_owner",
                "value": "cama_value",
                "structure": "cama_structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return None
                
            # Build query
            query = f"SELECT * FROM {table_name} WHERE source_id = '{source_id}'"
            
            # Execute query
            results = await execute_target_query(query)
            
            if results and len(results) > 0:
                return results[0]
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get existing {entity_type} record from CAMA: {str(e)}")
            return None
    
    async def update_record(
        self,
        entity_type: str,
        target_id: str,
        record_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Update an existing record in the CAMA system.
        
        Args:
            entity_type: Type of entity to update (e.g., "property", "owner")
            target_id: Target system ID to update
            record_data: Updated record data
            **kwargs: Additional parameters
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "cama_property",
                "owner": "cama_owner",
                "value": "cama_value",
                "structure": "cama_structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return False
                
            # Set update timestamp
            record_data['updated_at'] = datetime.utcnow()
            
            # Build SET clause
            set_clause = ', '.join([
                f"{key} = '{value}'" if isinstance(value, str) else f"{key} = {value}"
                for key, value in record_data.items()
                if key != 'id' and key != 'created_at'  # Don't update ID or creation timestamp
            ])
            
            # Build query
            query = f"UPDATE {table_name} SET {set_clause} WHERE id = '{target_id}'"
            
            # Execute query
            result = await execute_target_query(query)
            
            return result is not None
        except Exception as e:
            logger.error(f"Failed to update {entity_type} record in CAMA: {str(e)}")
            return False
    
    async def delete_record(
        self,
        entity_type: str,
        target_id: str,
        **kwargs
    ) -> bool:
        """
        Delete a record from the CAMA system.
        
        Args:
            entity_type: Type of entity to delete (e.g., "property", "owner")
            target_id: Target system ID to delete
            **kwargs: Additional parameters
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Map entity types to table names
            table_mapping = {
                "property": "cama_property",
                "owner": "cama_owner",
                "value": "cama_value",
                "structure": "cama_structure"
            }
            
            table_name = table_mapping.get(entity_type.lower())
            if not table_name:
                logger.error(f"Unknown entity type: {entity_type}")
                return False
                
            # Build query
            query = f"DELETE FROM {table_name} WHERE id = '{target_id}'"
            
            # Execute query
            result = await execute_target_query(query)
            
            return result is not None
        except Exception as e:
            logger.error(f"Failed to delete {entity_type} record from CAMA: {str(e)}")
            return False