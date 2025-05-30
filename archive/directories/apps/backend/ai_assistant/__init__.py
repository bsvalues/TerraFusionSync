"""
TerraFusion SyncService AI Assistant

This module provides AI-powered assistance for sync configuration and guidance.
"""

from .perplexity_client import PerplexityClient

# Convenience instantiation of the default client
try:
    default_client = PerplexityClient()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Could not initialize default Perplexity client: {str(e)}")
    default_client = None