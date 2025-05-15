"""
TerraFusion Platform - JWT Token Utilities

This module provides JWT token generation, validation, and management
functions for the TerraFusion Platform authentication system.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union, Set

import jwt

from auth.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES
)

# Configure logging
logger = logging.getLogger(__name__)

# In-memory token blacklist (replace with database in production)
_token_blacklist: Set[str] = set()
_blacklist_expiry: Dict[str, float] = {}

def clean_expired_blacklist_tokens():
    """
    Remove expired tokens from the blacklist to prevent memory leaks.
    This should be called periodically.
    """
    global _token_blacklist, _blacklist_expiry
    
    current_time = time.time()
    expired_tokens = [
        token for token, expiry in _blacklist_expiry.items()
        if expiry < current_time
    ]
    
    for token in expired_tokens:
        if token in _token_blacklist:
            _token_blacklist.remove(token)
        if token in _blacklist_expiry:
            del _blacklist_expiry[token]
    
    logger.debug(f"Cleaned {len(expired_tokens)} expired tokens from blacklist")


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
    now = datetime.utcnow()
    expires = now + JWT_ACCESS_TOKEN_EXPIRES
    
    # Base claims
    claims = {
        'iat': now,
        'exp': expires,
        'sub': str(user_id),
        'username': username,
        'role': role,
        'permissions': permissions,
        'type': 'access'
    }
    
    # Add county IDs if provided
    if county_ids:
        claims['county_ids'] = county_ids
    
    # Add additional claims if provided
    if additional_claims:
        claims.update(additional_claims)
    
    # Generate and return the token
    try:
        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.debug(f"Created access token for user {username} (role: {role})")
        return token
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise


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
    now = datetime.utcnow()
    expires = now + JWT_REFRESH_TOKEN_EXPIRES
    
    # Base claims
    claims = {
        'iat': now,
        'exp': expires,
        'sub': str(user_id),
        'username': username,
        'role': role,
        'type': 'refresh'
    }
    
    # Add additional claims if provided
    if additional_claims:
        claims.update(additional_claims)
    
    # Generate and return the token
    try:
        token = jwt.encode(claims, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.debug(f"Created refresh token for user {username}")
        return token
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        raise


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
    try:
        # Check if token is blacklisted
        if token in _token_blacklist:
            logger.warning("Attempt to use blacklisted token")
            raise jwt.InvalidTokenError("Token has been revoked")
        
        # Decode the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("Expired token detected")
        raise
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise
    
    except Exception as e:
        logger.error(f"Error decoding token: {str(e)}")
        raise jwt.InvalidTokenError(f"Error decoding token: {str(e)}")


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist to revoke it.
    
    Args:
        token: JWT token string
        
    Returns:
        True if the token was blacklisted, False otherwise
    """
    try:
        # Decode without verification to get the expiry
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Add to blacklist
        _token_blacklist.add(token)
        
        # Store the expiry time for cleanup
        if 'exp' in payload:
            _blacklist_expiry[token] = payload['exp']
        else:
            # If no expiry, store for 24 hours
            _blacklist_expiry[token] = time.time() + 86400
        
        logger.info(f"Token for user {payload.get('username', 'unknown')} blacklisted")
        return True
    
    except Exception as e:
        logger.error(f"Failed to blacklist token: {str(e)}")
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
    # Get user permissions from token
    user_permissions = token_payload.get('permissions', [])
    
    # Admin with wildcard permission has access to everything
    if '*' in user_permissions:
        return True
    
    # Check if user has all required permissions
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
    # Get counties user has access to from token
    user_counties = token_payload.get('county_ids', [])
    
    # Wildcard for all counties
    if '*' in user_counties:
        return True
    
    # Check if user has access to the specific county
    return county_id in user_counties