"""
Integration module for SyncService with the API Gateway.

This module provides a simple API client for the API Gateway to interact with the
SyncService, bridging the gap between the different service components.
"""

import logging
import json
import requests
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Default URL for SyncService
DEFAULT_SYNCSERVICE_URL = "http://0.0.0.0:8080"


class SyncServiceClient:
    """Client for interacting with the SyncService from the API Gateway."""
    
    def __init__(self, base_url: str = None, timeout: int = 10):
        """
        Initialize the SyncService client.
        
        Args:
            base_url: Base URL for SyncService API
            timeout: Default timeout for API calls in seconds
        """
        self.base_url = base_url or DEFAULT_SYNCSERVICE_URL
        self.timeout = timeout
        logger.info(f"SyncServiceClient initialized with base URL: {self.base_url}")
    
    def get_health(self) -> Dict[str, Any]:
        """
        Get the health status of the SyncService.
        
        Returns:
            Dictionary with health information
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting SyncService health: {str(e)}")
            raise
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from the SyncService.
        
        Returns:
            Dictionary with metrics information
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/metrics",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting SyncService metrics: {str(e)}")
            raise
    
    def create_sync_pair(self, sync_pair_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new sync pair.
        
        Args:
            sync_pair_data: Dictionary with sync pair configuration
            
        Returns:
            Dictionary with the created sync pair
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/sync-pairs",
                json=sync_pair_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error creating sync pair: {str(e)}")
            raise
    
    def get_sync_pairs(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get sync pairs with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            filters: Dictionary with filter parameters
            
        Returns:
            Dictionary with paginated sync pairs
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if filters:
                params.update(filters)
                
            response = requests.get(
                f"{self.base_url}/api/v1/sync-pairs",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting sync pairs: {str(e)}")
            raise
    
    def get_sync_pair(self, sync_pair_id: int) -> Dict[str, Any]:
        """
        Get a specific sync pair by ID.
        
        Args:
            sync_pair_id: ID of the sync pair
            
        Returns:
            Dictionary with sync pair details
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/sync-pairs/{sync_pair_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting sync pair {sync_pair_id}: {str(e)}")
            raise
    
    def update_sync_pair(
        self,
        sync_pair_id: int,
        sync_pair_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update a sync pair.
        
        Args:
            sync_pair_id: ID of the sync pair to update
            sync_pair_data: Dictionary with updated sync pair configuration
            
        Returns:
            Dictionary with the updated sync pair
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.put(
                f"{self.base_url}/api/v1/sync-pairs/{sync_pair_id}",
                json=sync_pair_data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error updating sync pair {sync_pair_id}: {str(e)}")
            raise
    
    def delete_sync_pair(self, sync_pair_id: int) -> Dict[str, Any]:
        """
        Delete a sync pair.
        
        Args:
            sync_pair_id: ID of the sync pair to delete
            
        Returns:
            Dictionary with deletion result
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/sync-pairs/{sync_pair_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error deleting sync pair {sync_pair_id}: {str(e)}")
            raise
    
    def create_sync_operation(
        self,
        sync_pair_id: int,
        operation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new sync operation.
        
        Args:
            sync_pair_id: ID of the sync pair to use
            operation_data: Dictionary with operation configuration
            
        Returns:
            Dictionary with the created operation
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            data = {
                "sync_pair_id": sync_pair_id,
                **operation_data
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/sync-operations",
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error creating sync operation: {str(e)}")
            raise
    
    def get_sync_operations(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get sync operations with pagination and filtering.
        
        Args:
            page: Page number (1-based)
            per_page: Number of items per page
            filters: Dictionary with filter parameters
            
        Returns:
            Dictionary with paginated sync operations
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            params = {
                "page": page,
                "per_page": per_page
            }
            
            if filters:
                params.update(filters)
                
            response = requests.get(
                f"{self.base_url}/api/v1/sync-operations",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting sync operations: {str(e)}")
            raise
    
    def get_sync_operation(self, operation_id: int) -> Dict[str, Any]:
        """
        Get a specific sync operation by ID.
        
        Args:
            operation_id: ID of the sync operation
            
        Returns:
            Dictionary with operation details
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/sync-operations/{operation_id}",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting sync operation {operation_id}: {str(e)}")
            raise
    
    def execute_sync_operation(self, operation_id: int) -> Dict[str, Any]:
        """
        Execute a sync operation.
        
        Args:
            operation_id: ID of the sync operation to execute
            
        Returns:
            Dictionary with execution result
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/sync-operations/{operation_id}/execute",
                timeout=self.timeout * 3  # Longer timeout for execution
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error executing sync operation {operation_id}: {str(e)}")
            raise
    
    def cancel_sync_operation(self, operation_id: int) -> Dict[str, Any]:
        """
        Cancel a running sync operation.
        
        Args:
            operation_id: ID of the sync operation to cancel
            
        Returns:
            Dictionary with cancellation result
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/sync-operations/{operation_id}/cancel",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error cancelling sync operation {operation_id}: {str(e)}")
            raise
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get detailed health status of the entire system.
        
        Returns:
            Dictionary with system health information
            
        Raises:
            requests.RequestException: If the request fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/system/health",
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error getting system health: {str(e)}")
            raise


# Create a singleton instance for use throughout the application
sync_service = SyncServiceClient()


def is_syncservice_available() -> bool:
    """
    Check if the SyncService is available.
    
    Returns:
        True if available, False otherwise
    """
    try:
        sync_service.get_health()
        return True
    except Exception:
        return False


def wait_for_syncservice(
    max_retries: int = 5,
    retry_delay: int = 2,
    timeout: int = 5
) -> bool:
    """
    Wait for SyncService to become available.
    
    Args:
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        timeout: Timeout for each health check in seconds
        
    Returns:
        True if SyncService becomes available, False otherwise
    """
    client = SyncServiceClient(timeout=timeout)
    
    for attempt in range(1, max_retries + 1):
        try:
            client.get_health()
            logger.info(f"SyncService is available (attempt {attempt}/{max_retries})")
            return True
        except Exception as e:
            logger.warning(f"SyncService not available (attempt {attempt}/{max_retries}): {str(e)}")
            
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    return False