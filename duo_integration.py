"""
TerraFusion Platform - Duo Security MFA Integration

This module provides comprehensive Duo Security Multi-Factor Authentication
integration for the TerraFusion Platform, ensuring compliance with county
security policies and enterprise-grade authentication requirements.
"""

import os
import time
import json
import logging
from typing import Dict, Optional, Tuple, Any
from functools import wraps
from datetime import datetime, timedelta

import duo_client
from flask import request, session, redirect, url_for, render_template, jsonify, current_app
from werkzeug.security import check_password_hash

# Configure logging
logger = logging.getLogger(__name__)

class DuoMFAManager:
    """
    Duo Security MFA Manager for TerraFusion Platform.
    
    Handles multi-factor authentication integration with Duo Security
    for admin portal access, vendor API authentication, and service
    account management.
    """
    
    def __init__(self, app=None):
        """
        Initialize Duo MFA Manager.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        self.duo_admin_client = None
        self.duo_auth_client = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """
        Initialize Duo integration with Flask application.
        
        Args:
            app: Flask application instance
        """
        self.app = app
        
        # Load Duo configuration from environment
        self.duo_config = {
            'admin_integration_key': os.environ.get('DUO_ADMIN_IKEY'),
            'admin_secret_key': os.environ.get('DUO_ADMIN_SKEY'),
            'admin_api_hostname': os.environ.get('DUO_ADMIN_API_HOST'),
            'auth_integration_key': os.environ.get('DUO_AUTH_IKEY'),
            'auth_secret_key': os.environ.get('DUO_AUTH_SKEY'),
            'auth_api_hostname': os.environ.get('DUO_AUTH_API_HOST'),
            'application_key': os.environ.get('DUO_APPLICATION_KEY', app.secret_key)
        }
        
        # Initialize Duo clients
        self._initialize_duo_clients()
        
        # Configure session settings for MFA
        app.config.update({
            'DUO_MFA_TIMEOUT': int(os.environ.get('DUO_MFA_TIMEOUT', 300)),  # 5 minutes
            'DUO_SESSION_TIMEOUT': int(os.environ.get('DUO_SESSION_TIMEOUT', 900)),  # 15 minutes
            'DUO_BYPASS_LOCALHOST': os.environ.get('DUO_BYPASS_LOCALHOST', 'false').lower() == 'true'
        })
    
    def _initialize_duo_clients(self):
        """Initialize Duo API clients for admin and auth operations."""
        try:
            # Initialize Admin API client for user management
            if all([self.duo_config['admin_integration_key'],
                   self.duo_config['admin_secret_key'],
                   self.duo_config['admin_api_hostname']]):
                self.duo_admin_client = duo_client.Client(
                    integration_key=self.duo_config['admin_integration_key'],
                    secret_key=self.duo_config['admin_secret_key'],
                    api_hostname=self.duo_config['admin_api_hostname']
                )
                logger.info("Duo Admin API client initialized successfully")
            
            # Initialize Auth API client for authentication
            if all([self.duo_config['auth_integration_key'],
                   self.duo_config['auth_secret_key'],
                   self.duo_config['auth_api_hostname']]):
                self.duo_auth_client = duo_client.Client(
                    integration_key=self.duo_config['auth_integration_key'],
                    secret_key=self.duo_config['auth_secret_key'],
                    api_hostname=self.duo_config['auth_api_hostname']
                )
                logger.info("Duo Auth API client initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize Duo clients: {str(e)}")
            if not self.app.config.get('DUO_BYPASS_LOCALHOST', False):
                raise
    
    def is_duo_configured(self) -> bool:
        """
        Check if Duo is properly configured.
        
        Returns:
            bool: True if Duo is configured and ready
        """
        return (self.duo_auth_client is not None and 
                self.duo_admin_client is not None)
    
    def create_duo_auth_request(self, username: str, client_ip: str = None) -> Dict[str, Any]:
        """
        Create a Duo authentication request.
        
        Args:
            username: Username for authentication
            client_ip: Client IP address (optional)
            
        Returns:
            Dictionary containing auth request details
        """
        if not self.duo_auth_client:
            raise ValueError("Duo Auth client not initialized")
        
        try:
            # Create authentication request
            auth_request = {
                'username': username,
                'factor': 'auto',  # Let Duo decide the best factor
                'device': 'auto',  # Use user's primary device
                'pushinfo': f'TerraFusion Platform login from {client_ip or "unknown IP"}',
                'type': 'request'
            }
            
            # Add optional parameters
            if client_ip:
                auth_request['ipaddr'] = client_ip
            
            # Create preauth request to check user status
            preauth_response = self.duo_auth_client.preauth(
                username=username,
                ipaddr=client_ip
            )
            
            if preauth_response['result'] == 'auth':
                # User is enrolled and ready for MFA
                auth_request['txid'] = self._generate_transaction_id()
                auth_request['status'] = 'pending'
                
                # Store request in session for verification
                session['duo_auth_request'] = auth_request
                session['duo_auth_timestamp'] = time.time()
                
                return {
                    'success': True,
                    'auth_request': auth_request,
                    'message': 'MFA request created successfully'
                }
            else:
                # User is not enrolled or denied
                return {
                    'success': False,
                    'error': preauth_response.get('status_msg', 'User not enrolled in Duo MFA'),
                    'result': preauth_response['result']
                }
                
        except Exception as e:
            logger.error(f"Failed to create Duo auth request: {str(e)}")
            return {
                'success': False,
                'error': f'MFA request failed: {str(e)}'
            }
    
    def verify_duo_auth(self, username: str, passcode: str = None) -> Dict[str, Any]:
        """
        Verify Duo authentication response.
        
        Args:
            username: Username being authenticated
            passcode: Optional passcode for manual verification
            
        Returns:
            Dictionary containing verification results
        """
        if not self.duo_auth_client:
            raise ValueError("Duo Auth client not initialized")
        
        # Check for stored auth request
        auth_request = session.get('duo_auth_request')
        auth_timestamp = session.get('duo_auth_timestamp')
        
        if not auth_request or not auth_timestamp:
            return {
                'success': False,
                'error': 'No pending MFA request found'
            }
        
        # Check timeout
        if time.time() - auth_timestamp > self.app.config['DUO_MFA_TIMEOUT']:
            session.pop('duo_auth_request', None)
            session.pop('duo_auth_timestamp', None)
            return {
                'success': False,
                'error': 'MFA request expired'
            }
        
        try:
            # Perform authentication
            auth_params = {
                'username': username,
                'factor': 'auto',
                'device': 'auto'
            }
            
            if passcode:
                auth_params['factor'] = 'passcode'
                auth_params['passcode'] = passcode
            
            auth_response = self.duo_auth_client.auth(**auth_params)
            
            if auth_response['result'] == 'allow':
                # Authentication successful
                session.pop('duo_auth_request', None)
                session.pop('duo_auth_timestamp', None)
                
                # Set MFA session
                session['duo_authenticated'] = True
                session['duo_auth_time'] = time.time()
                session['duo_username'] = username
                
                # Log successful authentication
                self._log_mfa_event(username, 'success', 'Authentication successful')
                
                return {
                    'success': True,
                    'message': 'MFA authentication successful',
                    'auth_response': auth_response
                }
            else:
                # Authentication failed
                self._log_mfa_event(username, 'failure', 
                                  auth_response.get('status_msg', 'Authentication denied'))
                
                return {
                    'success': False,
                    'error': auth_response.get('status_msg', 'Authentication denied'),
                    'result': auth_response['result']
                }
                
        except Exception as e:
            logger.error(f"Failed to verify Duo auth: {str(e)}")
            self._log_mfa_event(username, 'error', f'Verification error: {str(e)}')
            return {
                'success': False,
                'error': f'MFA verification failed: {str(e)}'
            }
    
    def check_mfa_session(self, username: str = None) -> bool:
        """
        Check if current session has valid MFA authentication.
        
        Args:
            username: Optional username to verify session ownership
            
        Returns:
            bool: True if session has valid MFA
        """
        if not session.get('duo_authenticated'):
            return False
        
        auth_time = session.get('duo_auth_time')
        if not auth_time:
            return False
        
        # Check session timeout
        if time.time() - auth_time > self.app.config['DUO_SESSION_TIMEOUT']:
            self.clear_mfa_session()
            return False
        
        # Check username if provided
        if username and session.get('duo_username') != username:
            return False
        
        return True
    
    def clear_mfa_session(self):
        """Clear MFA session data."""
        session.pop('duo_authenticated', None)
        session.pop('duo_auth_time', None)
        session.pop('duo_username', None)
        session.pop('duo_auth_request', None)
        session.pop('duo_auth_timestamp', None)
    
    def get_user_devices(self, username: str) -> Dict[str, Any]:
        """
        Get Duo devices for a user.
        
        Args:
            username: Username to query
            
        Returns:
            Dictionary containing user devices
        """
        if not self.duo_admin_client:
            return {'success': False, 'error': 'Duo Admin client not available'}
        
        try:
            # Get user information
            users = self.duo_admin_client.get_users(username=username)
            if not users:
                return {'success': False, 'error': 'User not found in Duo'}
            
            user_id = users[0]['user_id']
            
            # Get user's devices
            phones = self.duo_admin_client.get_user_phones(user_id)
            tokens = self.duo_admin_client.get_user_tokens(user_id)
            
            return {
                'success': True,
                'devices': {
                    'phones': phones,
                    'tokens': tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get user devices: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID for MFA requests."""
        import uuid
        return f"tf-{int(time.time())}-{str(uuid.uuid4())[:8]}"
    
    def _log_mfa_event(self, username: str, event_type: str, message: str):
        """
        Log MFA events for audit purposes.
        
        Args:
            username: Username involved in the event
            event_type: Type of event (success, failure, error)
            message: Event description
        """
        try:
            from app import db
            from models import AuditLog
            
            audit_entry = AuditLog(
                user_id=username,
                action=f'duo_mfa_{event_type}',
                resource_type='authentication',
                resource_id='duo_mfa',
                details=json.dumps({
                    'event_type': event_type,
                    'message': message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'ip_address': request.remote_addr if request else None
                }),
                ip_address=request.remote_addr if request else None,
                user_agent=request.user_agent.string if request else None,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(audit_entry)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to log MFA event: {str(e)}")

# Global instance
duo_mfa = DuoMFAManager()

def require_mfa(bypass_localhost=False):
    """
    Decorator to require MFA authentication for routes.
    
    Args:
        bypass_localhost: Whether to bypass MFA for localhost connections
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if Duo is configured
            if not duo_mfa.is_duo_configured():
                if current_app.config.get('DUO_BYPASS_LOCALHOST', False):
                    logger.warning("Duo MFA not configured - bypassing for development")
                    return f(*args, **kwargs)
                else:
                    return jsonify({'error': 'MFA not properly configured'}), 500
            
            # Check for localhost bypass
            if bypass_localhost and request.remote_addr in ['127.0.0.1', '::1']:
                return f(*args, **kwargs)
            
            # Check current MFA session
            if not duo_mfa.check_mfa_session():
                if request.is_json:
                    return jsonify({'error': 'MFA authentication required'}), 401
                else:
                    return redirect(url_for('mfa_login', next=request.url))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def init_duo_integration(app):
    """
    Initialize Duo MFA integration with Flask application.
    
    Args:
        app: Flask application instance
    """
    duo_mfa.init_app(app)
    
    # Register MFA routes
    register_mfa_routes(app)
    
    logger.info("Duo MFA integration initialized")

def register_mfa_routes(app):
    """
    Register MFA-related routes with the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/mfa/login', methods=['GET', 'POST'])
    def mfa_login():
        """MFA login page and handling."""
        if request.method == 'GET':
            return render_template('mfa/login.html')
        
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return render_template('mfa/login.html', 
                                 error='Username and password required')
        
        # Verify primary credentials first
        from models import User
        user = User.query.filter_by(username=username).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            return render_template('mfa/login.html', 
                                 error='Invalid username or password')
        
        # Create Duo MFA request
        auth_result = duo_mfa.create_duo_auth_request(
            username=username,
            client_ip=request.remote_addr
        )
        
        if auth_result['success']:
            return render_template('mfa/challenge.html', 
                                 username=username,
                                 auth_request=auth_result['auth_request'])
        else:
            return render_template('mfa/login.html', 
                                 error=auth_result['error'])
    
    @app.route('/mfa/verify', methods=['POST'])
    def mfa_verify():
        """Verify MFA challenge response."""
        username = request.form.get('username')
        passcode = request.form.get('passcode')
        
        if not username:
            return jsonify({'success': False, 'error': 'Username required'}), 400
        
        # Verify MFA
        verification_result = duo_mfa.verify_duo_auth(
            username=username,
            passcode=passcode
        )
        
        if verification_result['success']:
            # Set user session
            session['user_id'] = username
            session['authenticated'] = True
            
            # Redirect to originally requested page
            next_page = request.args.get('next') or url_for('dashboard')
            return jsonify({
                'success': True,
                'redirect': next_page
            })
        else:
            return jsonify({
                'success': False,
                'error': verification_result['error']
            }), 401
    
    @app.route('/mfa/logout', methods=['POST'])
    def mfa_logout():
        """Logout and clear MFA session."""
        duo_mfa.clear_mfa_session()
        session.clear()
        return redirect(url_for('mfa_login'))
    
    @app.route('/mfa/status')
    def mfa_status():
        """Check MFA configuration and session status."""
        return jsonify({
            'configured': duo_mfa.is_duo_configured(),
            'authenticated': duo_mfa.check_mfa_session(),
            'username': session.get('duo_username'),
            'auth_time': session.get('duo_auth_time')
        })