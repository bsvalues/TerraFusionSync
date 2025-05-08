"""
TerraFusion SyncService - Onboarding Routes

This module provides routes for the onboarding experience and tutorial.
"""

import json
from datetime import datetime

from flask import render_template, redirect, url_for, session, request, jsonify, current_app, flash

from apps.backend.database import get_shared_db
from apps.backend.models import User, UserOnboarding, OnboardingEvent
from apps.backend.onboarding import onboarding_bp
from apps.backend.onboarding.config import get_tutorial_for_role

db = get_shared_db()

@onboarding_bp.route('/')
def onboarding_home():
    """Onboarding home page - redirects to tutorial or completion page."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the onboarding tutorial.', 'warning')
        return redirect(url_for('login'))
    
    # Get user onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    # If no onboarding record, create one
    if not onboarding:
        user = User.query.get(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('dashboard'))
            
        onboarding = UserOnboarding(
            user_id=user_id,
            current_step='overview',
            progress_data=json.dumps({
                'completed_steps': [],
                'total_steps': len(get_tutorial_for_role(user.role)['steps'])
            })
        )
        db.session.add(onboarding)
        
        # Create an onboarding started event
        event = OnboardingEvent(
            onboarding_id=onboarding.id,
            event_type='onboarding_started'
        )
        db.session.add(event)
        db.session.commit()
    
    # If onboarding is completed, redirect to completion page
    if onboarding.is_completed:
        return redirect(url_for('onboarding_bp.onboarding_complete'))
    
    # Redirect to current step
    return redirect(url_for('onboarding_bp.tutorial_step', step_id=onboarding.current_step or 'overview'))

@onboarding_bp.route('/tutorial')
def tutorial_home():
    """Tutorial home page."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the onboarding tutorial.', 'warning')
        return redirect(url_for('login'))
    
    # Get user onboarding record
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    # If no onboarding record, redirect to start
    if not onboarding:
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Get tutorial for user role
    tutorial = get_tutorial_for_role(user.role)
    
    # Get steps and mark completed ones
    steps = tutorial['steps']
    completed_steps = onboarding.completed_steps
    
    for step in steps:
        step['completed'] = step['id'] in completed_steps
    
    # Create an event for viewing the tutorial
    event = OnboardingEvent(
        onboarding_id=onboarding.id,
        event_type='tutorial_viewed'
    )
    db.session.add(event)
    db.session.commit()
    
    return render_template(
        'onboarding/tutorial.html',
        tutorial=tutorial,
        steps=steps,
        user=user,
        progress=onboarding.progress
    )

@onboarding_bp.route('/step/<step_id>')
def tutorial_step(step_id):
    """Display a specific tutorial step."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the onboarding tutorial.', 'warning')
        return redirect(url_for('login'))
    
    # Get user onboarding record
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    # If no onboarding record, redirect to start
    if not onboarding:
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # If onboarding is completed, redirect to completion page
    if onboarding.is_completed:
        return redirect(url_for('onboarding_bp.onboarding_complete'))
    
    # Get tutorial for user role
    tutorial = get_tutorial_for_role(user.role)
    
    # Find the requested step
    step = None
    next_step = None
    prev_step = None
    step_index = -1
    
    for i, s in enumerate(tutorial['steps']):
        if s['id'] == step_id:
            step = s
            step_index = i
            break
    
    # If step not found, redirect to first step
    if not step:
        return redirect(url_for('onboarding_bp.tutorial_step', step_id=tutorial['steps'][0]['id']))
    
    # Find next and previous steps
    if step_index > 0:
        prev_step = tutorial['steps'][step_index - 1]
    
    if step_index < len(tutorial['steps']) - 1:
        next_step = tutorial['steps'][step_index + 1]
    
    # Update current step
    onboarding.current_step = step_id
    db.session.commit()
    
    # Create an event for viewing this step
    event = OnboardingEvent(
        onboarding_id=onboarding.id,
        event_type='step_viewed',
        step_id=step_id
    )
    db.session.add(event)
    db.session.commit()
    
    # Get completed steps
    completed_steps = onboarding.completed_steps
    
    return render_template(
        'onboarding/step.html',
        tutorial=tutorial,
        step=step,
        next_step=next_step,
        prev_step=prev_step,
        user=user,
        progress=onboarding.progress,
        completed=step['id'] in completed_steps,
        completed_steps=completed_steps
    )

@onboarding_bp.route('/complete_step/<step_id>', methods=['POST'])
def complete_step(step_id):
    """Mark a step as completed."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Get user onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        return jsonify({'success': False, 'error': 'Onboarding record not found'}), 404
    
    # Mark step as completed
    onboarding.mark_step_completed(step_id)
    
    # Update last activity
    onboarding.last_activity_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'progress': onboarding.progress,
        'completed_steps': onboarding.completed_steps
    })

@onboarding_bp.route('/complete', methods=['GET', 'POST'])
def onboarding_complete():
    """Onboarding completion page."""
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in to access the onboarding tutorial.', 'warning')
        return redirect(url_for('login'))
    
    # Get user onboarding record
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('dashboard'))
    
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    # If no onboarding record, redirect to start
    if not onboarding:
        return redirect(url_for('onboarding_bp.onboarding_home'))
    
    # Handle POST request to complete onboarding
    if request.method == 'POST':
        onboarding.complete_onboarding()
        db.session.commit()
        flash('Onboarding completed successfully!', 'success')
        return redirect(url_for('dashboard'))
    
    # Get tutorial for user role
    tutorial = get_tutorial_for_role(user.role)
    
    # Mark as completed if all steps are done
    completed_steps = onboarding.completed_steps
    all_completed = len(completed_steps) == len(tutorial['steps'])
    
    # If not all steps are completed, redirect to tutorial
    if not all_completed and not onboarding.is_completed:
        flash('Please complete all steps before finishing the tutorial.', 'warning')
        return redirect(url_for('onboarding_bp.tutorial_home'))
    
    return render_template(
        'onboarding/completion.html',
        tutorial=tutorial,
        user=user,
        steps_completed=len(completed_steps),
        total_steps=len(tutorial['steps'])
    )

@onboarding_bp.route('/skip', methods=['POST'])
def skip_onboarding():
    """Skip the onboarding process."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    # Get user onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        # Create a new record marked as completed
        onboarding = UserOnboarding(
            user_id=user_id,
            is_completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(onboarding)
    else:
        # Mark existing record as completed
        onboarding.is_completed = True
        onboarding.completed_at = datetime.utcnow()
    
    # Create an event for skipping onboarding
    event = OnboardingEvent(
        onboarding_id=onboarding.id,
        event_type='onboarding_skipped'
    )
    db.session.add(event)
    db.session.commit()
    
    return jsonify({'success': True, 'redirect': url_for('dashboard')})

@onboarding_bp.route('/status')
def onboarding_status():
    """Get the onboarding status for the current user."""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user onboarding record
    onboarding = UserOnboarding.query.filter_by(user_id=user_id).first()
    
    if not onboarding:
        return jsonify({
            'started': False,
            'completed': False,
            'progress': 0,
            'current_step': None
        })
    
    return jsonify({
        'started': True,
        'completed': onboarding.is_completed,
        'progress': onboarding.progress,
        'current_step': onboarding.current_step,
        'completed_steps': onboarding.completed_steps
    })