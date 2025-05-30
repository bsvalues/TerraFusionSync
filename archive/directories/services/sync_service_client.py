"""
TerraFusion API Gateway - Sync Service Client

This module provides a client for making API calls to the TerraFusion SyncService.
"""

import logging
import requests
import os
from typing import Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class SyncServiceClient:
    """Client for making requests to the TerraFusion SyncService."""
    
    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize the SyncService client.
        
        Args:
            base_url: Base URL for the SyncService. Defaults to environment variable or localhost:8080.
            timeout: Request timeout in seconds.
        """
        self.base_url = base_url or os.environ.get("SYNC_SERVICE_URL", "http://0.0.0.0:8080")
        self.timeout = timeout
        logger.info(f"SyncServiceClient initialized with base URL: {self.base_url}")
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Make a GET request to the SyncService.
        
        Args:
            path: API path to request (without base URL)
            params: Optional query parameters
            
        Returns:
            Tuple of (response_json, status_code)
        
        Raises:
            Exception if the request fails
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"Making GET request to {url}")
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"text": response.text}
            
            logger.debug(f"Response from {url}: status={response.status_code}")
            return response_data, response.status_code
            
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}", exc_info=True)
            raise
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Make a POST request to the SyncService.
        
        Args:
            path: API path to request (without base URL)
            data: Optional JSON body data
            params: Optional query parameters
            
        Returns:
            Tuple of (response_json, status_code)
        
        Raises:
            Exception if the request fails
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"Making POST request to {url}")
        
        try:
            response = requests.post(url, json=data, params=params, timeout=self.timeout)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"text": response.text}
            
            logger.debug(f"Response from {url}: status={response.status_code}")
            return response_data, response.status_code
            
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}", exc_info=True)
            raise
    
    def put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Make a PUT request to the SyncService.
        
        Args:
            path: API path to request (without base URL)
            data: Optional JSON body data
            
        Returns:
            Tuple of (response_json, status_code)
        
        Raises:
            Exception if the request fails
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"Making PUT request to {url}")
        
        try:
            response = requests.put(url, json=data, timeout=self.timeout)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"text": response.text}
            
            logger.debug(f"Response from {url}: status={response.status_code}")
            return response_data, response.status_code
            
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}", exc_info=True)
            raise
    
    def delete(self, path: str) -> Tuple[Dict[str, Any], int]:
        """
        Make a DELETE request to the SyncService.
        
        Args:
            path: API path to request (without base URL)
            
        Returns:
            Tuple of (response_json, status_code)
        
        Raises:
            Exception if the request fails
        """
        url = f"{self.base_url}{path}"
        logger.debug(f"Making DELETE request to {url}")
        
        try:
            response = requests.delete(url, timeout=self.timeout)
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except ValueError:
                response_data = {"text": response.text}
            
            logger.debug(f"Response from {url}: status={response.status_code}")
            return response_data, response.status_code
            
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed: {e}", exc_info=True)
            raise