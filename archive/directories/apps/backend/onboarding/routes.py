"""
Onboarding Routes

This module defines the routes for the user onboarding experience.
"""

from typing import Optional, Tuple, Dict

from flask import render_template, session, redirect, url_for, request, jsonify, flash, current_app
from flask_login import current_user, login_required

from . import onboarding_bp
from .config import get_tutorial_for_role
from apps.backend.models.onboarding import UserOnboarding, OnboardingEvent


@onboarding_bp.route('/')
@login_required
def tutorial_home():
    """
    Display the onboarding home page with tutorial overview.
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        flash("No tutorial available for your role.", "warning")
        return redirect(url_for('dashboard'))
    
    # Get or create user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    # Calculate progress
    completed_steps = onboarding.completed_step_ids
    progress = onboarding.get_progress_percentage(len(tutorial.steps))
    
    # If onboarding is complete, redirect to completion page
    if onboarding.is_complete:
        return redirect(url_for('onboarding_bp.onboarding_complete'))
    
    # Process steps to mark as completed or not
    steps = []
    for step in tutorial.steps:
        steps.append({
            'id': step.id,
            'title': step.title,
            'description': step.description,
            'completed': step.id in completed_steps
        })
    
    return render_template(
        'tutorial.html',
        tutorial=tutorial,
        steps=steps,
        progress=progress,
        completed_steps=completed_steps
    )


@onboarding_bp.route('/step/<step_id>')
@login_required
def tutorial_step(step_id: str):
    """
    Display a single tutorial step.
    
    Args:
        step_id: ID of the step to display
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        flash("No tutorial available for your role.", "warning")
        return redirect(url_for('dashboard'))
    
    # Find the step
    step = None
    step_index = -1
    for i, s in enumerate(tutorial.steps):
        if s.id == step_id:
            step = s
            step_index = i
            break
    
    if not step:
        flash("Tutorial step not found.", "error")
        return redirect(url_for('onboarding_bp.tutorial_home'))
    
    # Get user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    # Update last visited step
    onboarding.last_step_id = step_id
    
    # Check if step is completed
    completed = step_id in onboarding.completed_step_ids
    completed_steps = onboarding.completed_step_ids
    
    # Get previous and next steps
    prev_step = tutorial.steps[step_index - 1] if step_index > 0 else None
    next_step = tutorial.steps[step_index + 1] if step_index < len(tutorial.steps) - 1 else None
    
    # Calculate progress
    progress = onboarding.get_progress_percentage(len(tutorial.steps))
    
    return render_template(
        'step.html',
        tutorial=tutorial,
        step=step,
        prev_step=prev_step,
        next_step=next_step,
        completed=completed,
        completed_steps=completed_steps,
        progress=progress
    )


@onboarding_bp.route('/step/<step_id>/complete', methods=['POST'])
@login_required
def complete_step(step_id: str):
    """
    Mark a step as completed.
    
    Args:
        step_id: ID of the step to mark as completed
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        return jsonify({'success': False, 'error': 'No tutorial available for your role'}), 400
    
    # Find the step
    step = None
    for s in tutorial.steps:
        if s.id == step_id:
            step = s
            break
    
    if not step:
        return jsonify({'success': False, 'error': 'Tutorial step not found'}), 404
    
    # Get user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    # Mark step as completed
    onboarding.mark_step_complete(step_id)
    
    # Check if all steps are completed
    completed_steps = set(onboarding.completed_step_ids)
    all_steps = set(s.id for s in tutorial.steps)
    
    # If all steps are completed, mark onboarding as complete
    if completed_steps == all_steps:
        onboarding.mark_complete()
    
    return jsonify({'success': True})


@onboarding_bp.route('/complete', methods=['GET', 'POST'])
@login_required
def onboarding_complete():
    """
    Display the onboarding completion page.
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        flash("No tutorial available for your role.", "warning")
        return redirect(url_for('dashboard'))
    
    # Get user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    if request.method == 'POST':
        # Mark onboarding as complete if not already
        if not onboarding.is_complete:
            onboarding.mark_complete()
        
        # Redirect to dashboard
        flash("Onboarding completed! Welcome to the TerraFusion platform.", "success")
        return redirect(url_for('dashboard'))
    
    # Get number of steps completed
    completed_steps = len(onboarding.completed_step_ids)
    total_steps = len(tutorial.steps)
    
    return render_template(
        'completion.html',
        tutorial=tutorial,
        user=current_user,
        steps_completed=completed_steps,
        total_steps=total_steps
    )


@onboarding_bp.route('/skip', methods=['POST'])
@login_required
def skip_onboarding():
    """
    Skip the onboarding tutorial.
    
    This will mark all steps as complete and redirect to the dashboard.
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        return jsonify({'success': False, 'error': 'No tutorial available for your role'}), 400
    
    # Get user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    # Mark all steps as completed
    for step in tutorial.steps:
        onboarding.mark_step_complete(step.id)
    
    # Mark onboarding as complete
    onboarding.mark_complete()
    
    return jsonify({
        'success': True,
        'redirect': url_for('dashboard')
    })


@onboarding_bp.route('/reset', methods=['POST'])
@login_required
def reset_onboarding():
    """
    Reset the onboarding progress.
    
    This will clear all completed steps and allow the user to start over.
    """
    # Get tutorial for user's role
    tutorial = get_tutorial_for_role(current_user.role)
    if not tutorial:
        return jsonify({'success': False, 'error': 'No tutorial available for your role'}), 400
    
    # Get user onboarding record
    onboarding = UserOnboarding.get_for_user(current_user.id, tutorial.id)
    
    # Reset progress
    onboarding.reset_progress()
    
    return jsonify({
        'success': True,
        'redirect': url_for('onboarding_bp.tutorial_home')
    })