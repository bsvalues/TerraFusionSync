"""
TerraFusion Platform - Authentication Module

This module provides authentication functionality for the TerraFusion Platform.
"""
import logging
from typing import Dict, Any, Optional, Union

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash

from auth.models import User
from auth.audit import create_audit_log

logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth', template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate form data
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('auth/login.html', error='Username and password are required')
        
        # Get user from database
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password', 'error')
            create_audit_log(
                event_type='login_failed',
                resource_type='user',
                description=f'Failed login attempt for user {username}',
                username=username,
                severity='warning'
            )
            return render_template('auth/login.html', error='Invalid username or password')
        
        # Check if user is active
        if not user.active:
            flash('Account is disabled', 'error')
            create_audit_log(
                event_type='login_failed',
                resource_type='user',
                resource_id=str(user.id),
                description=f'Login attempt for disabled account: {username}',
                username=username,
                severity='warning'
            )
            return render_template('auth/login.html', error='Account is disabled')
        
        # Login successful, store user in session
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['county_ids'] = user.county_ids
        session.permanent = True
        
        # Update last login timestamp
        from app import db
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create audit log entry
        create_audit_log(
            event_type='login_success',
            resource_type='user',
            resource_id=str(user.id),
            description=f'User {username} logged in successfully',
            user_id=str(user.id),
            username=user.username,
            severity='info'
        )
        
        # Redirect to next page or dashboard
        next_page = request.args.get('next') or url_for('dashboard')
        flash(f'Welcome back, {user.display_name or user.username}!', 'success')
        return redirect(next_page)
    
    # GET request - display login form
    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    user_id = session.get('user_id')
    username = session.get('username')
    
    if user_id and username:
        # Create audit log entry
        create_audit_log(
            event_type='logout',
            resource_type='user',
            resource_id=str(user_id),
            description=f'User {username} logged out',
            user_id=str(user_id),
            username=username,
            severity='info'
        )
    
    # Clear session
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login_page'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    # This is typically only used in development or for initial admin setup
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        display_name = request.form.get('display_name') or f"{first_name} {last_name}".strip()
        
        # Validate form data
        if not username or not password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/register.html', 
                                  error='All fields are required',
                                  username=username,
                                  email=email,
                                  first_name=first_name,
                                  last_name=last_name,
                                  display_name=display_name)
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('auth/register.html', 
                                  error='Passwords do not match',
                                  username=username,
                                  email=email,
                                  first_name=first_name,
                                  last_name=last_name,
                                  display_name=display_name)
        
        # Check if username or email is already taken
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html', 
                                  error='Username already exists',
                                  email=email,
                                  first_name=first_name,
                                  last_name=last_name,
                                  display_name=display_name)
        
        if email and User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/register.html', 
                                  error='Email already exists',
                                  username=username,
                                  first_name=first_name,
                                  last_name=last_name,
                                  display_name=display_name)
        
        # Create new user
        from app import db
        
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            display_name=display_name,
            role='Staff',  # Default role
            active=True,
            auth_type='local',
            county_ids=[]  # No counties by default
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Create audit log entry
            create_audit_log(
                event_type='user_created',
                resource_type='user',
                resource_id=str(new_user.id),
                description=f'User {username} created',
                severity='info'
            )
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating user: {str(e)}")
            flash('An error occurred during registration', 'error')
            return render_template('auth/register.html', 
                                  error='An error occurred during registration',
                                  username=username,
                                  email=email,
                                  first_name=first_name,
                                  last_name=last_name,
                                  display_name=display_name)
    
    # GET request - display registration form
    return render_template('auth/register.html')


