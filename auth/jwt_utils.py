"""
TerraFusion Platform - JWT Authentication Utilities

This module provides utilities for JWT token generation, validation, and management.
"""
import datetime
import logging
from typing import Dict, Any, Tuple, Optional, List, Union

import jwt

from auth.config import (
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES
)

logger = logging.getLogger(__name__)

def generate_token(
    user_id: Union[int, str], 
    username: str, 
    role: str, 
    county_ids: Optional[List[str]] = None, 
    token_type: str = 'access', 
    expires_delta: Optional[datetime.timedelta] = None
) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
        county_ids: List of county IDs the user has access to
        token_type: Type of token ('access' or 'refresh')
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    if county_ids is None:
        county_ids = []
    
    # Set the payload
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "county_ids": county_ids,
        "type": token_type,
        "iat": datetime.datetime.utcnow()
    }
    
    # Set token expiration based on type
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        if token_type == 'refresh':
            expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_REFRESH_TOKEN_EXPIRES)
        else:  # 'access' token by default
            expire = datetime.datetime.utcnow() + datetime.timedelta(seconds=JWT_ACCESS_TOKEN_EXPIRES)
    
    payload["exp"] = expire
    
    # Generate and return the token
    try:
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        logger.debug(f"Generated {token_type} token for user {username} (ID: {user_id})")
        return token
    except Exception as e:
        logger.error(f"Error generating {token_type} token: {str(e)}")
        raise

def verify_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Verify a JWT token and return the payload if valid.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Tuple of (success, payload, error_message)
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        logger.debug(f"Successfully verified token for user {payload.get('username')}")
        return True, payload, None
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return False, None, "Token expired"
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        return False, None, "Invalid token"
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        return False, None, f"Error verifying token: {str(e)}"

def refresh_access_token(refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        Tuple of (success, new_access_token, error_message)
    """
    # Verify the refresh token
    success, payload, error = verify_token(refresh_token)
    
    if not success:
        return False, None, error
    
    # Check if it's actually a refresh token
    if payload.get("type") != "refresh":
        logger.warning("Attempted to use an access token as a refresh token")
        return False, None, "Invalid refresh token"
    
    try:
        # Generate a new access token with the same claims
        new_token = generate_token(
            user_id=payload.get("sub"),
            username=payload.get("username"),
            role=payload.get("role"),
            county_ids=payload.get("county_ids", []),
            token_type="access"
        )
        logger.info(f"Generated new access token for user {payload.get('username')}")
        return True, new_token, None
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return False, None, f"Error refreshing token: {str(e)}"

def get_token_from_header(auth_header: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Extract token from Authorization header.
    
    Args:
        auth_header: The Authorization header value
        
    Returns:
        Tuple of (success, token, error_message)
    """
    if not auth_header:
        return False, None, "Authorization header missing"
    
    parts = auth_header.split()
    
    # Check if the Authorization header has the correct format
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False, None, "Authorization header must be 'Bearer <token>'"
    
    token = parts[1]
    return True, token, None

def get_token_identity(token: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Get the identity information from a token.
    
    Args:
        token: JWT token
        
    Returns:
        Tuple of (success, identity_dict, error_message)
    """
    success, payload, error = verify_token(token)
    
    if not success:
        return False, None, error
    
    # Extract identity fields
    identity = {
        "user_id": payload.get("sub"),
        "username": payload.get("username"),
        "role": payload.get("role"),
        "county_ids": payload.get("county_ids", [])
    }
    
    return True, identity, None