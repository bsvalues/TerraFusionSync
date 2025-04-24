"""
GIS system adapter for the SyncService.

This module provides a concrete implementation of the source system adapter
interface for GIS (Geographic Information System) data.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from syncservice.interfaces.system_adapter import SourceSystemAdapter

logger = logging.getLogger(__name__)


class GISAdapter(SourceSystemAdapter):
    """
    Source system adapter for GIS (Geographic Information System).
    
    This adapter provides connectivity and data access methods for GIS systems,
    which store spatial information and geographic data.
    """
    
    def __init__(self, connection_params: Dict[str, Any]):
        """
        Initialize the GIS adapter with connection parameters.
        
        Args:
            connection_params: Dictionary containing connection parameters for the GIS system
        """
        super().__init__(connection_params)
        self.api_url = connection_params.get('api_url')
        self.api_key = connection_params.get('api_key')
        self.session = None
    
    async def connect(self) -> bool:
        """
        Establish a connection to the GIS system.
        
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
                'Accept': 'application/json'
            })
            
            # Test connection
            return await self.check_connection()
        except Exception as e:
            logger.error(f"Failed to connect to GIS: {str(e)}")
            return False
        
    async def disconnect(self) -> bool:
        """
        Close the connection to the GIS system.
        
        Returns:
            True if disconnection was successful, False otherwise
        """
        try:
            if self.session:
                self.session.close()
                self.session = None
            return True
        except Exception as e:
            logger.error(f"Failed to disconnect from GIS: {str(e)}")
            return False
    
    async def check_connection(self) -> bool:
        """
        Check if the connection to the GIS system is active.
        
        Returns:
            True if connection is active, False otherwise
        """
        try:
            if not self.session or not self.api_url:
                return False
                
            # Make a test request to the GIS API
            response = self.session.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to check GIS connection: {str(e)}")
            return False
    
    def get_system_type(self) -> str:
        """
        Get the type of system this adapter connects to.
        
        Returns:
            String identifier for the system type
        """
        return "gis"
    
    async def get_all_records(
        self, 
        entity_type: str,
        batch_size: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Get all records of a specific entity type from the GIS system.
        
        Args:
            entity_type: Type of entity to retrieve (e.g., "parcel", "zoning")
            batch_size: Number of records to retrieve in each batch
            **kwargs: Additional filters or parameters
            
        Returns:
            List of records from the GIS system
        """
        try:
            if not self.session or not self.api_url:
                return []
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "parcel": "parcels",
                "zoning": "zoning",
                "district": "districts",
                "boundary": "boundaries"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            # Build query parameters
            params = {
                'limit': batch_size,
                'offset': kwargs.get('offset', 0)
            }
            
            # Add filters
            if kwargs.get('filters'):
                for field, value in kwargs.get('filters').items():
                    params[field] = value
            
            # Make request
            response = self.session.get(f"{self.api_url}/{endpoint}", params=params)
            
            # Check response
            if response.status_code != 200:
                logger.error(f"Failed to get {entity_type} records from GIS: {response.text}")
                return []
                
            # Parse response
            data = response.json()
            return data.get('features', [])
        except Exception as e:
            logger.error(f"Failed to get {entity_type} records from GIS: {str(e)}")
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
            entity_type: Type of entity to retrieve (e.g., "parcel", "zoning")
            since: Timestamp to filter changes by
            batch_size: Number of records to retrieve in each batch
            **kwargs: Additional filters or parameters
            
        Returns:
            List of changed records from the GIS system
        """
        try:
            if not self.session or not self.api_url:
                return []
                
            # Map entity types to API endpoints
            endpoint_mapping = {
                "parcel": "parcels",
                "zoning": "zoning",
                "district": "districts",
                "boundary": "boundaries"
            }
            
            endpoint = endpoint_mapping.get(entity_type.lower())
            if not endpoint:
                logger.error(f"Unknown entity type: {entity_type}")
                return []
            
            # Format timestamp for API
            since_str = since.isoformat()
            
            # Build query parameters
            params = {
                'limit': batch_size,
                'offset': kwargs.get('offset', 0),
                'last_modified': f"gt:{since_str}"
            }
            
            # Add filters
            if kwargs.get('filters'):
                for field, value in kwargs.get('filters').items():
                    params[field] = value
            
            # Make request
            response = self.session.get(f"{self.api_url}/{endpoint}", params=params)
            
            # Check response
            if response.status_code != 200:
                logger.error(f"Failed to get changed {entity_type} records from GIS: {response.text}")
                return []
                
            # Parse response
            data = response.json()
            return data.get('features', [])
        except Exception as e:
            logger.error(f"Failed to get changed {entity_type} records from GIS: {str(e)}")
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
            entity_type: Type of related entity to retrieve (e.g., "zoning" for parcels)
            related_ids: List of IDs to find related records for
            **kwargs: Additional filters or parameters
            
        Returns:
            List of related records from the GIS system
        """
        try:
            if not self.session or not self.api_url or not related_ids:
                return []
                
            # Map entity types and relations to API endpoints
            relation_mapping = {
                "parcel": {
                    "zoning": "parcels/{id}/zoning",
                    "district": "parcels/{id}/districts",
                    "boundary": "parcels/{id}/boundaries"
                },
                "zoning": {
                    "parcel": "zoning/{id}/parcels"
                },
                "district": {
                    "parcel": "districts/{id}/parcels",
                    "boundary": "districts/{id}/boundaries"
                }
            }
            
            # Get relation information for the requested entity type
            from_type = kwargs.get('from_type', 'parcel')
            relation_info = relation_mapping.get(from_type, {}).get(entity_type.lower())
            
            if not relation_info:
                logger.error(f"Unknown relation: {from_type} -> {entity_type}")
                return []
            
            results = []
            
            # Fetch related records for each ID
            for id in related_ids:
                # Format endpoint with ID
                endpoint = relation_info.replace('{id}', id)
                
                # Make request
                response = self.session.get(f"{self.api_url}/{endpoint}")
                
                # Check response
                if response.status_code != 200:
                    logger.error(f"Failed to get related {entity_type} records from GIS: {response.text}")
                    continue
                    
                # Parse response
                data = response.json()
                results.extend(data.get('features', []))
            
            return results
        except Exception as e:
            logger.error(f"Failed to get related {entity_type} records from GIS: {str(e)}")
            return []