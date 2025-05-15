"""
TerraFusion Platform - JWT Authentication Utilities

This module provides utilities for JWT token generation, validation, and management.
"""
import datetime
import logging
import os
from typing import Dict, Any, Optional, Tuple, Union

import jwt

logger = logging.getLogger(__name__)

# Get secret key from environment or use fallback
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', os.environ.get('FLASK_SECRET_KEY', 'default_jwt_secret_key'))
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(hours=8)  # 8 hours
JWT_REFRESH_TOKEN_EXPIRES = datetime.timedelta(days=7)  # 7 days


def generate_token(user_id: Union[int, str], username: str, role: str, county_ids: Optional[list] = None, 
                   token_type: str = 'access', expires_delta: Optional[datetime.timedelta] = None) -> str:
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
    # Set expiration time
    if expires_delta:
        expires = datetime.datetime.utcnow() + expires_delta
    else:
        # Default expiration based on token type
        if token_type == 'refresh':
            expires = datetime.datetime.utcnow() + JWT_REFRESH_TOKEN_EXPIRES
        else:
            expires = datetime.datetime.utcnow() + JWT_ACCESS_TOKEN_EXPIRES
    
    # Create payload
    payload = {
        'sub': str(user_id),
        'username': username,
        'role': role,
        'type': token_type,
        'exp': expires,
        'iat': datetime.datetime.utcnow(),
        'county_ids': county_ids or []
    }
    
    # Generate token
    try:
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        logger.error(f"Error generating JWT token: {str(e)}")
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
        # Decode and verify token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Check expiration
        if 'exp' in payload:
            expiration = datetime.datetime.fromtimestamp(payload['exp'])
            if expiration < datetime.datetime.utcnow():
                return False, None, "Token has expired"
        
        return True, payload, None
    except jwt.ExpiredSignatureError:
        return False, None, "Token has expired"
    except jwt.InvalidTokenError as e:
        return False, None, f"Invalid token: {str(e)}"
    except Exception as e:
        logger.error(f"Error verifying JWT token: {str(e)}")
        return False, None, f"Error verifying token: {str(e)}"


def refresh_access_token(refresh_token: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Generate a new access token using a refresh token.
    
    Args:
        refresh_token: Refresh token
        
    Returns:
        Tuple of (success, new_access_token, error_message)
    """
    # Verify refresh token
    success, payload, error = verify_token(refresh_token)
    
    if not success:
        return False, None, error
    
    # Check token type
    if payload.get('type') != 'refresh':
        return False, None, "Invalid token type"
    
    # Generate new access token
    try:
        new_token = generate_token(
            user_id=payload['sub'],
            username=payload['username'],
            role=payload['role'],
            county_ids=payload.get('county_ids', []),
            token_type='access'
        )
        
        return True, new_token, None
    except Exception as e:
        logger.error(f"Error refreshing access token: {str(e)}")
        return False, None, f"Error refreshing token: {str(e)}"