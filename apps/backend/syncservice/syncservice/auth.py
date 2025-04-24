"""
Authentication module for the TerraFusion SyncService.

This module provides JWT validation and role-based authorization
for the SyncService API, integrating with the County's Azure AD
identity infrastructure.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Union, Callable

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import jwt
    import httpx
except ImportError:
    # Fallbacks when dependencies are not available
    HTTPBearer = lambda *args, **kwargs: None
    HTTPException = type('HTTPException', (Exception,), {})
    status = type('status', (), {'HTTP_401_UNAUTHORIZED': 401, 'HTTP_403_FORBIDDEN': 403})
    Depends = lambda x: x

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure AD configuration
AZURE_AD_TENANT_ID = os.environ.get("AZURE_AD_TENANT_ID", "")
AZURE_AD_CLIENT_ID = os.environ.get("AZURE_AD_CLIENT_ID", "")
AZURE_AD_JWKS_URI = os.environ.get(
    "AZURE_AD_JWKS_URI",
    f"https://login.microsoftonline.com/{AZURE_AD_TENANT_ID}/discovery/v2.0/keys"
)

# Security scheme for JWT bearer tokens
oauth2_scheme = HTTPBearer()

# Cache for JWKS keys
jwks_cache = {}
jwks_last_updated = 0


async def get_jwks():
    """
    Fetch JSON Web Key Set (JWKS) from Azure AD.
    
    Returns:
        dict: The JWKS keys
    """
    global jwks_cache, jwks_last_updated
    
    # Use cached keys if available and not expired
    current_time = int(__import__('time').time())
    if jwks_cache and (current_time - jwks_last_updated) < 3600:  # 1 hour cache
        return jwks_cache
    
    try:
        # Fetch JWKS from Azure AD
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_AD_JWKS_URI)
            response.raise_for_status()
            jwks_cache = response.json()
            jwks_last_updated = current_time
            return jwks_cache
    except Exception as e:
        logger.error(f"Error fetching JWKS: {str(e)}")
        
        # If we have cached keys, use them even if expired
        if jwks_cache:
            logger.warning("Using expired JWKS cache")
            return jwks_cache
        
        # If no cache available, raise the error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to fetch authentication keys"
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Validate the JWT token and extract user information.
    
    Args:
        credentials: The HTTP bearer token credentials
    
    Returns:
        dict: User information from the validated token
    
    Raises:
        HTTPException: If token validation fails
    """
    # Check if we're in development mode with no auth
    if os.environ.get("SYNCSERVICE_DEV_MODE") == "1":
        return {"id": "dev-user", "name": "Development User", "roles": ["admin"]}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    token = credentials.credentials
    
    try:
        # Get the JWKS for token validation
        jwks = await get_jwks()
        
        # Decode and validate the token
        # For production, we'd use the azure-identity package and proper JWKS validation
        # This is a simplified version for demonstration
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # In production, we'd verify against JWKS
                audience=AZURE_AD_CLIENT_ID
            )
        except jwt.JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Check if token is expired
        if "exp" in payload and payload["exp"] < int(__import__('time').time()):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired"
            )
        
        # Extract user information
        user_info = {
            "id": payload.get("oid", ""),
            "name": payload.get("name", ""),
            "email": payload.get("email", payload.get("upn", "")),
            "roles": payload.get("roles", [])
        }
        
        if not user_info["id"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identity in token"
            )
        
        return user_info
        
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )


def has_role(roles: Union[str, List[str]]):
    """
    Dependency for checking if a user has the required role(s).
    
    Args:
        roles: A single role or list of roles that grant access
    
    Returns:
        Callable: A dependency function that checks user roles
    """
    if isinstance(roles, str):
        roles = [roles]
    
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        # Check if user has any of the required roles
        user_roles = user.get("roles", [])
        
        # Always grant access in development mode
        if os.environ.get("SYNCSERVICE_DEV_MODE") == "1":
            return user
            
        # Admin role always has access to everything
        if "admin" in user_roles:
            return user
            
        # Check for specific role match
        for role in roles:
            if role in user_roles:
                return user
                
        # No matching role found
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required role(s): {', '.join(roles)}"
        )
    
    return role_checker