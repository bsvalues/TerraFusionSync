"""
TerraFusion SyncService - Onboarding Routes

This module provides routes for the interactive onboarding tutorial.
"""

import logging
from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, request, jsonify, g

from apps.backend.database import get_shared_db
from apps.backend.models.onboarding import UserOnboarding, OnboardingEvent
from apps.backend.onboarding.config import (
    get_tutorial_steps, get_welcome_message, get_completion_message
)
from apps.backend.auth.county_rbac import requires_auth
from . import onboarding_bp

# Configure logger
logger = logging.getLogger(__name__)

# Get database instance
db = get_shared_db()

@onboarding_bp.route('/')
@requires_auth
def onboarding_home():
    """Interactive tutorial home page."""
    # Get current user
    user = g.user
    if not user:
        return redirect(url_for('login'))
        
    # Get or create onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # If tutorial is complete, show completion page
    if onboarding.tutorial_complete:
        return redirect(url_for('onboarding_bp.tutorial_completion'))
    
    # Get tutorial steps for the user's role
    steps = get_tutorial_steps(user.role)
    if not steps:
        flash('No tutorial is available for your role.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Get welcome message
    welcome_message = get_welcome_message(user.role)
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='tutorial_view'
    )
    
    return render_template(
        'tutorial.html',
        onboarding=onboarding,
        steps=steps,
        role=user.role,
        welcome_message=welcome_message
    )

@onboarding_bp.route('/step/<int:step_number>')
@requires_auth
def view_step(step_number):
    """View a specific tutorial step."""
    # Get current user
    user = g.user
    if not user:
        return redirect(url_for('login'))
    
    # Get or create onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # If tutorial is complete, show completion page
    if onboarding.tutorial_complete:
        return redirect(url_for('onboarding_bp.tutorial_completion'))
    
    # Get tutorial steps for the user's role
    steps = get_tutorial_steps(user.role)
    if not steps:
        flash('No tutorial is available for your role.', 'warning')
        return redirect(url_for('dashboard'))
    
    # Validate step number
    if step_number < 1 or step_number > len(steps):
        flash('Invalid tutorial step.', 'error')
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Check if this step is accessible
    is_completed = str(step_number) in onboarding.progress_dict
    is_current = step_number == onboarding.current_step
    is_previous = step_number < onboarding.current_step
    
    if not (is_completed or is_current or is_previous):
        flash('You need to complete the previous steps first.', 'warning')
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Get step data
    step = steps[step_number - 1]
    total_steps = len(steps)
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='step_view',
        step_number=step_number
    )
    
    return render_template(
        'step.html',
        step=step,
        step_number=step_number,
        total_steps=total_steps,
        role=user.role,
        onboarding=onboarding
    )

@onboarding_bp.route('/step/<int:step_number>/complete', methods=['POST'])
@requires_auth
def complete_step(step_number):
    """Mark a tutorial step as completed."""
    # Get current user
    user = g.user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    # Get or create onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # Get tutorial steps for the user's role
    steps = get_tutorial_steps(user.role)
    if not steps:
        return jsonify({'success': False, 'error': 'No tutorial available for your role'})
    
    # Validate step number
    if step_number < 1 or step_number > len(steps):
        return jsonify({'success': False, 'error': 'Invalid tutorial step'})
    
    # Mark step as complete
    onboarding.mark_step_complete(step_number)
    db.session.commit()
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='step_complete',
        step_number=step_number
    )
    
    # Check if all steps are complete
    is_final_step = step_number == len(steps)
    is_all_complete = len(onboarding.progress_dict) == len(steps)
    
    if is_final_step and is_all_complete:
        # Mark tutorial as complete
        onboarding.mark_tutorial_complete()
        db.session.commit()
        
        # Log event
        OnboardingEvent.log_event(
            user_id=user.id,
            event_type='tutorial_complete'
        )
        
        return jsonify({
            'success': True,
            'redirect': url_for('onboarding_bp.tutorial_completion')
        })
    
    # Redirect to next step or back to overview
    if step_number < len(steps):
        next_step = step_number + 1
        return jsonify({
            'success': True,
            'redirect': url_for('onboarding_bp.view_step', step_number=next_step)
        })
    else:
        return jsonify({
            'success': True,
            'redirect': url_for('onboarding_bp.onboarding_home')
        })

@onboarding_bp.route('/completion')
@requires_auth
def tutorial_completion():
    """Tutorial completion page."""
    # Get current user
    user = g.user
    if not user:
        return redirect(url_for('login'))
    
    # Get onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # If tutorial is not complete, redirect to home
    if not onboarding.tutorial_complete:
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Get completion message
    completion = get_completion_message(user.role)
    message = completion.get('message') if completion else 'Congratulations on completing the tutorial!'
    image = completion.get('image') if completion else 'default_welcome.svg'
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='completion_view'
    )
    
    return render_template(
        'completion.html',
        message=message,
        image=image,
        role=user.role,
        user=user,
        onboarding=onboarding
    )

@onboarding_bp.route('/dismiss', methods=['POST'])
@requires_auth
def dismiss_onboarding():
    """Dismiss the tutorial without completing it."""
    # Get current user
    user = g.user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    # Get onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # Dismiss tutorial
    onboarding.dismiss_tutorial()
    db.session.commit()
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='tutorial_dismissed'
    )
    
    return jsonify({'success': True})

@onboarding_bp.route('/reset', methods=['POST'])
@requires_auth
def reset_onboarding():
    """Reset the tutorial progress."""
    # Get current user
    user = g.user
    if not user:
        return jsonify({'success': False, 'error': 'Authentication required'})
    
    # Get onboarding record
    onboarding = get_or_create_onboarding(user.id, user.role)
    
    # Reset progress
    onboarding.reset_progress()
    db.session.commit()
    
    # Log event
    OnboardingEvent.log_event(
        user_id=user.id,
        event_type='tutorial_reset'
    )
    
    return jsonify({'success': True})

def get_or_create_onboarding(user_id, role):
    """
    Get or create an onboarding record for a user.
    
    Args:
        user_id: ID of the user
        role: Role of the user
        
    Returns:
        UserOnboarding instance
    """
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        onboarding = UserOnboarding(
            user_id=user_id,
            role=role,
            current_step=1,
            progress='{}',
            tutorial_complete=False
        )
        db.session.add(onboarding)
        db.session.commit()
    
    return onboarding