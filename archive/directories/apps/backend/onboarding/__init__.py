"""
Onboarding Module

This module provides the onboarding experience for new users.
"""

from flask import Blueprint

# Create blueprint
onboarding_bp = Blueprint('onboarding_bp', __name__, 
                        url_prefix='/onboarding',
                        template_folder='../../templates/onboarding')

# Import routes
from . import routes  # noqa