@auth_bp.route('/profile')
def profile():
    """Display user profile."""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to view your profile', 'error')
        return redirect(url_for('auth.login', next=request.path))
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/profile.html', user=user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    """Edit user profile."""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to edit your profile', 'error')
        return redirect(url_for('auth.login', next=request.path))
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        display_name = request.form.get('display_name')
        email = request.form.get('email')
        
        # Validate email if changed
        if email != user.email and User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return render_template('auth/edit_profile.html', user=user, error='Email already exists')
        
        # Update user
        from app import db
        
        # Store previous state for audit log
        previous_state = user.to_dict()
        
        # Update user fields
        user.first_name = first_name
        user.last_name = last_name
        user.display_name = display_name
        user.email = email
        
        try:
            db.session.commit()
            
            # Create audit log entry
            create_audit_log(
                event_type='profile_updated',
                resource_type='user',
                resource_id=str(user.id),
                description=f'User {user.username} updated profile',
                user_id=str(user.id),
                username=user.username,
                details={
                    'previous': previous_state,
                    'new': user.to_dict()
                },
                severity='info'
            )
            
            flash('Profile updated successfully', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating profile: {str(e)}")
            flash('An error occurred while updating profile', 'error')
            return render_template('auth/edit_profile.html', user=user, error='An error occurred')
    
    # GET request - display edit form
    return render_template('auth/edit_profile.html', user=user)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change user password."""
    # Check if user is logged in
    if 'user_id' not in session:
        flash('Please log in to change your password', 'error')
        return redirect(url_for('auth.login', next=request.path))
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Get form data
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate form data
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'error')
            return render_template('auth/change_password.html', error='All fields are required')
        
        if not check_password_hash(user.password_hash, current_password):
            flash('Current password is incorrect', 'error')
            create_audit_log(
                event_type='password_change_failed',
                resource_type='user',
                resource_id=str(user.id),
                description=f'Failed password change attempt for user {user.username}: incorrect current password',
                user_id=str(user.id),
                username=user.username,
                severity='warning'
            )
            return render_template('auth/change_password.html', error='Current password is incorrect')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return render_template('auth/change_password.html', error='New passwords do not match')
        
        # Update password
        from app import db
        
        user.password_hash = generate_password_hash(new_password)
        
        try:
            db.session.commit()
            
            # Create audit log entry
            create_audit_log(
                event_type='password_changed',
                resource_type='user',
                resource_id=str(user.id),
                description=f'User {user.username} changed password',
                user_id=str(user.id),
                username=user.username,
                severity='info'
            )
            
            flash('Password changed successfully', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password: {str(e)}")
            flash('An error occurred while changing password', 'error')
            return render_template('auth/change_password.html', error='An error occurred')
    
    # GET request - display change password form
    return render_template('auth/change_password.html')


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current user from the session."""
    if 'user_id' not in session:
        return None
    
    # Get user from database
    user = User.query.get(session['user_id'])
    if not user:
        return None
    
    return user.to_dict()


def get_user_counties() -> List[str]:
    """Get the counties the current user has access to."""
    if 'county_ids' not in session:
        return []
    
    return session['county_ids'] or []


def is_admin() -> bool:
    """Check if the current user is an admin."""
    return session.get('role') == 'ITAdmin'


def requires_auth(f):
    """Decorator to require authentication for routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # Store the next URL for redirection after login
            session['next'] = request.path
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.path))
        
        # Set user in Flask's g object for easy access
        g.user_id = session['user_id']
        g.username = session['username']
        g.role = session['role']
        g.county_ids = session.get('county_ids', [])
        
        return f(*args, **kwargs)
    
    return decorated


def requires_role(role):
    """Decorator to require a specific role for routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # Store the next URL for redirection after login
            session['next'] = request.path
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.path))
        
        if session.get('role') != role:
            flash('You do not have permission to access this page', 'error')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    
    return decorated


def requires_permissions(permissions):
    """Decorator to require specific permissions for routes."""
    from functools import wraps
    
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            # Store the next URL for redirection after login
            session['next'] = request.path
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login', next=request.path))
        
        # Get user from database
        user = User.query.get(session['user_id'])
        if not user:
            flash('User not found', 'error')
            return redirect(url_for('auth.login'))
        
        # Check permissions - this would typically use a UserPermissions model
        # For now, we'll use a simple role-based approach
        
        # Admins have all permissions
        if user.role == 'ITAdmin':
            return f(*args, **kwargs)
        
        # Check for required permissions based on role
        role_permissions = {
            'Assessor': ['run_sync', 'view_sync', 'run_validation', 'view_validation', 
                         'run_reporting', 'view_reporting', 'run_gis_export', 'view_gis_export',
                         'run_market_analysis', 'view_market_analysis'],
            'Staff': ['view_sync', 'view_validation', 'view_reporting', 'view_gis_export',
                      'view_market_analysis'],
            'Auditor': ['view_audit_logs', 'view_reporting', 'view_validation']
        }
        
        user_permissions = role_permissions.get(user.role, [])
        
        # Check if user has all required permissions
        if isinstance(permissions, list):
            if not all(perm in user_permissions for perm in permissions):
                flash('You do not have the required permissions', 'error')
                return redirect(url_for('dashboard'))
        else:
            if permissions not in user_permissions:
                flash('You do not have the required permissions', 'error')
                return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    
    return decorated