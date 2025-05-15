"""
TerraFusion Platform - Authentication Module

This package provides authentication services for the TerraFusion Platform.
"""
from flask import Blueprint

# Create the authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Import routes to register them with the blueprint
from auth import routes