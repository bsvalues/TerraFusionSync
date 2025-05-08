"""
TerraFusion SyncService AI Assistant - API Routes

This module provides Flask routes for the AI assistant features.
"""

import logging
from flask import Blueprint, request, jsonify, session, render_template
from .sync_assistant import SyncAssistant

# Create blueprint
ai_assistant_bp = Blueprint('ai_assistant', __name__, url_prefix='/ai-assistant')

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Sync Assistant
assistant = SyncAssistant()

# Custom decorator for permission check
def requires_permission(permission_name):
    """Decorator to check if user has required permission."""
    def decorator(f):
        from functools import wraps
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Try to use County RBAC if available
            try:
                from apps.backend.auth import check_county_permission
                
                if not check_county_permission(permission_name):
                    return jsonify({
                        "success": False,
                        "message": f"Permission denied: {permission_name} required"
                    }), 403
                
            except ImportError:
                # Fall back to role-based check using session
                user_role = session.get('role', '')
                
                # Map permissions to allowed roles
                permission_roles = {
                    'use_ai_assistant': ['ITAdmin', 'Assessor', 'Staff'],
                    'analyze_config': ['ITAdmin', 'Assessor'],
                    'advanced_features': ['ITAdmin']
                }
                
                if user_role not in permission_roles.get(permission_name, []):
                    return jsonify({
                        "success": False,
                        "message": f"Permission denied: Role {user_role} cannot access this feature"
                    }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

@ai_assistant_bp.route('/')
@requires_permission('use_ai_assistant')
def assistant_home():
    """AI Assistant home page."""
    return render_template('ai_assistant/index.html')

@ai_assistant_bp.route('/api/field-mapping', methods=['POST'])
@requires_permission('use_ai_assistant')
def field_mapping_suggestions():
    """Get field mapping suggestions."""
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'source_fields' not in data or 'target_fields' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required fields: source_fields and target_fields"
            }), 400
        
        # Get suggestions from assistant
        result = assistant.get_field_mapping_suggestions(
            source_fields=data['source_fields'],
            target_fields=data['target_fields']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error generating field mapping suggestions: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@ai_assistant_bp.route('/api/analyze-config', methods=['POST'])
@requires_permission('analyze_config')
def analyze_configuration():
    """Analyze sync configuration and provide recommendations."""
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'sync_config' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required field: sync_config"
            }), 400
        
        # Get user role
        user_role = session.get('role', 'Staff')
        
        # Get analysis from assistant
        result = assistant.analyze_sync_configuration(
            sync_config=data['sync_config'],
            user_role=user_role
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing sync configuration: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@ai_assistant_bp.route('/api/troubleshoot', methods=['POST'])
@requires_permission('use_ai_assistant')
def troubleshoot():
    """Get troubleshooting guidance for sync issues."""
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'issue_description' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required field: issue_description"
            }), 400
        
        # Get optional fields
        sync_logs = data.get('sync_logs')
        config = data.get('config')
        
        # Get guidance from assistant
        guidance = assistant.get_troubleshooting_guidance(
            issue_description=data['issue_description'],
            sync_logs=sync_logs,
            config=config
        )
        
        return jsonify({
            "success": True,
            "guidance": guidance
        })
        
    except Exception as e:
        logger.error(f"Error getting troubleshooting guidance: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500

@ai_assistant_bp.route('/api/ask', methods=['POST'])
@requires_permission('use_ai_assistant')
def ask_question():
    """Answer a question about sync configuration or operations."""
    try:
        data = request.json
        
        # Validate required fields
        if not data or 'question' not in data:
            return jsonify({
                "success": False,
                "message": "Missing required field: question"
            }), 400
        
        # Get optional context
        context = data.get('context')
        
        # Get answer from assistant
        answer = assistant.answer_question(
            question=data['question'],
            context=context
        )
        
        return jsonify({
            "success": True,
            "answer": answer
        })
        
    except Exception as e:
        logger.error(f"Error answering question: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error: {str(e)}"
        }), 500