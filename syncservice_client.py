"""
API client for interacting with the SyncService.

This module provides a client for making API calls to the SyncService.
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)

# Default SyncService URL (when running in the local environment)
DEFAULT_URL = "http://localhost:8000"


class SyncServiceClient:
    """
    Client for interacting with the SyncService API.
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize the SyncService client.
        
        Args:
            base_url: Base URL of the SyncService API (defaults to localhost:8000)
            api_key: API key for authentication (defaults to environment variable)
        """
        self.base_url = base_url or os.environ.get("SYNC_SERVICE_URL", DEFAULT_URL)
        self.api_key = api_key or os.environ.get("SYNC_SERVICE_API_KEY", "dev-api-key")
        
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for API requests.
        
        Returns:
            Dictionary of HTTP headers
        """
        return {
            "Content-Type": "application/json",
            "X-API-Key": self.api_key
        }
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make an HTTP request to the SyncService API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Optional request data
            
        Returns:
            Response data as dictionary
            
        Raises:
            RequestException: If the request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self._get_headers(), timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self._get_headers(), json=data, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
                
            response.raise_for_status()
            return response.json()
            
        except RequestException as e:
            logger.error(f"Error making {method} request to {url}: {str(e)}")
            raise
            
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of the SyncService.
        
        Returns:
            Health status information
        """
        try:
            return self._make_request("GET", "/health/status")
        except RequestException:
            # Fall back to basic health check
            try:
                return self._make_request("GET", "/health/live")
            except RequestException as e:
                logger.error(f"Health check failed: {str(e)}")
                return {
                    "status": "DOWN",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
                
    def start_full_sync(self, sync_pair_id: str, entity_types: Optional[List[str]] = None, 
                         params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start a full sync operation.
        
        Args:
            sync_pair_id: ID of the sync pair
            entity_types: Types of entities to sync (defaults to ["property", "owner"])
            params: Additional parameters for the sync
            
        Returns:
            Operation details
        """
        data = {
            "sync_pair_id": sync_pair_id,
            "entity_types": entity_types or ["property", "owner"],
            "params": params or {}
        }
        
        return self._make_request("POST", "/api/sync/full", data)
        
    def start_incremental_sync(self, sync_pair_id: str, hours: int = 24,
                               entity_types: Optional[List[str]] = None,
                               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Start an incremental sync operation.
        
        Args:
            sync_pair_id: ID of the sync pair
            hours: Number of hours to look back for changes
            entity_types: Types of entities to sync (defaults to ["property", "owner"])
            params: Additional parameters for the sync
            
        Returns:
            Operation details
        """
        data = {
            "sync_pair_id": sync_pair_id,
            "hours": hours,
            "entity_types": entity_types or ["property", "owner"],
            "params": params or {}
        }
        
        return self._make_request("POST", "/api/sync/incremental", data)
        
    def get_sync_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get the status of a sync operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Operation status
        """
        return self._make_request("GET", f"/api/sync/status/{operation_id}")
        
    def cancel_sync_operation(self, operation_id: str) -> Dict[str, Any]:
        """
        Cancel a sync operation.
        
        Args:
            operation_id: ID of the operation
            
        Returns:
            Operation status
        """
        return self._make_request("POST", f"/api/sync/cancel/{operation_id}")
        
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get currently active sync operations.
        
        Returns:
            List of active operations
        """
        response = self._make_request("GET", "/api/sync/active")
        # Ensure we return a list even if the API returns an object/dict
        if isinstance(response, dict):
            return [response] if response else []
        return response
        
    def get_sync_metrics(self, sync_pair_id: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """
        Get sync metrics.
        
        Args:
            sync_pair_id: Optional filter by sync pair ID
            days: Number of days to include in metrics
            
        Returns:
            Dictionary of sync metrics
        """
        endpoint = f"/api/sync/metrics?days={days}"
        if sync_pair_id:
            endpoint += f"&sync_pair_id={sync_pair_id}"
            
        return self._make_request("GET", endpoint)
        
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get current system information.
        
        Returns:
            Dictionary of system information
        """
        return self._make_request("GET", "/api/system")
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get current service configuration.
        
        Returns:
            Dictionary of configuration values
        """
        return self._make_request("GET", "/api/config")