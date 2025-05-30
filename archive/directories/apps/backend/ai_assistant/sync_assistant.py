"""
TerraFusion SyncService AI Assistant - Sync Configuration Guidance

This module provides AI-powered guidance for sync configuration and operations.
"""

import logging
from typing import Dict, List, Any, Optional

from . import default_client
from .perplexity_client import PerplexityClient

# Configure logging
logger = logging.getLogger(__name__)

class SyncAssistant:
    """
    Assistant for providing guidance on sync configuration and operations.
    """
    
    def __init__(self, ai_client=None):
        """
        Initialize the Sync Assistant.
        
        Args:
            ai_client: AI client instance (defaults to the default Perplexity client)
        """
        self.client = ai_client or default_client
        if not self.client:
            logger.warning("No AI client available, SyncAssistant will operate in limited mode")
    
    def get_field_mapping_suggestions(self, 
                                     source_fields: List[Dict[str, Any]], 
                                     target_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get suggestions for mapping fields between source and target systems.
        
        Args:
            source_fields: List of fields from the source system
            target_fields: List of fields from the target system
            
        Returns:
            Dictionary with field mapping suggestions
        """
        if not self.client:
            return {
                "success": False,
                "message": "AI assistant is not available",
                "suggestions": []
            }
        
        try:
            # Build context
            context = {
                "source_fields": source_fields,
                "target_fields": target_fields,
            }
            
            # Build the prompt
            prompt = """
            Please suggest field mappings between the source and target systems.
            Provide a JSON array of suggested mappings, where each mapping is an object with:
            - source_field: The name of the field in the source system
            - target_field: The name of the field in the target system
            - confidence: A score from 0-1 indicating confidence in the mapping
            - notes: Any notes or reasoning for the suggested mapping
            
            Only include high-confidence mappings (above 0.7).
            Use exact field names from the context provided.
            """
            
            # Get suggestions from AI
            response = self.client.get_completion(
                prompt=prompt,
                context=context,
                temperature=0.1  # Lower temperature for more deterministic output
            )
            
            # Process and structure the response
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                
                # Extract JSON array from the content (might be wrapped in markdown)
                import re
                import json
                
                # Try to find JSON array in the content
                json_match = re.search(r'\[\s*\{.*\}\s*\]', content, re.DOTALL)
                if json_match:
                    suggestions_json = json_match.group(0)
                    try:
                        suggestions = json.loads(suggestions_json)
                        return {
                            "success": True,
                            "message": "Generated field mapping suggestions",
                            "suggestions": suggestions
                        }
                    except json.JSONDecodeError:
                        logger.error(f"Could not parse JSON suggestions: {suggestions_json}")
                
                # If we couldn't extract JSON, return the raw content
                return {
                    "success": True,
                    "message": "Review these field mapping suggestions:",
                    "raw_content": content,
                    "suggestions": []
                }
            
            return {
                "success": False,
                "message": "Could not generate field mapping suggestions",
                "suggestions": []
            }
            
        except Exception as e:
            logger.error(f"Error generating field mapping suggestions: {str(e)}")
            return {
                "success": False,
                "message": f"Error generating suggestions: {str(e)}",
                "suggestions": []
            }
    
    def analyze_sync_configuration(self, 
                                  sync_config: Dict[str, Any],
                                  user_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a sync configuration and provide recommendations.
        
        Args:
            sync_config: The complete sync configuration
            user_role: Role of the user requesting analysis (adjusts detail level)
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        if not self.client:
            return {
                "success": False,
                "message": "AI assistant is not available",
                "analysis": "",
                "recommendations": []
            }
        
        try:
            # Build context
            context = {
                "sync_configuration": sync_config,
                "user_role": user_role or "Staff"
            }
            
            # Build the prompt
            prompt = """
            Please analyze this sync configuration and provide:
            1. A concise analysis of any potential issues or inefficiencies
            2. Specific recommendations for improvement
            3. Additional considerations based on best practices for government data systems
            
            Format your response with clear headings and bullet points for recommendations.
            Tailor the technical depth based on the user's role.
            """
            
            # Get analysis from AI
            response_text = self.client.get_sync_guidance(
                question=prompt,
                sync_context=context
            )
            
            # Process the response
            recommendations = []
            
            # Extract recommendations from the response (simple approach)
            import re
            rec_section = re.search(r'(?:Recommendations|RECOMMENDATIONS)[:\s]*((?:.+\n)+)', 
                                    response_text, re.IGNORECASE)
            
            if rec_section:
                rec_text = rec_section.group(1)
                # Extract bullet points
                bullets = re.findall(r'[-*]\s*(.+)', rec_text)
                recommendations = bullets
            
            return {
                "success": True,
                "message": "Configuration analysis complete",
                "analysis": response_text,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sync configuration: {str(e)}")
            return {
                "success": False,
                "message": f"Error analyzing configuration: {str(e)}",
                "analysis": "",
                "recommendations": []
            }
    
    def get_troubleshooting_guidance(self, 
                                    issue_description: str,
                                    sync_logs: Optional[List[Dict[str, Any]]] = None,
                                    config: Optional[Dict[str, Any]] = None) -> str:
        """
        Get troubleshooting guidance for sync issues.
        
        Args:
            issue_description: Description of the issue from the user
            sync_logs: Optional logs from the sync operation
            config: Optional sync configuration
            
        Returns:
            String with troubleshooting guidance
        """
        if not self.client:
            return "AI assistant is not available for troubleshooting guidance."
        
        try:
            # Build context
            context = {
                "issue_description": issue_description
            }
            
            if sync_logs:
                # Include only the most relevant logs (e.g., errors, last 10 entries)
                context["sync_logs"] = sync_logs[-10:]
            
            if config:
                context["configuration"] = config
            
            # Build the prompt
            prompt = f"""
            I need help troubleshooting this sync issue: {issue_description}
            
            Please provide:
            1. Potential causes of the issue
            2. Step-by-step troubleshooting instructions
            3. Recommended solutions
            
            Format your response with clear headings and steps.
            """
            
            # Get guidance from AI
            return self.client.get_sync_guidance(
                question=prompt,
                sync_context=context
            )
            
        except Exception as e:
            logger.error(f"Error getting troubleshooting guidance: {str(e)}")
            return f"I'm sorry, I encountered an error while generating troubleshooting guidance: {str(e)}"
    
    def answer_question(self, question: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Answer a general question about sync configuration or operations.
        
        Args:
            question: The user's question
            context: Optional context about the current sync setup
            
        Returns:
            String with the answer
        """
        if not self.client:
            return "AI assistant is not available to answer questions at this time."
        
        try:
            # Get answer from AI
            return self.client.get_sync_guidance(
                question=question,
                sync_context=context or {}
            )
            
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return f"I'm sorry, I encountered an error while answering your question: {str(e)}"