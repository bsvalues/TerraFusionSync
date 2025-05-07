"""
Routes for the TerraFusion SyncService onboarding module.

This module provides routes for the interactive onboarding experience.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, session, g
from werkzeug.exceptions import NotFound
from functools import wraps

from apps.backend.database import db
from apps.backend.models.onboarding import UserOnboarding

logger = logging.getLogger(__name__)

# Create a blueprint for onboarding
onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/onboarding')

# Create a simple audit log function
def create_audit_log(user_id: str, action: str, details: str):
    """Create a simple audit log entry."""
    logger.info(f"AUDIT: {user_id} - {action} - {details}")
    # In a real system, this would save to the database

# Tutorial step definitions - customized per role
TUTORIAL_STEPS = {
    'ITAdmin': [
        {
            'title': 'Dashboard Overview',
            'description': 'Learn how to navigate the main dashboard and access system administration features.',
            'image': 'itadmin_dashboard.svg'
        },
        {
            'title': 'User Management',
            'description': 'Manage user accounts, roles, and permissions for the TerraFusion platform.',
            'image': 'itadmin_users.svg'
        },
        {
            'title': 'System Monitoring',
            'description': 'Monitor system performance, view logs, and maintain optimal service health.',
            'image': 'itadmin_monitoring.svg'
        },
        {
            'title': 'Backup & Recovery',
            'description': 'Configure backup schedules and learn how to perform disaster recovery.',
            'image': 'itadmin_backup.svg'
        },
        {
            'title': 'Security Settings',
            'description': 'Configure security policies, audit logs, and access controls.',
            'image': 'itadmin_security.svg'
        }
    ],
    'Assessor': [
        {
            'title': 'Dashboard Overview',
            'description': 'Learn how to navigate the main dashboard and access assessment features.',
            'image': 'assessor_dashboard.svg'
        },
        {
            'title': 'Review Queue',
            'description': 'Access and manage the property assessment review queue.',
            'image': 'assessor_review.svg'
        },
        {
            'title': 'Approval Process',
            'description': 'Learn how to review, approve, or reject property assessment submissions.',
            'image': 'assessor_approval.svg'
        },
        {
            'title': 'Data Validation',
            'description': 'Understand the validation process and how to address data quality issues.',
            'image': 'assessor_validation.svg'
        }
    ],
    'Staff': [
        {
            'title': 'Dashboard Overview',
            'description': 'Learn how to navigate the main dashboard and access staff features.',
            'image': 'staff_dashboard.svg'
        },
        {
            'title': 'File Upload',
            'description': 'Learn how to upload property assessment data files for processing.',
            'image': 'staff_upload.svg'
        },
        {
            'title': 'Submission Status',
            'description': 'Track the status of your uploaded files and submissions.',
            'image': 'staff_status.svg'
        },
        {
            'title': 'Error Correction',
            'description': 'Understand how to address validation errors in your submissions.',
            'image': 'staff_errors.svg'
        }
    ],
    'Auditor': [
        {
            'title': 'Dashboard Overview',
            'description': 'Learn how to navigate the main dashboard and access audit features.',
            'image': 'auditor_dashboard.svg'
        },
        {
            'title': 'Audit Trail',
            'description': 'Access and review the comprehensive audit trail of system activities.',
            'image': 'auditor_trail.svg'
        },
        {
            'title': 'Compliance Reports',
            'description': 'Generate and export compliance reports for regulatory requirements.',
            'image': 'auditor_reports.svg'
        },
        {
            'title': 'User Activity',
            'description': 'Monitor and review user activities and access patterns.',
            'image': 'auditor_activity.svg'
        }
    ],
    'default': [
        {
            'title': 'Dashboard Overview',
            'description': 'Learn how to navigate the main dashboard and access core features.',
            'image': 'default_dashboard.svg'
        },
        {
            'title': 'Account Settings',
            'description': 'Configure your user profile and preferences.',
            'image': 'default_account.svg'
        },
        {
            'title': 'Basic Features',
            'description': 'Explore the basic features available to all users.',
            'image': 'default_features.svg'
        }
    ]
}

# Welcome and completion messages/images
WELCOME_MESSAGES = {
    'ITAdmin': {
        'message': 'Welcome to the IT Administrator onboarding tutorial. This guide will help you learn about the powerful administrative features available to you.',
        'image': 'itadmin_welcome.svg'
    },
    'Assessor': {
        'message': 'Welcome to the County Assessor onboarding tutorial. This guide will help you understand the property assessment review and approval process.',
        'image': 'assessor_welcome.svg'
    },
    'Staff': {
        'message': 'Welcome to the County Staff onboarding tutorial. This guide will help you learn how to upload and manage property assessment data.',
        'image': 'staff_welcome.svg'
    },
    'Auditor': {
        'message': 'Welcome to the County Auditor onboarding tutorial. This guide will help you access and understand the comprehensive audit capabilities.',
        'image': 'auditor_welcome.svg'
    },
    'default': {
        'message': 'Welcome to the TerraFusion SyncService onboarding tutorial. This guide will help you get started with the platform.',
        'image': 'default_welcome.svg'
    }
}

COMPLETION_MESSAGES = {
    'ITAdmin': {
        'message': 'Congratulations! You have completed the IT Administrator tutorial. You now have the knowledge to effectively manage the TerraFusion platform.',
        'image': 'itadmin_complete.svg'
    },
    'Assessor': {
        'message': 'Congratulations! You have completed the County Assessor tutorial. You are now ready to review and approve property assessments.',
        'image': 'assessor_complete.svg'
    },
    'Staff': {
        'message': 'Congratulations! You have completed the County Staff tutorial. You are now ready to upload and manage property assessment data.',
        'image': 'staff_complete.svg'
    },
    'Auditor': {
        'message': 'Congratulations! You have completed the County Auditor tutorial. You are now ready to access and analyze the comprehensive audit trail.',
        'image': 'auditor_complete.svg'
    },
    'default': {
        'message': 'Congratulations! You have completed the TerraFusion SyncService tutorial. You are now ready to use the platform effectively.',
        'image': 'default_complete.svg'
    }
}

def get_user_onboarding(user_id: str) -> UserOnboarding:
    """Get or create a user onboarding record."""
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    if not onboarding:
        # Create a new onboarding record
        onboarding = UserOnboarding(
            user_id=user_id,
            current_step=1,
            tutorial_complete=False,
            progress=json.dumps({}),
            completion_date=None
        )
        db.session.add(onboarding)
        db.session.commit()
    return onboarding

def get_steps_for_role(role: str) -> List[Dict]:
    """Get tutorial steps for a specific role."""
    return TUTORIAL_STEPS.get(role, TUTORIAL_STEPS['default'])

def get_welcome_for_role(role: str) -> Dict:
    """Get welcome message and image for a specific role."""
    return WELCOME_MESSAGES.get(role, WELCOME_MESSAGES['default'])

def get_completion_for_role(role: str) -> Dict:
    """Get completion message and image for a specific role."""
    return COMPLETION_MESSAGES.get(role, COMPLETION_MESSAGES['default'])

# Authentication helper function
def get_current_user():
    """Get current user from session."""
    return session.get('user')

# Simple decorator for requiring authentication
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# Admin role check
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get('user', {})
        roles = user.get('roles', [])
        if 'ITAdmin' not in roles:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated

@onboarding_bp.route('/')
@login_required
def onboarding_home():
    """Display the onboarding home page."""
    user = get_current_user()
    user_id = user.get('id')
    
    # Get role from user's roles - use first one or default
    roles = user.get('roles', ['default'])
    role = roles[0] if roles else 'default'
    
    # Get or create onboarding record
    onboarding = get_user_onboarding(user_id)
    
    # Get steps for the user's role
    steps = get_steps_for_role(role)
    
    return render_template(
        'onboarding/tutorial.html',
        user=user,
        role=role,
        onboarding=onboarding,
        steps=steps
    )

@onboarding_bp.route('/step/<int:step_number>')
@login_required
def view_step(step_number: int):
    """Display a specific tutorial step."""
    user = get_current_user()
    user_id = user.get('id')
    
    # Get role from user's roles - use first one or default
    roles = user.get('roles', ['default'])
    role = roles[0] if roles else 'default'
    
    # Get or create onboarding record
    onboarding = get_user_onboarding(user_id)
    
    # Get steps for the user's role
    steps = get_steps_for_role(role)
    total_steps = len(steps)
    
    # Validate step number
    if step_number < 1 or step_number > total_steps:
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Get step content
    step = steps[step_number - 1]
    
    # If user is trying to access a future step
    if step_number > onboarding.current_step:
        return redirect(url_for('onboarding_bp.view_step', step_number=onboarding.current_step))
    
    return render_template(
        'onboarding/step.html',
        user=user,
        role=role,
        step=step,
        step_number=step_number,
        total_steps=total_steps
    )

@onboarding_bp.route('/complete/<int:step_number>', methods=['POST'])
@login_required
def complete_step(step_number: int):
    """Mark a step as complete and redirect to the next step."""
    user = get_current_user()
    user_id = user.get('id')
    
    # Get role from user's roles - use first one or default
    roles = user.get('roles', ['default'])
    role = roles[0] if roles else 'default'
    
    # Get or create onboarding record
    onboarding = get_user_onboarding(user_id)
    
    # Get steps for the user's role
    steps = get_steps_for_role(role)
    total_steps = len(steps)
    
    # Validate step number
    if step_number < 1 or step_number > total_steps:
        return jsonify({'success': False, 'error': 'Invalid step number'}), 400
    
    # Update progress
    progress = onboarding.progress_dict
    progress[str(step_number)] = {
        'completed': True,
        'completed_at': datetime.utcnow().isoformat()
    }
    onboarding.progress = json.dumps(progress)
    
    # If this is the current step, advance to the next step
    if step_number == onboarding.current_step and step_number < total_steps:
        onboarding.current_step += 1
    
    # If this is the final step, mark the tutorial as complete
    if step_number == total_steps:
        onboarding.tutorial_complete = True
        onboarding.completion_date = datetime.utcnow()
        
        # Log that the user completed the tutorial
        create_audit_log(
            user_id=user_id,
            action='tutorial_completed',
            details=f"User completed the {role} tutorial"
        )
    
    db.session.commit()
    
    # Determine where to redirect
    if step_number < total_steps:
        redirect_url = url_for('onboarding_bp.view_step', step_number=step_number + 1)
    else:
        redirect_url = url_for('onboarding_bp.completion_page')
    
    return jsonify({
        'success': True,
        'redirect': redirect_url
    })

@onboarding_bp.route('/completion')
@login_required
def completion_page():
    """Display the tutorial completion page."""
    user = get_current_user()
    user_id = user.get('id')
    
    # Get role from user's roles - use first one or default
    roles = user.get('roles', ['default'])
    role = roles[0] if roles else 'default'
    
    # Get or create onboarding record
    onboarding = get_user_onboarding(user_id)
    
    # If the tutorial is not complete, redirect to the current step
    if not onboarding.tutorial_complete:
        return redirect(url_for('onboarding_bp.view_step', step_number=onboarding.current_step))
    
    # Get completion message and image
    completion_data = get_completion_for_role(role)
    
    return render_template(
        'onboarding/completion.html',
        user=user,
        role=role,
        message=completion_data['message'],
        image=completion_data['image']
    )

@onboarding_bp.route('/dismiss', methods=['POST'])
@login_required
def dismiss_onboarding():
    """Dismiss the onboarding tutorial."""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    user_id = user.get('id')
    
    # Get or create onboarding record
    onboarding = get_user_onboarding(user_id)
    
    # Mark the tutorial as dismissed
    onboarding.tutorial_dismissed = True
    onboarding.dismissed_date = datetime.utcnow()
    
    db.session.commit()
    
    # Log that the user dismissed the tutorial
    create_audit_log(
        user_id=user_id,
        action='tutorial_dismissed',
        details="User dismissed the onboarding tutorial"
    )
    
    return jsonify({'success': True})

@onboarding_bp.route('/reset', methods=['POST'])
@login_required
@admin_required
def reset_onboarding():
    """Reset the onboarding tutorial for a user (admin only)."""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'User ID required'}), 400
    
    # Get the onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    if not onboarding:
        return jsonify({'success': False, 'error': 'Onboarding record not found'}), 404
    
    # Reset the onboarding record
    onboarding.current_step = 1
    onboarding.tutorial_complete = False
    onboarding.tutorial_dismissed = False
    onboarding.progress = '{}'
    onboarding.completion_date = None
    onboarding.dismissed_date = None
    
    db.session.commit()
    
    # Log that an admin reset the onboarding
    admin_user = get_current_user()
    create_audit_log(
        user_id=admin_user.get('id'),
        action='tutorial_reset',
        details=f"Admin reset onboarding tutorial for user {user_id}"
    )
    
    return jsonify({'success': True})