"""
Authentication module for TerraFusion SyncService API Gateway.

This module provides Azure AD authentication integration for the Flask API Gateway.
"""
import os
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable

from flask import request, jsonify, redirect, session, url_for, current_app
import msal
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Azure AD Configuration
AZURE_CLIENT_ID = os.environ.get("AZURE_CLIENT_ID", "")
AZURE_TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")
AZURE_CLIENT_SECRET = os.environ.get("AZURE_CLIENT_SECRET", "")
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"
AZURE_SCOPE = ["https://graph.microsoft.com/.default"]

# Default redirect URI
REDIRECT_URI = os.environ.get("REDIRECT_URI", "http://localhost:5000/auth/callback")

# Create MSAL app
try:
    msal_app = msal.ConfidentialClientApplication(
        AZURE_CLIENT_ID,
        authority=AZURE_AUTHORITY,
        client_credential=AZURE_CLIENT_SECRET
    )
except Exception as e:
    logger.error(f"Error initializing MSAL app: {str(e)}")
    msal_app = None


def build_auth_url() -> str:
    """
    Build the Azure AD authentication URL.
    
    Returns:
        str: The authentication URL for redirecting users
    """
    try:
        if not msal_app:
            logger.error("MSAL app not initialized")
            return ""
            
        return msal_app.get_authorization_request_url(
            AZURE_SCOPE,
            redirect_uri=REDIRECT_URI,
            state={"next": request.args.get("next", "/")}
        )
    except Exception as e:
        logger.error(f"Error building auth URL: {str(e)}")
        return ""


def get_token_from_code(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token.
    
    Args:
        code: The authorization code from Azure AD
        
    Returns:
        Dictionary containing the access token and other info
    """
    try:
        if not msal_app:
            logger.error("MSAL app not initialized")
            return {}
            
        return msal_app.acquire_token_by_authorization_code(
            code,
            scopes=AZURE_SCOPE,
            redirect_uri=REDIRECT_URI
        )
    except Exception as e:
        logger.error(f"Error getting token from code: {str(e)}")
        return {}


def get_token_from_cache(user_id: str) -> Dict[str, Any]:
    """
    Get access token from cache.
    
    Args:
        user_id: The user ID to look up in the cache
        
    Returns:
        Dictionary containing the access token and other info
    """
    try:
        if not msal_app:
            logger.error("MSAL app not initialized")
            return {}
            
        accounts = msal_app.get_accounts(username=user_id)
        if accounts:
            result = msal_app.acquire_token_silent(
                AZURE_SCOPE,
                account=accounts[0]
            )
            return result if result else {}
        return {}
    except Exception as e:
        logger.error(f"Error getting token from cache: {str(e)}")
        return {}


def validate_token(token: str) -> Dict[str, Any]:
    """
    Validate an access token with Microsoft Graph API.
    
    Args:
        token: The access token to validate
        
    Returns:
        Dictionary containing the user information if valid
    """
    try:
        graph_url = "https://graph.microsoft.com/v1.0/me"
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(graph_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        
        logger.error(f"Token validation failed: {response.status_code} - {response.text}")
        return {}
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        return {}


def requires_auth(f: Callable) -> Callable:
    """
    Decorator for routes that require authentication.
    
    Args:
        f: The function to wrap
        
    Returns:
        Wrapped function that checks for authentication
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # Check if user is authenticated
        if "user" not in session:
            # Store the current URL for redirect after auth
            next_url = request.url
            # Redirect to login
            auth_url = build_auth_url()
            if auth_url:
                return redirect(auth_url)
            else:
                return jsonify({
                    "error": "Authentication service unavailable",
                    "message": "Unable to build authentication URL"
                }), 503
        
        # User is authenticated, proceed
        return f(*args, **kwargs)
    
    return decorated


def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Get the current authenticated user.
    
    Returns:
        Dictionary containing user information or None if not authenticated
    """
    if "user" in session:
        return session["user"]
    return None


def logout_user() -> None:
    """
    Log out the current user by clearing the session.
    """
    session.clear()


# Initialize login routes
def init_auth_routes(app):
    """
    Initialize authentication routes for the Flask app.
    
    Args:
        app: The Flask application instance
    """
    @app.route("/auth/login")
    def login():
        """Login route that redirects to Azure AD."""
        # Build the auth URL and redirect
        auth_url = build_auth_url()
        if auth_url:
            return redirect(auth_url)
        else:
            return jsonify({
                "error": "Authentication service unavailable",
                "message": "Unable to build authentication URL"
            }), 503
    
    @app.route("/auth/callback")
    def auth_callback():
        """Callback route that Azure AD redirects to after login."""
        # Exchange code for token
        code = request.args.get("code")
        if not code:
            return jsonify({
                "error": "Authentication failed",
                "message": "No authorization code provided"
            }), 400
        
        # Get token from code
        result = get_token_from_code(code)
        if "error" in result:
            return jsonify({
                "error": "Authentication failed",
                "message": result.get("error_description", "Failed to acquire token")
            }), 401
        
        # Validate token and get user info
        token = result.get("access_token", "")
        user_info = validate_token(token)
        if not user_info:
            return jsonify({
                "error": "Authentication failed",
                "message": "Failed to validate token"
            }), 401
        
        # Store user info and token in session
        session["user"] = user_info
        session["token"] = token
        
        # Redirect to original destination
        next_url = request.args.get("state", {}).get("next", "/")
        return redirect(next_url)
    
    @app.route("/auth/logout")
    def logout():
        """Logout route that clears the session."""
        logout_user()
        return redirect("/")
    
    @app.route("/auth/status")
    def auth_status():
        """Status route that returns the current auth status."""
        user = get_current_user()
        return jsonify({
            "authenticated": user is not None,
            "user": user
        })