"""
Authentication module for the SyncService API.

This module provides functions for authenticating API requests.
"""

import os
import logging
from fastapi import HTTPException, Depends
from fastapi.security import APIKeyHeader

# Logger
logger = logging.getLogger("syncservice.auth")

# Get API key from environment
API_KEY = os.environ.get("SYNC_SERVICE_API_KEY", "dev-api-key")

# Create API key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    Verify API key for protected endpoints.
    
    Args:
        api_key: API key from header
    
    Returns:
        True if key is valid
    
    Raises:
        HTTPException: If key is invalid
    """
    if api_key != API_KEY:
        logger.warning(f"Invalid API key used: {api_key[:5]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    return True