"""
ERP system adapter for the SyncService.

This module provides a concrete implementation of the target system adapter
interface for ERP (Enterprise Resource Planning) data.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests

from syncservice.interfaces.system_adapter import TargetSystemAdapter

logger = logging.getLogger(__name__)


class ERPAdapter(TargetSystemAdapter):
    """
    Target system adapter for ERP (Enterprise Resource Planning).
    
    This adapter provides connectivity and data access methods for ERP systems,
    which integrate core business processes.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the ERP adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters for the ERP system
        """
        super().__init__(connection_params)
        self.api_url = connection_params.get('api_url')
        self.api_key = connection_params.get('api_key')
        self.tenant_id = connection_params.get('tenant_id')
        self.session = None
    
    async def connect(self) -> bool:
        """
        Establish a connection to the ERP system.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Create requests session
            self.session = requests.Session()
            
            # Set default headers
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-Tenant-ID': self.tenant_id
            })
            
            # Test connection
            return await self.check_connection()
        except Exception as e:
            logger.error(f"Failed to connect to ERP: {str(e)}")
            return False
        
    async def disconnect(self) -> bool:
        """
        Close the connection to the ERP system.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            if self.session:
                self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from ERP: {str(e)}")
            return False
    
    async def check_connection(self) -> bool:
        """
        Check if the connection to the ERP system is active.
        
        Returns:
            True if connection is active, False otherwise
        """
        try:
            if not self.session or not self.api_url:
                return False
                
            # Make a test request to the ERP API
            response = self.session.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to check ERP connection: {str(e)}")
            return False
    
    def get_system_type(self) -> str:
        """
        Get the type of system this adapter connects to.
        
        Returns:
            String identifier for the system type
        """
        return "erp"
    
    async def write_records(
        self,
        entity_type: str,
        records: List[Dict[str, Any]],
        **kwargs
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Write records to the ERP system.
        
        Args:
            entity_type: Type of entity to write (e.g., "asset", "financial")
            records: List of records to write to the ERP system
            **kwargs: Additional parameters
            
        Returns:
            Tuple containing count of successfully written records and list of failed records
        """
        try:
            if not self.session or not self.api_url:
                return 0, records
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "asset": "assets",
                "financial": "financials",
                "property": "properties",
                "tax": "taxes"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
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
                        
                        # Generate ID for new record if not present
                        if 'id' not in record:
                            record['id'] = str(uuid.uuid4())
                            
                        # Set metadata
                        if 'metadata' not in record:
                            record['metadata'] = {}
                            
                        record['metadata']['created_at'] = datetime.utcnow().isoformat()
                        record['metadata']['updated_at'] = datetime.utcnow().isoformat()
                        record['metadata']['sync_source'] = kwargs.get('source_system', 'unknown')
                        
                        # Make request
                        response = self.session.post(f"{self.api_url}/{endpoint}", json=record)
                        
                        # Check response
                        if response.status_code in (200, 201):
                            success_count += 1
                        else:
                            logger.error(f"Failed to create {entity_type} record in ERP: {response.text}")
                            failed_records.append(record)
                except Exception as e:
                    logger.error(f"Failed to write {entity_type} record to ERP: {str(e)}")
                    failed_records.append(record)
            
            return success_count, failed_records
        except Exception as e:
            logger.error(f"Failed to write {entity_type} records to ERP: {str(e)}")
            return 0, records
    
    async def get_existing_record(
        self,
        entity_type: str,
        source_id: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get an existing record from the ERP system by source identifier.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "asset", "financial")
            source_id: Source system ID to look up
            **kwargs: Additional parameters
            
        Returns:
            Record if found, None otherwise
        """
        try:
            if not self.session or not self.api_url:
                return None
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "asset": "assets",
                "financial": "financials",
                "property": "properties",
                "tax": "taxes"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
                logger.error(f"Unknown entity type: {entity_type}")
                return None
                
            # Make request
            response = self.session.get(f"{self.api_url}/{endpoint}", params={'source_id': source_id})
            
            # Check response
            if response.status_code != 200:
                return None
                
            # Parse response
            data = response.json()
            records = data.get('records', [])
            
            if records and len(records) > 0:
                return records[0]
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get existing {entity_type} record from ERP: {str(e)}")
            return None
    
    async def update_record(
        self,
        entity_type: str,
        target_id: str,
        record_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Update an existing record in the ERP system.
        
        Args:
            entity_type: Type of entity to update (e.g., "asset", "financial")
            target_id: Target system ID to update
            record_data: Updated record data
            **kwargs: Additional parameters
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            if not self.session or not self.api_url:
                return False
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "asset": "assets",
                "financial": "financials",
                "property": "properties",
                "tax": "taxes"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
                logger.error(f"Unknown entity type: {entity_type}")
                return False
                
            # Update metadata
            if 'metadata' not in record_data:
                record_data['metadata'] = {}
                
            record_data['metadata']['updated_at'] = datetime.utcnow().isoformat()
            record_data['metadata']['sync_source'] = kwargs.get('source_system', 'unknown')
            
            # Make request
            response = self.session.put(f"{self.api_url}/{endpoint}/{target_id}", json=record_data)
            
            # Check response
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Failed to update {entity_type} record in ERP: {str(e)}")
            return False
    
    async def delete_record(
        self,
        entity_type: str,
        target_id: str,
        **kwargs
    ) -> bool:
        """
        Delete a record from the ERP system.
        
        Args:
            entity_type: Type of entity to delete (e.g., "asset", "financial")
            target_id: Target system ID to delete
            **kwargs: Additional parameters
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            if not self.session or not self.api_url:
                return False
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "asset": "assets",
                "financial": "financials",
                "property": "properties",
                "tax": "taxes"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
                logger.error(f"Unknown entity type: {entity_type}")
                return False
                
            # Make request
            response = self.session.delete(f"{self.api_url}/{endpoint}/{target_id}")
            
            # Check response
            return response.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Failed to delete {entity_type} record from ERP: {str(e)}")
            return False