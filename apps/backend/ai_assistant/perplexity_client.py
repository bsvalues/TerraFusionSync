"""
TerraFusion SyncService AI Assistant - Perplexity API Client

This module provides a client for interacting with the Perplexity API
to power the contextual AI assistant for sync configuration guidance.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

class PerplexityClient:
    """Client for interacting with the Perplexity API."""
    
    API_URL = "https://api.perplexity.ai/chat/completions"
    DEFAULT_MODEL = "llama-3.1-sonar-small-128k-online"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Perplexity client.
        
        Args:
            api_key: Perplexity API key (defaults to PERPLEXITY_API_KEY environment variable)
        """
        self.api_key = api_key or os.environ.get("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise ValueError("Perplexity API key is required")
    
    def get_completion(self, 
                      prompt: str, 
                      system_message: Optional[str] = None,
                      context: Optional[Dict[str, Any]] = None,
                      model: Optional[str] = None,
                      temperature: float = 0.2) -> Dict[str, Any]:
        """
        Get a completion from the Perplexity API.
        
        Args:
            prompt: The user's prompt/question
            system_message: Optional system message to guide the AI response
            context: Optional dict with context information to include in the prompt
            model: Model to use (defaults to DEFAULT_MODEL)
            temperature: Temperature for response generation (0.0-1.0, higher = more creative)
            
        Returns:
            Dictionary with the API response
        """
        # Prepare messages
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({
                "role": "system",
                "content": system_message
            })
        
        # Construct the user prompt with context if provided
        user_prompt = prompt
        if context:
            # Format context as JSON and include it in the prompt
            context_str = json.dumps(context, indent=2)
            user_prompt = f"Given the following context:\n\n{context_str}\n\n{prompt}"
        
        # Add user message
        messages.append({
            "role": "user",
            "content": user_prompt
        })
        
        # Prepare the request payload
        payload = {
            "model": model or self.DEFAULT_MODEL,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 1,
            "presence_penalty": 0,
            "stream": False
        }
        
        # Set headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # Make the API request
            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30  # 30 second timeout
            )
            
            # Check for successful response
            response.raise_for_status()
            
            # Parse and return the response
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error querying Perplexity API: {str(e)}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    
    def get_sync_guidance(self, 
                         question: str, 
                         sync_context: Dict[str, Any]) -> str:
        """
        Get guidance specific to sync configuration.
        
        Args:
            question: The user's question about sync configuration
            sync_context: Context about the current sync setup
            
        Returns:
            String with the AI-generated guidance
        """
        system_message = """
        You are TerraAssist, an expert AI assistant for the TerraFusion SyncService platform.
        Your role is to provide helpful, accurate guidance on configuring data synchronization
        between county property assessment systems.
        
        Guidelines:
        - Provide clear, concise explanations suitable for county employees who may have
          varying technical expertise
        - Focus on practical guidance related to sync configuration, data mapping, and
          troubleshooting
        - When suggesting solutions, consider best practices for government data systems
        - Always prioritize data integrity and security in your recommendations
        - For complex technical questions, provide step-by-step instructions
        - Format your responses with proper headings, bullet points, and emphasis
          to improve readability
        
        Remember that you are assisting with property assessment data synchronization
        in a county government context, so your advice should align with government
        IT policies and practices.
        """
        
        try:
            # Get the completion
            response = self.get_completion(
                prompt=question,
                system_message=system_message,
                context=sync_context,
                temperature=0.2
            )
            
            # Extract and return the response text
            if response and "choices" in response and len(response["choices"]) > 0:
                return response["choices"][0]["message"]["content"]
            else:
                logger.error(f"Unexpected response format from Perplexity API: {response}")
                return "I'm sorry, I encountered an issue processing your request. Please try again."
                
        except Exception as e:
            logger.error(f"Error getting sync guidance: {str(e)}")
            return "I'm sorry, I encountered an error while trying to provide guidance. Please try again later."