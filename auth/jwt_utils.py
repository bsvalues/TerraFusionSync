"""
TerraFusion Platform - JWT Token Utilities

This module provides JWT token generation, validation, and management
functions for the TerraFusion Platform authentication system.
"""

import uuid
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta

import jwt
from jwt.exceptions import (
    InvalidTokenError, ExpiredSignatureError, 
    InvalidSignatureError, DecodeError
)

from auth.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES, JWT_REFRESH_TOKEN_EXPIRES
)

# Configure logging
logger = logging.getLogger(__name__)

# In-memory token blacklist (could be replaced with Redis in production)
# Format: {token_jti: expiration_datetime}
TOKEN_BLACKLIST = {}


def clean_expired_blacklist_tokens():
    """
    Remove expired tokens from the blacklist to prevent memory leaks.
    This should be called periodically.
    """
    now = datetime.utcnow()
    expired_tokens = [jti for jti, exp in TOKEN_BLACKLIST.items() if exp < now]
    for jti in expired_tokens:
        TOKEN_BLACKLIST.pop(jti, None)
    
    if expired_tokens:
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
    token_jti = str(uuid.uuid4())
    
    # Create the token payload
    payload = {
        'sub': str(user_id),  # Subject (user ID)
        'jti': token_jti,     # JWT ID (unique identifier for this token)
        'iat': now,           # Issued at time
        'exp': now + JWT_ACCESS_TOKEN_EXPIRES,  # Expiration time
        'type': 'access',     # Token type
        'username': username,
        'role': role,
        'permissions': permissions,
    }
    
    # Add county IDs if provided
    if county_ids:
        payload['county_ids'] = county_ids
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Generate and return the token
    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    logger.debug(f"Created access token for user {username} with JTI {token_jti}")
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
    now = datetime.utcnow()
    token_jti = str(uuid.uuid4())
    
    # Create the token payload
    payload = {
        'sub': str(user_id),  # Subject (user ID)
        'jti': token_jti,     # JWT ID (unique identifier for this token)
        'iat': now,           # Issued at time
        'exp': now + JWT_REFRESH_TOKEN_EXPIRES,  # Expiration time
        'type': 'refresh',    # Token type
        'username': username,
        'role': role,
    }
    
    # Add any additional claims
    if additional_claims:
        payload.update(additional_claims)
    
    # Generate and return the token
    token = jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )
    
    logger.debug(f"Created refresh token for user {username} with JTI {token_jti}")
    return token


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dictionary containing the token claims
        
    Raises:
        InvalidTokenError: If the token is invalid or expired
    """
    try:
        # Decode the token
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Check if token is in blacklist
        token_jti = payload.get('jti')
        if token_jti in TOKEN_BLACKLIST:
            logger.warning(f"Attempt to use blacklisted token with JTI {token_jti}")
            raise InvalidTokenError("Token has been revoked")
        
        return payload
    
    except ExpiredSignatureError:
        logger.info("Token validation failed: expired signature")
        raise InvalidTokenError("Token has expired")
    
    except InvalidSignatureError:
        logger.warning("Token validation failed: invalid signature")
        raise InvalidTokenError("Invalid token signature")
    
    except DecodeError:
        logger.warning("Token validation failed: decode error")
        raise InvalidTokenError("Token cannot be decoded")
    
    except Exception as e:
        logger.error(f"Token validation failed with unexpected error: {str(e)}")
        raise InvalidTokenError(f"Token validation failed: {str(e)}")


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist to revoke it.
    
    Args:
        token: JWT token string
        
    Returns:
        True if the token was blacklisted, False otherwise
    """
    try:
        # Decode the token without verification to extract jti and exp
        payload = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        
        token_jti = payload.get('jti')
        token_exp = payload.get('exp')
        
        if not token_jti or not token_exp:
            logger.warning("Cannot blacklist token: missing jti or exp claim")
            return False
        
        # Convert exp (Unix timestamp) to datetime
        exp_datetime = datetime.fromtimestamp(token_exp)
        
        # Add to blacklist with expiration time
        TOKEN_BLACKLIST[token_jti] = exp_datetime
        
        logger.info(f"Token with JTI {token_jti} added to blacklist")
        
        # Clean expired tokens occasionally
        if len(TOKEN_BLACKLIST) % 10 == 0:  # Every 10 blacklist operations
            clean_expired_blacklist_tokens()
        
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
    # Extract permissions from token
    token_permissions = token_payload.get('permissions', [])
    
    # Check for admin with wildcard permission
    if '*' in token_permissions:
        return True
    
    # Check if all required permissions are present
    return all(perm in token_permissions for perm in required_permissions)


def validate_county_access(token_payload: Dict[str, Any], county_id: str) -> bool:
    """
    Check if the token grants access to a specific county.
    
    Args:
        token_payload: Decoded token payload
        county_id: County ID to check access for
        
    Returns:
        True if the token grants access to the county, False otherwise
    """
    # Extract county IDs from token
    token_county_ids = token_payload.get('county_ids', [])
    
    # Check for admin with access to all counties
    if '*' in token_county_ids:
        return True
    
    # Check if the requested county is in the allowed list
    return county_id in token_county_ids