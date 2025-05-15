"""
TerraFusion Platform - JWT Token Utilities

This module provides JWT token generation, validation, and management
functions for the TerraFusion Platform authentication system.
"""
import datetime
import logging
import time
from typing import Dict, Any, List, Optional, Set, Union

import jwt

from auth.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES
)

logger = logging.getLogger(__name__)

# In-memory token blacklist for development
# In production, use Redis or a database
TOKEN_BLACKLIST: Set[str] = set()
BLACKLIST_EXPIRY: Dict[str, int] = {}


def clean_expired_blacklist_tokens():
    """
    Remove expired tokens from the blacklist to prevent memory leaks.
    This should be called periodically.
    """
    current_time = int(time.time())
    expired_tokens = [token for token, expiry in BLACKLIST_EXPIRY.items() if expiry < current_time]
    
    for token in expired_tokens:
        TOKEN_BLACKLIST.discard(token)
        BLACKLIST_EXPIRY.pop(token, None)
    
    if expired_tokens:
        logger.info(f"Cleaned {len(expired_tokens)} expired tokens from blacklist")


def create_access_token(
    user_id: Union[str, int],
    username: str,
    role: str,
    permissions: List[str],
    county_ids: Optional[List[str]] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new access token for a user.
    
    Args:
        user_id: User ID (string or integer)
        username: Username for display and logging
        role: User's role (e.g., 'Admin', 'Manager')
        permissions: List of permission strings
        county_ids: List of county IDs the user has access to
        additional_claims: Any additional claims to include in the token
        
    Returns:
        JWT token string
    """
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    
    # Create payload
    payload = {
        'sub': str(user_id),
        'username': username,
        'role': role,
        'permissions': permissions,
        'type': 'access',
        'iat': now,
        'exp': expiry
    }
    
    # Add county IDs if provided
    if county_ids:
        payload['county_ids'] = county_ids
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Create token
    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    return token


def create_refresh_token(
    user_id: Union[str, int],
    username: str,
    role: str,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a new refresh token for a user.
    
    Args:
        user_id: User ID (string or integer)
        username: Username for display and logging
        role: User's role (e.g., 'Admin', 'Manager')
        additional_claims: Any additional claims to include in the token
        
    Returns:
        JWT refresh token string
    """
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES)
    
    # Create payload
    payload = {
        'sub': str(user_id),
        'username': username,
        'role': role,
        'type': 'refresh',
        'iat': now,
        'exp': expiry
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Create token
    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing the token claims
        
    Raises:
        jwt.InvalidTokenError: If the token is invalid or expired
    """
    # Check if token is blacklisted
    if token in TOKEN_BLACKLIST:
        logger.warning("Attempt to use blacklisted token")
        raise jwt.InvalidTokenError("Token is blacklisted")
    
    try:
        # Decode and validate token
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist to revoke it.
    
    Args:
        token: JWT token string
        
    Returns:
        True if the token was blacklisted, False otherwise
    """
    try:
        # Get token expiration time
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Add token to blacklist
        TOKEN_BLACKLIST.add(token)
        
        # Store expiration time to clean up later
        if 'exp' in payload:
            BLACKLIST_EXPIRY[token] = payload['exp']
        
        logger.info(f"Token blacklisted for user {payload.get('username')}")
        return True
    except Exception as e:
        logger.warning(f"Failed to blacklist token: {str(e)}")
        return False


def validate_permissions(token_payload: Dict[str, Any], required_permissions: List[str]) -> bool:
    """
    Check if the token contains the required permissions.
    
    Args:
        token_payload: Decoded token payload
        required_permissions: List of required permission strings
        
    Returns:
        True if the token has all required permissions, False otherwise
    """
    user_permissions = token_payload.get('permissions', [])
    
    # Admin role has implicit access to everything
    if token_payload.get('role') == 'Admin':
        return True
    
    # Check if the user has all required permissions
    return all(perm in user_permissions for perm in required_permissions)


def validate_county_access(token_payload: Dict[str, Any], county_id: str) -> bool:
    """
    Check if the token grants access to a specific county.
    
    Args:
        token_payload: Decoded token payload
        county_id: County ID to check access for
        
    Returns:
        True if the token grants access to the county, False otherwise
    """
    # Get county IDs from token
    county_ids = token_payload.get('county_ids', [])
    
    # Admin role has implicit access to all counties
    if token_payload.get('role') == 'Admin':
        return True
    
    # Wildcard access
    if '*' in county_ids:
        return True
    
    # Check specific access
    return county_id in county_ids