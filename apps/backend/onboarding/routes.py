"""
Onboarding routes for TerraFusion SyncService.

Provides routes for interactive user onboarding and role-based tutorials.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, current_app

# Configuration and utilities
logger = logging.getLogger(__name__)

# Import database model and app context
from ..models import UserOnboarding, db

def create_onboarding_blueprint() -> Blueprint:
    """Create the onboarding blueprint with routes."""
    onboarding_bp = Blueprint('onboarding_bp', __name__, url_prefix='/onboarding')
    
    @onboarding_bp.route('/', methods=['GET'])
    def onboarding_home():
        """
        Main onboarding route that redirects to appropriate tutorial
        based on the user's role and progress.
        """
        # Get current user from session
        try:
            from ..auth import get_county_current_user
            user = get_county_current_user()
        except (ImportError, AttributeError):
            # Fallback if county auth not available
            user = session.get('user', {})
        
        if not user:
            return redirect(url_for('login_page'))
        
        # Get or create onboarding record
        onboarding = get_or_create_onboarding(user)
        
        # If onboarding is completed or dismissed, redirect to dashboard
        if onboarding.dismissed or onboarding.onboarding_completed:
            return redirect(url_for('dashboard'))
        
        # Redirect to the current step
        return redirect(url_for('onboarding_bp.tutorial_step', role=onboarding.role, step=onboarding.current_step))
    
    @onboarding_bp.route('/tutorial/<string:role>/<int:step>', methods=['GET'])
    def tutorial_step(role, step):
        """
        Display a specific tutorial step for a role.
        """
        # Get current user
        try:
            from ..auth import get_county_current_user
            user = get_county_current_user()
        except (ImportError, AttributeError):
            user = session.get('user', {})
        
        if not user:
            return redirect(url_for('login_page'))
        
        # Get onboarding record
        onboarding = get_or_create_onboarding(user)
        
        # Check if role matches
        if onboarding.role != role:
            # Redirect to the correct role's onboarding
            return redirect(url_for('onboarding_bp.tutorial_step', role=onboarding.role, step=onboarding.current_step))
        
        # Get tutorial content based on role and step
        tutorial_content = get_tutorial_content(role, step)
        
        return render_template(
            'onboarding/tutorial.html',
            user=user,
            role=role,
            current_step=step,
            total_steps=get_total_steps(role),
            tutorial=tutorial_content,
            onboarding=onboarding
        )
    
    @onboarding_bp.route('/mark_completed/<int:step>', methods=['POST'])
    def mark_step_completed(step):
        """
        Mark a step as completed and redirect to the next step.
        """
        # Get current user
        try:
            from ..auth import get_county_current_user
            user = get_county_current_user()
        except (ImportError, AttributeError):
            user = session.get('user', {})
        
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get onboarding record
        onboarding = get_or_create_onboarding(user)
        
        # Mark the step as completed
        onboarding.mark_step_completed(step)
        db.session.commit()
        
        # Check if this was the last step
        if step >= get_total_steps(onboarding.role):
            onboarding.complete_onboarding()
            db.session.commit()
            return jsonify({
                'success': True, 
                'completed': True,
                'redirect': url_for('dashboard')
            })
        
        # Return next step info
        return jsonify({
            'success': True, 
            'next_step': onboarding.current_step,
            'redirect': url_for('onboarding_bp.tutorial_step', role=onboarding.role, step=onboarding.current_step)
        })
    
    @onboarding_bp.route('/dismiss', methods=['POST'])
    def dismiss_onboarding():
        """
        Dismiss the onboarding tutorial permanently.
        """
        # Get current user
        try:
            from ..auth import get_county_current_user
            user = get_county_current_user()
        except (ImportError, AttributeError):
            user = session.get('user', {})
        
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Get and update onboarding record
        onboarding = get_or_create_onboarding(user)
        onboarding.dismissed = True
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': url_for('dashboard')
        })
    
    @onboarding_bp.route('/reset', methods=['POST'])
    def reset_onboarding():
        """
        Reset onboarding progress.
        """
        # Get current user
        try:
            from ..auth import get_county_current_user
            user = get_county_current_user()
        except (ImportError, AttributeError):
            user = session.get('user', {})
        
        if not user:
            return jsonify({'error': 'Not authenticated'}), 401
        
        # Reset onboarding
        onboarding = get_or_create_onboarding(user)
        onboarding.current_step = 1
        onboarding.completed_steps = json.dumps([])
        onboarding.onboarding_completed = None
        onboarding.dismissed = False
        onboarding.last_activity = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'redirect': url_for('onboarding_bp.onboarding_home')
        })
    
    return onboarding_bp

def get_or_create_onboarding(user: Dict[str, Any]) -> UserOnboarding:
    """
    Get or create onboarding record for a user.
    
    Args:
        user: User dictionary from session
        
    Returns:
        UserOnboarding record
    """
    user_id = user.get('id', f"user-{user.get('username', 'unknown')}")
    username = user.get('username', 'unknown')
    
    # Default to the first role if multiple roles exist
    roles = user.get('roles', [])
    role = roles[0] if roles else 'Staff'  # Default to Staff as fallback
    
    # Try to find existing record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        # Create new record
        onboarding = UserOnboarding(
            user_id=user_id,
            username=username,
            role=role,
            current_step=1,
            completed_steps=json.dumps([]),
            tutorial_config=get_tutorial_config(role)
        )
        db.session.add(onboarding)
        db.session.commit()
    
    return onboarding

def get_tutorial_config(role: str) -> Dict[str, Any]:
    """
    Get tutorial configuration for a specific role.
    
    Args:
        role: User role
        
    Returns:
        Dictionary with tutorial configuration
    """
    # Get the number of steps for each role's tutorial
    return {
        'total_steps': get_total_steps(role),
        'role': role,
        'version': 1.0
    }

def get_total_steps(role: str) -> int:
    """
    Get the total number of tutorial steps for a role.
    
    Args:
        role: User role
        
    Returns:
        Number of steps
    """
    # Configuration of steps per role
    step_counts = {
        'ITAdmin': 7,
        'Assessor': 5,
        'Staff': 4,
        'Auditor': 4
    }
    
    return step_counts.get(role, 4)  # Default to 4 steps

def get_tutorial_content(role: str, step: int) -> Dict[str, Any]:
    """
    Get the tutorial content for a specific role and step.
    
    Args:
        role: User role
        step: Tutorial step
        
    Returns:
        Dictionary with tutorial content
    """
    # Load tutorial content from configuration
    # In a real application, this might be stored in a database or config files
    
    tutorials = {
        # ITAdmin tutorials
        'ITAdmin': {
            1: {
                'title': 'Welcome to County Property Assessment',
                'description': 'As an IT Administrator, you have full access to the system. This tutorial will help you understand how to manage the system, users, and data synchronization.',
                'image': 'admin_welcome.svg',
                'target_element': '#dashboard-overview',
                'actions': [
                    {'type': 'highlight', 'element': '#admin-panel', 'description': 'Admin panel for system configuration'},
                    {'type': 'click', 'element': '#admin-panel', 'description': 'Click here to access admin features'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            2: {
                'title': 'System Administration',
                'description': 'The System Administration panel provides tools for monitoring, configuration, and user management.',
                'image': 'admin_system.svg',
                'target_element': '#system-admin',
                'actions': [
                    {'type': 'highlight', 'element': '#system-status', 'description': 'View system status and metrics'},
                    {'type': 'highlight', 'element': '#user-management', 'description': 'Manage users and permissions'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            3: {
                'title': 'User Management',
                'description': 'As an administrator, you can manage users, roles, and permissions.',
                'image': 'admin_users.svg',
                'target_element': '#user-management',
                'actions': [
                    {'type': 'highlight', 'element': '#add-user', 'description': 'Add new users to the system'},
                    {'type': 'highlight', 'element': '#edit-roles', 'description': 'Modify user roles and permissions'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            4: {
                'title': 'Sync Pair Management',
                'description': 'Configure and manage synchronization between systems.',
                'image': 'admin_sync.svg',
                'target_element': '#sync-management',
                'actions': [
                    {'type': 'highlight', 'element': '#create-sync', 'description': 'Create new sync pairs'},
                    {'type': 'highlight', 'element': '#manage-sync', 'description': 'Manage existing sync pairs'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            5: {
                'title': 'Approval Workflow',
                'description': 'Review and approve sync operations submitted by staff.',
                'image': 'admin_approval.svg',
                'target_element': '#approval-queue',
                'actions': [
                    {'type': 'highlight', 'element': '#pending-approvals', 'description': 'View pending approval requests'},
                    {'type': 'highlight', 'element': '#approve-button', 'description': 'Approve sync operations'},
                    {'type': 'highlight', 'element': '#reject-button', 'description': 'Reject sync operations'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            6: {
                'title': 'System Monitoring',
                'description': 'Monitor system health, performance, and activity.',
                'image': 'admin_monitoring.svg',
                'target_element': '#system-monitoring',
                'actions': [
                    {'type': 'highlight', 'element': '#metrics-dashboard', 'description': 'View system metrics'},
                    {'type': 'highlight', 'element': '#logs-viewer', 'description': 'Access system logs'},
                    {'type': 'highlight', 'element': '#alerts', 'description': 'Configure system alerts'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            7: {
                'title': 'Congratulations!',
                'description': 'You\'ve completed the IT Administrator tutorial. You now have the knowledge to effectively manage the County Property Assessment system.',
                'image': 'admin_complete.svg',
                'completion_action': 'button',
                'button_text': 'Finish Tutorial'
            }
        },
        
        # Assessor tutorials
        'Assessor': {
            1: {
                'title': 'Welcome to County Property Assessment',
                'description': 'As an Assessor, you are responsible for reviewing and approving property data changes. This tutorial will guide you through the process.',
                'image': 'assessor_welcome.svg',
                'target_element': '#dashboard-overview',
                'actions': [
                    {'type': 'highlight', 'element': '#approval-queue', 'description': 'Your approval queue'},
                    {'type': 'click', 'element': '#approval-queue', 'description': 'Click here to see pending approvals'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            2: {
                'title': 'Reviewing Property Changes',
                'description': 'Learn how to review property data changes submitted by staff members.',
                'image': 'assessor_review.svg',
                'target_element': '#review-changes',
                'actions': [
                    {'type': 'highlight', 'element': '#change-details', 'description': 'View detailed changes'},
                    {'type': 'highlight', 'element': '#diff-viewer', 'description': 'See before and after comparisons'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            3: {
                'title': 'Approving Changes',
                'description': 'Learn how to approve property data changes after review.',
                'image': 'assessor_approve.svg',
                'target_element': '#approve-changes',
                'actions': [
                    {'type': 'highlight', 'element': '#approve-button', 'description': 'Approve verified changes'},
                    {'type': 'highlight', 'element': '#comments-field', 'description': 'Add comments for the record'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            4: {
                'title': 'Rejecting Changes',
                'description': 'Learn how to reject changes that need revision.',
                'image': 'assessor_reject.svg',
                'target_element': '#reject-changes',
                'actions': [
                    {'type': 'highlight', 'element': '#reject-button', 'description': 'Reject changes that need revision'},
                    {'type': 'highlight', 'element': '#feedback-field', 'description': 'Provide feedback for correction'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            5: {
                'title': 'Congratulations!',
                'description': 'You\'ve completed the Assessor tutorial. You now have the knowledge to effectively review and approve property data changes.',
                'image': 'assessor_complete.svg',
                'completion_action': 'button',
                'button_text': 'Finish Tutorial'
            }
        },
        
        # Staff tutorials
        'Staff': {
            1: {
                'title': 'Welcome to County Property Assessment',
                'description': 'As a Staff member, you can upload and manage property data. This tutorial will guide you through the process.',
                'image': 'staff_welcome.svg',
                'target_element': '#dashboard-overview',
                'actions': [
                    {'type': 'highlight', 'element': '#upload-section', 'description': 'Upload new data'},
                    {'type': 'click', 'element': '#upload-section', 'description': 'Click here to upload data'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            2: {
                'title': 'Uploading Property Data',
                'description': 'Learn how to upload property data files for synchronization.',
                'image': 'staff_upload.svg',
                'target_element': '#upload-form',
                'actions': [
                    {'type': 'highlight', 'element': '#file-input', 'description': 'Select files to upload'},
                    {'type': 'highlight', 'element': '#upload-button', 'description': 'Submit files for review'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            3: {
                'title': 'Tracking Your Uploads',
                'description': 'Monitor the status of your uploaded data.',
                'image': 'staff_tracking.svg',
                'target_element': '#my-uploads',
                'actions': [
                    {'type': 'highlight', 'element': '#upload-status', 'description': 'Check upload status'},
                    {'type': 'highlight', 'element': '#pending-reviews', 'description': 'Track pending reviews'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            4: {
                'title': 'Congratulations!',
                'description': 'You\'ve completed the Staff tutorial. You now have the knowledge to effectively upload and manage property data.',
                'image': 'staff_complete.svg',
                'completion_action': 'button',
                'button_text': 'Finish Tutorial'
            }
        },
        
        # Auditor tutorials
        'Auditor': {
            1: {
                'title': 'Welcome to County Property Assessment',
                'description': 'As an Auditor, you can view and audit property data operations. This tutorial will guide you through the auditing tools.',
                'image': 'auditor_welcome.svg',
                'target_element': '#dashboard-overview',
                'actions': [
                    {'type': 'highlight', 'element': '#audit-section', 'description': 'Access audit tools'},
                    {'type': 'click', 'element': '#audit-section', 'description': 'Click here to view audit logs'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            2: {
                'title': 'Viewing Audit Logs',
                'description': 'Learn how to access and filter audit logs.',
                'image': 'auditor_logs.svg',
                'target_element': '#audit-logs',
                'actions': [
                    {'type': 'highlight', 'element': '#log-filters', 'description': 'Filter logs by date, user, or action'},
                    {'type': 'highlight', 'element': '#export-logs', 'description': 'Export logs for reporting'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            3: {
                'title': 'Reviewing Sync Operations',
                'description': 'Audit completed sync operations and their changes.',
                'image': 'auditor_review.svg',
                'target_element': '#sync-history',
                'actions': [
                    {'type': 'highlight', 'element': '#operation-details', 'description': 'View operation details'},
                    {'type': 'highlight', 'element': '#change-history', 'description': 'See property change history'}
                ],
                'completion_action': 'button',
                'button_text': 'Continue'
            },
            4: {
                'title': 'Congratulations!',
                'description': 'You\'ve completed the Auditor tutorial. You now have the knowledge to effectively audit property data operations.',
                'image': 'auditor_complete.svg',
                'completion_action': 'button',
                'button_text': 'Finish Tutorial'
            }
        }
    }
    
    # Get tutorial for the specified role and step
    role_tutorials = tutorials.get(role, tutorials['Staff'])  # Default to Staff if role not found
    tutorial = role_tutorials.get(step, role_tutorials[1])  # Default to step 1 if step not found
    
    return tutorial