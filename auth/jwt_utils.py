"""
TerraFusion Platform - JWT Utilities

This module provides utility functions for JSON Web Token (JWT) operations.
"""
import datetime
import logging
from typing import Dict, Any, List, Optional, Tuple

import jwt
from flask import request, current_app

from auth.config import (
    JWT_SECRET_KEY, JWT_ALGORITHM, JWT_ACCESS_TOKEN_EXPIRES,
    JWT_REFRESH_TOKEN_EXPIRES
)

logger = logging.getLogger(__name__)

def generate_token(
    user_id: int,
    username: str,
    role: str,
    county_ids: List[str],
    token_type: str = 'access',
    expires_in: Optional[int] = None
) -> str:
    """
    Generate a JWT token.
    
    Args:
        user_id: User ID
        username: Username
        role: User role
        county_ids: List of county IDs the user has access to
        token_type: Type of token ('access' or 'refresh')
        expires_in: Token expiration in seconds
        
    Returns:
        JWT token string
    """
    # Set expiration time
    if expires_in is None:
        if token_type == 'access':
            expires_in = JWT_ACCESS_TOKEN_EXPIRES
        else:
            expires_in = JWT_REFRESH_TOKEN_EXPIRES
    
    expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    
    # Create payload
    payload = {
        'sub': user_id,
        'username': username,
        'role': role,
        'county_ids': county_ids,
        'type': token_type,
        'iat': datetime.datetime.utcnow(),
        'exp': expiration
    }
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    # If the token is a byte string, decode it to a normal string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    
    return token

def verify_token(token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Tuple of (is_valid, payload)
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check if the token has expired
        exp = payload.get('exp')
        if exp:
            now = datetime.datetime.utcnow().timestamp()
            if now > exp:
                logger.warning(f"Token expired: {token[:10]}...")
                return False, {"error": "Token expired"}
        
        return True, payload
    
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired: {token[:10]}...")
        return False, {"error": "Token expired"}
    
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {token[:10]}... - {str(e)}")
        return False, {"error": "Invalid token"}
    
    except Exception as e:
        logger.error(f"Error verifying token: {token[:10]}... - {str(e)}")
        return False, {"error": f"Error verifying token: {str(e)}"}

def get_token_from_header() -> Optional[str]:
    """
    Extract the token from the Authorization header.
    
    Returns:
        Token string or None
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    # Check if it's a Bearer token
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        return parts[1]
    
    return None

def refresh_access_token(refresh_token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Refresh an access token using a refresh token.
    
    Args:
        refresh_token: Refresh token string
        
    Returns:
        Tuple of (success, result)
    """
    # Verify the refresh token
    is_valid, payload = verify_token(refresh_token)
    
    if not is_valid:
        return False, payload
    
    # Check if it's a refresh token
    if payload.get('type') != 'refresh':
        logger.warning("Invalid token type for refresh")
        return False, {"error": "Invalid token type"}
    
    # Generate a new access token
    try:
        access_token = generate_token(
            user_id=payload.get('sub'),
            username=payload.get('username'),
            role=payload.get('role'),
            county_ids=payload.get('county_ids', []),
            token_type='access'
        )
        
        return True, {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": JWT_ACCESS_TOKEN_EXPIRES
        }
    
    except Exception as e:
        logger.error(f"Error generating new access token: {str(e)}")
        return False, {"error": f"Error generating new access token: {str(e)}"}

def get_current_user_from_token() -> Optional[Dict[str, Any]]:
    """
    Get the current user from the token in the Authorization header.
    
    Returns:
        User data or None
    """
    token = get_token_from_header()
    
    if not token:
        return None
    
    is_valid, payload = verify_token(token)
    
    if not is_valid:
        return None
    
    # Check if it's an access token
    if payload.get('type') != 'access':
        return None
    
    # Return user data
    return {
        'user_id': payload.get('sub'),
        'username': payload.get('username'),
        'role': payload.get('role'),
        'county_ids': payload.get('county_ids', [])
    }