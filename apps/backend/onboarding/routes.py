"""
Onboarding routes and controllers for TerraFusion SyncService.

This module provides interactive tutorials and onboarding experiences
for new users based on their roles.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for, flash, current_app

from apps.backend.auth import requires_auth, get_current_user
from apps.backend.database import db
from apps.backend.models.onboarding import UserOnboarding

# Configure logging
logger = logging.getLogger(__name__)

# Tutorial steps by role
TUTORIAL_STEPS = {
    "ITAdmin": [
        {"title": "Welcome Admin", "description": "Welcome to the IT Administrator interface. This tutorial will guide you through system administration features.", "image": "admin_welcome.svg"},
        {"title": "System Overview", "description": "The dashboard shows system health, recent sync operations, and active users.", "image": "admin_system.svg"},
        {"title": "User Management", "description": "You can manage users, roles, and permissions from the Administration panel.", "image": "admin_users.svg"},
        {"title": "Configuration", "description": "Adjust system settings, connection parameters, and security policies.", "image": "admin_config.svg"},
        {"title": "Monitoring", "description": "View detailed logs, metrics, and set up alerts for critical events.", "image": "admin_complete.svg"}
    ],
    "Assessor": [
        {"title": "Welcome Assessor", "description": "Welcome to the County Assessor interface. This tutorial will guide you through the review and approval process.", "image": "assessor_welcome.svg"},
        {"title": "Review Queue", "description": "Your dashboard shows pending approvals that require your review.", "image": "assessor_queue.svg"},
        {"title": "Assessment Details", "description": "Click on any entry to view detailed information and compare changes.", "image": "assessor_details.svg"},
        {"title": "Approval Process", "description": "After reviewing, you can approve, reject, or request changes.", "image": "assessor_approval.svg"},
        {"title": "Reports", "description": "Generate reports on approved and pending assessments.", "image": "assessor_complete.svg"}
    ],
    "Staff": [
        {"title": "Welcome Staff", "description": "Welcome to the County Staff interface. This tutorial will guide you through data submission.", "image": "staff_welcome.svg"},
        {"title": "Submission Queue", "description": "Your dashboard shows recent submissions and their status.", "image": "staff_queue.svg"},
        {"title": "Upload Process", "description": "Use the upload button to submit new property assessment data.", "image": "staff_upload.svg"},
        {"title": "Validation", "description": "All submissions are automatically validated before review.", "image": "staff_validation.svg"},
        {"title": "Status Tracking", "description": "Track the status of your submissions through the approval process.", "image": "staff_complete.svg"}
    ],
    "Auditor": [
        {"title": "Welcome Auditor", "description": "Welcome to the County Auditor interface. This tutorial will guide you through audit capabilities.", "image": "auditor_welcome.svg"},
        {"title": "Audit Logs", "description": "Your dashboard shows a complete audit trail of all system activities.", "image": "auditor_logs.svg"},
        {"title": "Filter Controls", "description": "Use filters to search for specific activities by user, date, or type.", "image": "auditor_filters.svg"},
        {"title": "Compliance Reports", "description": "Generate compliance reports for internal or external review.", "image": "auditor_reports.svg"},
        {"title": "Alert Configuration", "description": "Set up alerts for unusual or high-risk activities.", "image": "auditor_complete.svg"}
    ],
    "default": [
        {"title": "Welcome", "description": "Welcome to TerraFusion SyncService. This tutorial will guide you through the basics.", "image": "default_welcome.svg"},
        {"title": "Dashboard", "description": "Your dashboard shows recent activity and key information.", "image": "default_dashboard.svg"},
        {"title": "Navigation", "description": "Use the menu on the left to access different features.", "image": "default_nav.svg"},
        {"title": "Profile", "description": "Manage your profile and preferences.", "image": "default_profile.svg"},
        {"title": "Help & Support", "description": "Access documentation and support resources.", "image": "default_complete.svg"}
    ]
}

def get_or_create_onboarding(user: Dict[str, Any]) -> UserOnboarding:
    """
    Get or create an onboarding record for a user.
    
    Args:
        user: User dictionary with id, username, roles
        
    Returns:
        UserOnboarding instance
    """
    # Extract user information
    user_id = user.get('id', f"user-{user.get('username', 'unknown')}")
    username = user.get('username', 'unknown')
    
    # Get user's primary role (first in list)
    roles = user.get('roles', [])
    role = roles[0] if roles else 'default'
    
    # Try to find existing onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        # Create new onboarding record
        onboarding = UserOnboarding(
            user_id=user_id,
            username=username,
            role=role,
            total_steps=len(TUTORIAL_STEPS.get(role, TUTORIAL_STEPS['default']))
        )
        db.session.add(onboarding)
        db.session.commit()
        logger.info(f"Created new onboarding record for user {username} with role {role}")
    
    return onboarding

def create_onboarding_blueprint() -> Blueprint:
    """
    Create the onboarding blueprint.
    
    Returns:
        Flask Blueprint for onboarding
    """
    onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/onboarding')
    
    @onboarding_bp.route('/', methods=['GET'])
    @requires_auth
    def onboarding_home():
        """Display the onboarding home page."""
        user = get_current_user()
        if not user:
            flash('Please log in to access the onboarding tutorial', 'error')
            return redirect(url_for('login_page'))
        
        # Get or create onboarding for this user
        onboarding = get_or_create_onboarding(user)
        
        # Get role-specific tutorial steps
        roles = user.get('roles', [])
        role = roles[0] if roles else 'default'
        steps = TUTORIAL_STEPS.get(role, TUTORIAL_STEPS['default'])
        
        return render_template(
            'onboarding/tutorial.html',
            user=user,
            onboarding=onboarding,
            steps=steps,
            current_step=onboarding.current_step,
            role=role
        )
    
    @onboarding_bp.route('/step/<int:step_number>', methods=['GET'])
    @requires_auth
    def view_step(step_number):
        """View a specific tutorial step."""
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get onboarding for this user
        onboarding = get_or_create_onboarding(user)
        
        # Check if the step is accessible
        if step_number > onboarding.current_step:
            flash('Please complete the previous steps first', 'warning')
            return redirect(url_for('onboarding_bp.onboarding_home'))
        
        # Get role-specific tutorial steps
        roles = user.get('roles', [])
        role = roles[0] if roles else 'default'
        steps = TUTORIAL_STEPS.get(role, TUTORIAL_STEPS['default'])
        
        # Make sure the step exists
        if step_number < 1 or step_number > len(steps):
            flash('Invalid tutorial step', 'error')
            return redirect(url_for('onboarding_bp.onboarding_home'))
        
        # Get the step content
        step = steps[step_number - 1]
        
        return render_template(
            'onboarding/step.html',
            user=user,
            onboarding=onboarding,
            step=step,
            step_number=step_number,
            total_steps=len(steps),
            role=role
        )
    
    @onboarding_bp.route('/complete/<int:step_number>', methods=['POST'])
    @requires_auth
    def complete_step(step_number):
        """Mark a step as completed."""
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get onboarding for this user
        onboarding = get_or_create_onboarding(user)
        
        # Update onboarding progress
        onboarding.mark_step_completed(step_number)
        db.session.commit()
        
        # Get role-specific tutorial steps
        roles = user.get('roles', [])
        role = roles[0] if roles else 'default'
        steps = TUTORIAL_STEPS.get(role, TUTORIAL_STEPS['default'])
        
        # Check if this was the last step
        if step_number >= len(steps):
            # Redirect to completion page
            return jsonify({
                'success': True,
                'completed': True,
                'redirect': url_for('onboarding_bp.completion')
            })
        
        # Redirect to next step
        return jsonify({
            'success': True,
            'completed': False,
            'next_step': step_number + 1,
            'redirect': url_for('onboarding_bp.view_step', step_number=step_number + 1)
        })
    
    @onboarding_bp.route('/dismiss', methods=['POST'])
    @requires_auth
    def dismiss_onboarding():
        """Dismiss the onboarding tutorial."""
        user = get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Get onboarding for this user
        onboarding = get_or_create_onboarding(user)
        
        # Dismiss onboarding
        onboarding.dismiss_onboarding()
        db.session.commit()
        
        return jsonify({'success': True})
    
    @onboarding_bp.route('/completion', methods=['GET'])
    @requires_auth
    def completion():
        """Display the onboarding completion page."""
        user = get_current_user()
        if not user:
            flash('Please log in to access the onboarding tutorial', 'error')
            return redirect(url_for('login_page'))
        
        # Get onboarding for this user
        onboarding = get_or_create_onboarding(user)
        
        # Get role-specific content
        roles = user.get('roles', [])
        role = roles[0] if roles else 'default'
        
        # Get completion message and image
        completion_messages = {
            'ITAdmin': 'You now have full access to all administrative tools and features.',
            'Assessor': 'You can now review and approve property assessment changes.',
            'Staff': 'You can now submit new property assessment data for review.',
            'Auditor': 'You now have full access to audit logs and reporting tools.',
            'default': 'You have completed the basic tutorial and can now use the system.'
        }
        
        message = completion_messages.get(role, completion_messages['default'])
        image = f"{role.lower()}_complete.svg"
        
        return render_template(
            'onboarding/completion.html',
            user=user,
            onboarding=onboarding,
            role=role,
            message=message,
            image=image
        )
    
    return onboarding_bp