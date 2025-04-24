"""
Authentication module for TerraFusion SyncService.

This module provides Azure AD authentication integration for the FastAPI SyncService.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Union

try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import OAuth2AuthorizationCodeBearer
    from jose import jwt, JWTError
    import httpx
except ImportError:
    # Provide fallbacks for when FastAPI and related packages are not installed
    class HTTPException(Exception):
        def __init__(self, status_code, detail):
            self.status_code = status_code
            self.detail = detail
    
    class OAuth2AuthorizationCodeBearer:
        def __init__(self, *args, **kwargs):
            pass
    
    Depends = lambda x: x
    status = type('status', (), {'HTTP_401_UNAUTHORIZED': 401, 'HTTP_403_FORBIDDEN': 403})
    jwt = None
    httpx = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure AD Configuration
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_JWKS_URI = f"{AZURE_AUTHORITY}/discovery/v2.0/keys"
AZURE_ISSUER = f"{AZURE_AUTHORITY}/v2.0"
AZURE_AUDIENCE = AZURE_CLIENT_ID

# Create OAuth2 scheme
oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{AZURE_AUTHORITY}/oauth2/v2.0/authorize",
    tokenUrl=f"{AZURE_AUTHORITY}/oauth2/v2.0/token",
    scopes={"https://graph.microsoft.com/.default": "Default scope"}
)


async def get_jwks() -> Dict[str, Any]:
    """
    Fetch the JSON Web Key Set (JWKS) from Azure AD.
    
    Returns:
        Dictionary containing the JWKS
    """
    try:
        if not httpx:
            logger.error("httpx not available")
            return {}
            
        async with httpx.AsyncClient() as client:
            response = await client.get(AZURE_JWKS_URI)
            return response.json()
    except Exception as e:
        logger.error(f"Error fetching JWKS: {str(e)}")
        return {}


async def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify the JWT token from Azure AD.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        Dictionary containing the token claims if valid
        
    Raises:
        HTTPException: If the token is invalid
    """
    try:
        if not jwt:
            logger.error("jwt library not available")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="JWT library not available"
            )
            
        # Get the JWKS
        jwks = await get_jwks()
        if not jwks:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Failed to fetch JWKS"
            )
        
        # Decode the token with the JWKS
        try:
            # In a real implementation, you would select the key from JWKS
            # that matches the token's kid (key ID) and use it to verify
            # For simplicity, we're just verifying signature and claims
            payload = jwt.decode(
                token,
                key=jwks,
                algorithms=["RS256"],
                audience=AZURE_AUDIENCE,
                issuer=AZURE_ISSUER
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Error verifying token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error verifying token"
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user from the token.
    
    Args:
        token: The JWT token from the request
        
    Returns:
        Dictionary containing the user information
        
    Raises:
        HTTPException: If the token is invalid
    """
    try:
        payload = await verify_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        # Return user information from token
        return {
            "id": user_id,
            "name": payload.get("name", ""),
            "email": payload.get("preferred_username", ""),
            "roles": payload.get("roles", [])
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error retrieving user information"
        )


def has_role(roles: Union[str, List[str]]) -> Any:
    """
    Dependency to check if the current user has required roles.
    
    Args:
        roles: String or list of role names required
        
    Returns:
        Dependency function for FastAPI
    """
    if isinstance(roles, str):
        roles = [roles]
    
    async def _check_roles(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_roles = user.get("roles", [])
        
        # Check if the user has any of the required roles
        if not any(role in user_roles for role in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User does not have the required roles: {', '.join(roles)}"
            )
        
        return user
    
    return _check_roles