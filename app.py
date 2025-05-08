"""
TerraFusion SyncService API Gateway

This module provides the main Flask application that serves as the API Gateway
for the TerraFusion SyncService platform.
"""
import os
import json
import logging
import requests
import subprocess
import threading
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin
from functools import wraps

from flask import Flask, jsonify, request, render_template, redirect, url_for, Response, session, flash

# Configure logging first to avoid "logger not defined" errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create and initialize the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "a secret key"

# Configure ProxyFix for running behind Replit's proxy
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

# Configure session cookies to ensure they're saved correctly
app.config['SESSION_COOKIE_SECURE'] = True  # Enable secure cookies for HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds
app.config['SESSION_TYPE'] = 'filesystem'  # Store session data on the filesystem instead of just cookies
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True  # Sign the session cookie for additional security

# Initialize Flask-Session
from flask_session import Session
Session(app)

# Create session directory if it doesn't exist
os.makedirs('./flask_session', exist_ok=True)

# Import database models
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database with the Flask app
db.init_app(app)

# Import database module and share our db instance with it
import apps.backend.database
apps.backend.database.set_shared_db(db)

# Import models
from apps.backend.models import SyncPair, SyncOperation, AuditEntry, SystemMetrics

# Import system monitor utility if available
try:
    from manual_fix_system_monitoring import SafeSystemMonitor, get_safe_system_info
    SAFE_MONITOR_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Using SafeSystemMonitor for API Gateway monitoring")
except ImportError:
    SAFE_MONITOR_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("SafeSystemMonitor not available for API Gateway, using simple metrics")

# Metrics functionality uses a simplified implementation to avoid recursion errors
METRICS_AVAILABLE = True
# Configure logging first to avoid "logger not defined" errors
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import authentication module
try:
    from apps.backend.auth import requires_auth, init_auth_routes, get_current_user
    CUSTOM_AUTH_AVAILABLE = True
    logger.info("Using custom authentication module")
except ImportError:
    # Provide fallback if auth module isn't available
    logger.warning("Auth module not available, using fallback implementation")
    CUSTOM_AUTH_AVAILABLE = False
    
    def requires_auth(f):
        """Fallback auth decorator that requires authentication and redirects to login page."""
        @wraps(f)
        def decorated(*args, **kwargs):
            logger.debug(f"requires_auth checking authentication for {request.path}")
            logger.debug(f"Session data in requires_auth: {session}")
            logger.debug(f"Request cookies: {request.cookies}")
            
            # Check if authenticated in session
            if 'token' not in session:
                logger.debug("Token not in session, redirecting to login")
                # Store the requested URL in session for redirect after login
                session['next'] = request.path
                
                # Always redirect to login page if not authenticated
                # Regardless of whether it's an API or browser request
                flash('Authentication required to access this page', 'error')
                return redirect(url_for('login_page', next=request.path))
            
            logger.debug(f"User is authenticated, proceeding to {request.path}")
            return f(*args, **kwargs)
        return decorated
    
    def init_auth_routes(app):
        """Fallback auth routes initializer."""
        # Register auth blueprint
        from flask import Blueprint
        auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')
        
        @auth_bp.route('/login', methods=['GET', 'POST'])
        def login():
            """
            Handle login for API Gateway.
            GET requests show login form, POST requests handle login.
            """
            if request.method == 'POST':
                if request.content_type == 'application/json':
                    # Handle JSON login for API
                    data = request.json
                    username = data.get('username')
                    password = data.get('password')
                    
                    if not username or not password:
                        return jsonify({'success': False, 'error': 'Username and password required'}), 400
                    
                    # Simple authentication for development
                    # In production, this would validate against actual credentials
                    
                    # Create user data
                    user_data = {
                        'id': f"user-{username}",
                        'name': username,
                        'email': f"{username}@example.com",
                        'roles': ['user']
                    }
                    
                    # Create expiration time - 24 hours from now
                    expiry = datetime.utcnow() + timedelta(hours=24)
                    
                    # Create token payload
                    payload = {
                        'sub': user_data['id'],
                        'name': user_data['name'],
                        'email': user_data['email'],
                        'roles': user_data['roles'],
                        'exp': expiry
                    }
                    
                    # Create token
                    import jwt
                    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    
                    # Store in session
                    session['token'] = token
                    session['user'] = user_data
                    
                    return jsonify({
                        'success': True,
                        'token': token,
                        'user': user_data
                    })
                else:
                    # Handle form login
                    username = request.form.get('username')
                    password = request.form.get('password')
                    next_param = request.form.get('next')
                    
                    if not username or not password:
                        flash('Username and password required', 'error')
                        return redirect(url_for('login_page', next=next_param))
                    
                    # Create user data
                    user_data = {
                        'id': f"user-{username}",
                        'name': username,
                        'email': f"{username}@example.com",
                        'roles': ['user']
                    }
                    
                    # Create expiration time - 24 hours from now
                    expiry = datetime.utcnow() + timedelta(hours=24)
                    
                    # Create token payload
                    payload = {
                        'sub': user_data['id'],
                        'name': user_data['name'],
                        'email': user_data['email'],
                        'roles': user_data['roles'],
                        'exp': expiry
                    }
                    
                    # Create token
                    import jwt
                    token = jwt.encode(payload, app.secret_key, algorithm='HS256')
                    
                    # Store in session
                    session['token'] = token
                    session['user'] = user_data
                    
                    # Get next URL from form parameter, URL param, session, or default to dashboard
                    next_url = next_param or request.args.get('next') or session.get('next') or url_for('dashboard')
                    
                    # Clean up session next if it exists
                    if 'next' in session:
                        session.pop('next', None)
                    
                    # Redirect to appropriate page
                    return redirect(next_url)
            else:
                # For GET requests, redirect to login page
                return redirect(url_for('login_page'))
        
        @auth_bp.route('/logout', methods=['GET', 'POST'])
        def logout():
            """Handle logout."""
            # Clear session
            session.clear()
            
            # Redirect to home page or return JSON response
            if request.content_type == 'application/json':
                return jsonify({'success': True, 'message': 'Logged out successfully'})
            else:
                flash('You have been logged out', 'info')
                return redirect(url_for('root'))
                
        app.register_blueprint(auth_bp)
        
    def get_current_user():
        """Fallback current user function."""
        return session.get('user')

# Import API blueprints
try:
    SYNC_API_AVAILABLE = True
    logger.info("Sync operations API module available")
except ImportError:
    SYNC_API_AVAILABLE = False
    logging.warning("Sync operations API module not available")

# Initialize authentication routes (including County RBAC if available)
try:
    from apps.backend.auth import init_auth_routes, COUNTY_RBAC_AVAILABLE
    init_auth_routes(app)
    if COUNTY_RBAC_AVAILABLE:
        logger.info("County RBAC authentication initialized")
    else:
        logger.warning("County RBAC not available")
except ImportError:
    logger.warning("Auth module not available, using fallback authentication")
    # Fallback auth initialization would go here

# Import and register WebSocket proxy
try:
    from proxy_websocket import register_websocket_proxy
    register_websocket_proxy(app)
    logger.info("WebSocket proxy registered successfully")
except ImportError as e:
    logger.warning(f"WebSocket proxy not available: {e}")

# Register API blueprints
try:
    from apps.backend.api.sync_operations import sync_bp
    app.register_blueprint(sync_bp)
    logger.info("Registered sync operations API blueprint")
except ImportError:
    logger.warning("Sync operations API blueprint not available")

# Register validation API blueprint
try:
    from apps.backend.api import validation_bp
    app.register_blueprint(validation_bp)
    logger.info("Registered validation API blueprint")
except ImportError:
    logger.warning("Validation API blueprint not available")

# Register rollback API blueprint for ITAdmin functionality
try:
    from apps.backend.api.rollback import rollback_bp
    app.register_blueprint(rollback_bp)
    logger.info("Registered rollback API blueprint for ITAdmin")
except ImportError:
    logger.warning("Rollback API blueprint not available")

# Register onboarding module for interactive tutorials
try:
    from apps.backend.onboarding import onboarding_bp
    app.register_blueprint(onboarding_bp)
    logger.info("Registered onboarding module for interactive tutorials")
except ImportError as e:
    logger.warning(f"Onboarding module not available: {e}")

# Add route for validation dashboard
@app.route('/validation', methods=['GET'])
def validation_dashboard():
    """Display the data validation dashboard."""
    return render_template('validation_dashboard.html')

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# Create a monitoring instance if available
if SAFE_MONITOR_AVAILABLE:
    api_gateway_monitor = SafeSystemMonitor()
    logger.info("Created SafeSystemMonitor instance for API Gateway")
else:
    api_gateway_monitor = None
    logger.warning("No monitoring instance available for API Gateway")

# Variables for metrics collection and service health checks
last_metrics_collection_time = 0
last_service_health_check_time = 0
METRICS_COLLECTION_INTERVAL = 60  # seconds
SERVICE_HEALTH_CHECK_INTERVAL = 300  # seconds (5 minutes)

# Create a middleware to trigger metrics collection and service health checks periodically
@app.before_request
def before_request_middleware():
    global last_metrics_collection_time, last_service_health_check_time
    current_time = time.time()
    
    # If it's been more than METRICS_COLLECTION_INTERVAL seconds since the last collection
    if current_time - last_metrics_collection_time > METRICS_COLLECTION_INTERVAL:
        # Run this in a separate thread to avoid blocking the request
        thread = threading.Thread(target=lambda: collect_metrics_safely())
        thread.daemon = True
        thread.start()
        last_metrics_collection_time = current_time
        
    # If it's been more than SERVICE_HEALTH_CHECK_INTERVAL seconds since the last health check
    if current_time - last_service_health_check_time > SERVICE_HEALTH_CHECK_INTERVAL:
        # Run the service health check in a separate thread with app context
        def run_health_check_with_context():
            with app.app_context():
                check_and_ensure_service_health()
                
        thread = threading.Thread(target=run_health_check_with_context)
        thread.daemon = True
        thread.start()
        last_service_health_check_time = current_time

def collect_metrics_safely():
    """Safely collect metrics without affecting the main application."""
    max_retries = 3
    retry_delay = 2  # seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            if check_syncservice_status():
                logger.info(f"Collecting metrics from SyncService (middleware trigger, attempt {attempt}/{max_retries})")
                result = collect_syncservice_metrics()
                if result:
                    logger.info("Successfully collected metrics through middleware")
                    # Create an audit entry for the retry if it wasn't the first attempt
                    if attempt > 1:
                        with app.app_context():
                            create_audit_log(
                                event_type="metrics_collection_retry_success",
                                resource_type="system_metrics",
                                description=f"Successfully collected metrics after {attempt} attempts",
                                severity="info"
                            )
                    return True
                else:
                    logger.warning(f"Failed to collect metrics on attempt {attempt}/{max_retries}")
            else:
                logger.warning(f"SyncService not available for middleware metrics collection (attempt {attempt}/{max_retries})")
            
            # If we've reached the maximum number of retries, give up
            if attempt >= max_retries:
                logger.error(f"Failed to collect metrics after {max_retries} attempts")
                # Create an audit entry for the failure
                with app.app_context():
                    try:
                        create_audit_log(
                            event_type="metrics_collection_failed",
                            resource_type="system_metrics",
                            description=f"Failed to collect metrics after {max_retries} attempts",
                            severity="warning"
                        )
                    except Exception as e:
                        logger.error(f"Failed to create audit log for metrics collection failure: {str(e)}")
                return False
            
            # Wait before retrying
            time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Error in metrics collection attempt {attempt}/{max_retries}: {str(e)}")
            
            # If we've reached the maximum number of retries, give up
            if attempt >= max_retries:
                # Create an audit entry for the exception
                with app.app_context():
                    try:
                        create_audit_log(
                            event_type="metrics_collection_error",
                            resource_type="system_metrics",
                            description=f"Error collecting metrics after {attempt} attempts: {str(e)}",
                            severity="error"
                        )
                    except Exception as log_error:
                        logger.error(f"Failed to create audit log for metrics collection error: {str(log_error)}")
                return False
            
            # Wait before retrying
            time.sleep(retry_delay)

# Function to collect metrics from syncservice
def collect_syncservice_metrics():
    """
    Collect metrics from SyncService and store them in the database.
    This function is designed to be called periodically.
    
    Returns:
        Dictionary with collected metrics or None if collection failed
    """
    if not check_syncservice_status():
        logger.warning("SyncService is not available for metrics collection")
        return None
    
    try:
        # Fetch metrics from the SyncService's metrics endpoint
        response = requests.get(f"{SYNCSERVICE_BASE_URL}/metrics", timeout=5)
        
        if response.status_code != 200:
            logger.error(f"Failed to get metrics from SyncService: HTTP {response.status_code}")
            return None
        
        metrics_data = response.json()
        
        # Get timestamp from the metrics or use current time
        timestamp = datetime.fromisoformat(
            metrics_data.get("timestamp", datetime.utcnow().isoformat())
        )
        
        # Extract system metrics
        system_data = metrics_data.get("system", {})
        
        # Create a new SystemMetrics record
        metrics = SystemMetrics(
            cpu_usage=system_data.get("cpu_usage_percent", 0.0),
            memory_usage=system_data.get("memory_usage_percent", 0.0),
            disk_usage=system_data.get("disk_usage_percent", 0.0),
            api_requests=system_data.get("api_requests", 0),
            active_syncs=metrics_data.get("performance", {}).get("active_syncs", 0),
            active_users=metrics_data.get("performance", {}).get("active_users", 0),
            average_response_time=metrics_data.get("performance", {}).get("response_time_avg_ms", 0.0) / 1000,
            error_rate=metrics_data.get("performance", {}).get("error_rate", 0.0),
            database_health="healthy",
            syncservice_health="healthy",
            api_gateway_health="healthy",
            raw_metrics=json.dumps(metrics_data)
        )
        # Set timestamp separately
        metrics.timestamp = timestamp
        
        # Save to database
        with app.app_context():
            db.session.add(metrics)
            db.session.commit()
            logger.info(f"Stored SyncService metrics at {timestamp}")
            
            # Create audit log entry for metrics collection
            try:
                create_audit_log(
                    event_type="metrics_collected",
                    resource_type="system_metrics",
                    description=f"Collected system metrics from SyncService (CPU: {metrics.cpu_usage:.1f}%, Memory: {metrics.memory_usage:.1f}%)",
                    severity="info",
                    previous_state=None,
                    new_state={
                        "cpu_usage": metrics.cpu_usage,
                        "memory_usage": metrics.memory_usage,
                        "disk_usage": metrics.disk_usage,
                        "api_requests": metrics.api_requests,
                        "active_syncs": metrics.active_syncs,
                        "active_users": metrics.active_users,
                        "average_response_time": metrics.average_response_time,
                        "error_rate": metrics.error_rate
                    }
                )
                logger.info("Created audit log entry for metrics collection")
            except Exception as e:
                logger.error(f"Failed to create audit log for metrics collection: {str(e)}")
        
        return metrics_data
    except Exception as e:
        logger.error(f"Error collecting SyncService metrics: {str(e)}")
        return None

# Metrics implementation using database storage

# SyncService connection settings
SYNCSERVICE_BASE_URL = "http://0.0.0.0:8080"


def ensure_syncservice_running() -> bool:
    """
    Ensure the SyncService is running.
    If not, attempt to start it in the background using restart script.
    
    Implements automatic service recovery with retry logic and proper logging.
    
    Returns:
        bool: True if the SyncService is running or was started successfully
    """
    # First, check if the service is already running
    if check_syncservice_status():
        return True
    
    # If we get here, the service is not running, so try to start it
    logger.warning("SyncService not running, attempting to restart it...")
    
    # Create audit log for restart attempt
    with app.app_context():
        create_audit_log(
            event_type="service_restart_attempt",
            resource_type="system",
            description="Automatic SyncService restart triggered due to detected outage",
            severity="warning"
        )
    
    # Maximum number of restart attempts
    max_attempts = 3
    
    # Try to restart the service with multiple attempts if needed
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"SyncService restart attempt {attempt}/{max_attempts}")
            
            # Use the restart script to restart the SyncService
            import subprocess
            
            # Get the path to the restart script
            restart_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                        "restart_syncservice_workflow.py")
            
            # Execute the restart script
            subprocess.run(["python", restart_script], 
                          stderr=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          check=False,
                          timeout=30)
            
            # Wait for the service to start up
            logger.info("Waiting for SyncService to start...")
            
            # Check with exponential backoff - wait longer between each check
            wait_times = [2, 4, 8]
            for wait in wait_times:
                time.sleep(wait)
                if check_syncservice_status():
                    logger.info("SyncService successfully restarted!")
                    
                    # Create success audit log
                    with app.app_context():
                        create_audit_log(
                            event_type="service_restart_success",
                            resource_type="system",
                            description=f"SyncService was successfully restarted after {attempt} attempt(s)",
                            severity="info"
                        )
                    return True
            
            # If we got here, the service didn't start even after waiting
            logger.warning(f"SyncService didn't respond after restart attempt {attempt}")
            
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout while executing restart script (attempt {attempt})")
        except subprocess.SubprocessError as e:
            logger.error(f"Error executing restart script: {str(e)} (attempt {attempt})")
        except Exception as e:
            logger.error(f"Unexpected error during SyncService restart: {str(e)} (attempt {attempt})")
    
    # If we get here, all restart attempts failed
    logger.error(f"Failed to restart SyncService after {max_attempts} attempts")
    
    # Create failure audit log
    with app.app_context():
        create_audit_log(
            event_type="service_restart_failure",
            resource_type="system",
            description=f"Failed to restart SyncService after {max_attempts} attempts",
            severity="error"
        )
    
    return False


def check_syncservice_status() -> bool:
    """
    Check if the SyncService is running.
    
    Returns:
        bool: True if the SyncService is running, False otherwise
    """
    try:
        response = requests.get(f"{SYNCSERVICE_BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.RequestException:
        return False


def check_and_ensure_service_health():
    """
    Perform comprehensive health check and ensure services are running.
    
    This function is called periodically to:
    1. Check if SyncService is running and responding
    2. Verify the service is healthy by checking its metrics
    3. Attempt to restart it if it's down or unhealthy
    4. Log the results and create audit entries
    
    This is the main auto-recovery mechanism for the TerraFusion platform.
    """
    logger.info("Performing periodic service health check...")
    
    # Check if SyncService is responsive
    syncservice_status = check_syncservice_status()
    
    if not syncservice_status:
        logger.warning("SyncService is not responding during health check")
        # Create audit entry for detection
        with app.app_context():
            create_audit_log(
                event_type="service_outage_detected",
                resource_type="system",
                description="SyncService outage detected during periodic health check",
                severity="warning"
            )
        
        # Attempt to restart the service
        restart_success = ensure_syncservice_running()
        
        if restart_success:
            logger.info("SyncService auto-recovery successful")
            # Success is already logged in ensure_syncservice_running
            return True
        else:
            logger.error("SyncService auto-recovery failed")
            # Failure is already logged in ensure_syncservice_running
            return False
    
    # If we get here, the service is responding, but let's check its health
    try:
        # Get metrics from SyncService to check its health
        response = requests.get(f"{SYNCSERVICE_BASE_URL}/metrics", timeout=5)
        
        if response.status_code != 200:
            logger.warning(f"SyncService returned unhealthy status code: {response.status_code}")
            
            # Create audit entry for unhealthy service
            with app.app_context():
                create_audit_log(
                    event_type="service_unhealthy",
                    resource_type="system",
                    description=f"SyncService is responding but unhealthy (status code: {response.status_code})",
                    severity="warning"
                )
            
            # Attempt to restart the service since it's unhealthy
            restart_success = ensure_syncservice_running()
            
            if restart_success:
                logger.info("Unhealthy SyncService auto-recovery successful")
                return True
            else:
                logger.error("Unhealthy SyncService auto-recovery failed")
                return False
        
        # If we get here, the service is healthy
        metrics = response.json()
        
        # Check for critical resource usage that might indicate problems
        system_data = metrics.get("system", {})
        cpu_usage = system_data.get("cpu_usage_percent", 0.0)
        memory_usage = system_data.get("memory_usage_percent", 0.0)
        
        if cpu_usage > 95 or memory_usage > 95:
            logger.warning(f"SyncService is under resource stress: CPU={cpu_usage}%, Memory={memory_usage}%")
            
            # Create audit entry for resource stress
            with app.app_context():
                create_audit_log(
                    event_type="service_resource_stress",
                    resource_type="system",
                    description=f"SyncService is under resource stress (CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%)",
                    severity="warning",
                    new_state={
                        "cpu_usage": cpu_usage,
                        "memory_usage": memory_usage
                    }
                )
        
        # Log successful health check
        logger.info(f"SyncService health check successful (CPU: {cpu_usage:.1f}%, Memory: {memory_usage:.1f}%)")
        return True
        
    except Exception as e:
        logger.error(f"Error during SyncService health check: {str(e)}")
        
        # Create audit entry for health check error
        with app.app_context():
            create_audit_log(
                event_type="service_health_check_error",
                resource_type="system",
                description=f"Error during SyncService health check: {str(e)}",
                severity="error"
            )
        
        # Even though there was an error checking health, we know the service is responding
        # so we'll consider it a partial success
        return syncservice_status


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page for the API Gateway."""
    logger.debug(f"login_page called with method: {request.method}")
    logger.debug(f"Session data before: {session}")
    
    # Check if logout action
    if request.args.get('action') == 'logout':
        # Clear session
        logger.debug("Logout action detected")
        session.clear()
        flash('You have been logged out successfully', 'success')
        return redirect(url_for('root'))
    
    # Check if already authenticated
    if 'token' in session and request.method == 'GET':
        # Redirect to dashboard or next URL
        logger.debug("Already authenticated, redirecting to dashboard")
        next_url = request.args.get('next', url_for('dashboard'))
        return redirect(next_url)
    
    # Handle login form submission
    if request.method == 'POST':
        logger.debug(f"Login POST data: {request.form}")
        logger.debug(f"Content type: {request.content_type}")
        logger.debug(f"Headers: {request.headers}")
        username = request.form.get('username')
        password = request.form.get('password')
        next_url = request.form.get('next', url_for('dashboard'))
        
        # Try County RBAC first, fall back to standard
        try:
            from apps.backend.auth import authenticate_county_user, COUNTY_RBAC_AVAILABLE
            if COUNTY_RBAC_AVAILABLE:
                user = authenticate_county_user(username, password)
                if user:
                    # Make the session permanent
                    session.permanent = True
                    
                    # Set session data
                    session['username'] = user['username']
                    session['role'] = user['primary_role']
                    session['roles'] = user['roles']
                    session['token'] = 'county_auth_' + str(uuid.uuid4())
                    session['county_auth'] = True
                    
                    # Log debug info
                    logger.debug(f"County auth successful for {username} with role {user['primary_role']}")
                    logger.debug(f"Session is permanent: {session.permanent}")
                    logger.debug(f"Session data: {session}")
                    
                    # Create audit log entry
                    create_audit_log(
                        event_type='login_success',
                        resource_type='auth',
                        description=f"User {username} logged in successfully",
                        username=username
                    )
                    
                    # Check if user needs onboarding
                    try:
                        from apps.backend.onboarding.routes import start_or_continue_onboarding
                        redirect_url = start_or_continue_onboarding(user)
                        if redirect_url:
                            return redirect(redirect_url)
                    except ImportError:
                        pass  # Onboarding module not available
                    except Exception as e:
                        logger.error(f"Error checking onboarding status: {e}")
                        
                    # Redirect to next URL or dashboard
                    return redirect(next_url)
                
                # County auth available but user failed to authenticate
                create_audit_log(
                    event_type='login_failed',
                    resource_type='auth',
                    description=f"Failed login attempt for user {username}",
                    username=username,
                    severity='warning'
                )
                return render_template('login.html', error="Invalid username or password")
        except ImportError:
            # County auth module not available
            pass
        except Exception as e:
            logger.error(f"Error in county auth: {e}")
            
        # Fallback to test accounts
        if username == 'admin' and password == 'admin123':
            # Make the session permanent
            session.permanent = True
            
            # Set session values
            session['username'] = username
            session['role'] = 'ITAdmin'
            session['roles'] = ['ITAdmin']
            session['token'] = 'fallback_auth_' + str(uuid.uuid4())
            
            # Log debug info
            logger.debug(f"Login successful for {username} with role ITAdmin")
            logger.debug(f"Session after login: {session}")
            logger.debug(f"Session is permanent: {session.permanent}")
            
            # Create response with cookies explicitly set for Replit environment
            response = redirect(next_url)
            session_id = session.sid if hasattr(session, 'sid') else None
            if session_id:
                # Explicitly set the session cookie with SameSite=None for Replit environment
                # This is needed because Replit runs behind a proxy
                response.set_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    session_id,
                    max_age=app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds() 
                        if isinstance(app.config.get('PERMANENT_SESSION_LIFETIME'), timedelta) 
                        else app.config.get('PERMANENT_SESSION_LIFETIME', 86400),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    secure=True,
                    httponly=True,
                    samesite='None'
                )
            logger.debug(f"Response headers: {response.headers}")
            return response
        elif username == 'assessor' and password == 'assessor123':
            # Make the session permanent
            session.permanent = True
            
            # Set session values
            session['username'] = username
            session['role'] = 'Assessor'
            session['roles'] = ['Assessor']
            session['token'] = 'fallback_auth_' + str(uuid.uuid4())
            
            # Log debug info
            logger.debug(f"Login successful for {username} with role Assessor")
            logger.debug(f"Session after login: {session}")
            
            # Create response with cookies explicitly set for Replit environment
            response = redirect(next_url)
            session_id = session.sid if hasattr(session, 'sid') else None
            if session_id:
                # Explicitly set the session cookie with SameSite=None for Replit environment
                response.set_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    session_id,
                    max_age=app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds() 
                        if isinstance(app.config.get('PERMANENT_SESSION_LIFETIME'), timedelta) 
                        else app.config.get('PERMANENT_SESSION_LIFETIME', 86400),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    secure=True,
                    httponly=True,
                    samesite='None'
                )
            logger.debug(f"Response headers for Assessor: {response.headers}")
            return response
        elif username == 'staff' and password == 'staff123':
            # Make the session permanent
            session.permanent = True
            
            # Set session values
            session['username'] = username
            session['role'] = 'Staff'
            session['roles'] = ['Staff']
            session['token'] = 'fallback_auth_' + str(uuid.uuid4())
            
            # Log debug info
            logger.debug(f"Login successful for {username} with role Staff")
            logger.debug(f"Session after login: {session}")
            
            # Create response with cookies explicitly set for Replit environment
            response = redirect(next_url)
            session_id = session.sid if hasattr(session, 'sid') else None
            if session_id:
                # Explicitly set the session cookie with SameSite=None for Replit environment
                response.set_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    session_id,
                    max_age=app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds() 
                        if isinstance(app.config.get('PERMANENT_SESSION_LIFETIME'), timedelta) 
                        else app.config.get('PERMANENT_SESSION_LIFETIME', 86400),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    secure=True,
                    httponly=True,
                    samesite='None'
                )
            logger.debug(f"Response headers for Staff: {response.headers}")
            return response
        elif username == 'auditor' and password == 'auditor123':
            # Make the session permanent
            session.permanent = True
            
            # Set session values
            session['username'] = username
            session['role'] = 'Auditor'
            session['roles'] = ['Auditor']
            session['token'] = 'fallback_auth_' + str(uuid.uuid4())
            
            # Log debug info
            logger.debug(f"Login successful for {username} with role Auditor")
            logger.debug(f"Session after login: {session}")
            
            # Create response with cookies explicitly set for Replit environment
            response = redirect(next_url)
            session_id = session.sid if hasattr(session, 'sid') else None
            if session_id:
                # Explicitly set the session cookie with SameSite=None for Replit environment
                response.set_cookie(
                    app.config.get('SESSION_COOKIE_NAME', 'session'),
                    session_id,
                    max_age=app.config.get('PERMANENT_SESSION_LIFETIME').total_seconds() 
                        if isinstance(app.config.get('PERMANENT_SESSION_LIFETIME'), timedelta) 
                        else app.config.get('PERMANENT_SESSION_LIFETIME', 86400),
                    path=app.config.get('SESSION_COOKIE_PATH', '/'),
                    secure=True,
                    httponly=True,
                    samesite='None'
                )
            logger.debug(f"Response headers for Auditor: {response.headers}")
            return response
        else:
            # Create audit log for failed login
            create_audit_log(
                event_type='login_failed',
                resource_type='auth',
                description=f"Failed login attempt for user {username}",
                username=username,
                severity='warning'
            )
            return render_template('login.html', error="Invalid username or password")
    
    # Render login page for GET requests
    return render_template('login.html', error=request.args.get('error'))


@app.route('/')
def root():
    """Root endpoint for the API Gateway."""
    return render_template('index.html', 
                          service_status=check_syncservice_status(),
                          sync_pairs=db.session.query(SyncPair).all())


@app.route('/dashboard')
@requires_auth
def dashboard():
    """Main dashboard view."""
    # Try to get County user first, fall back to standard user
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission, COUNTY_RBAC_AVAILABLE
        if COUNTY_RBAC_AVAILABLE:
            user = get_current_county_user()
            if user:
                # Use County dashboard with role-based access control
                import datetime
                import os
                import psutil
                from sqlalchemy import func, desc
                
                current_time = datetime.datetime.now()
                
                # Get real data from the database
                # Get the latest sync operation
                latest_sync = db.session.query(SyncOperation).order_by(
                    SyncOperation.started_at.desc()
                ).first()
                
                # Get sync statistics
                today_start = datetime.datetime.combine(current_time.date(), datetime.time.min)
                week_start = today_start - datetime.timedelta(days=current_time.weekday())
                
                today_ops = db.session.query(SyncOperation).filter(
                    SyncOperation.started_at >= today_start
                ).count()
                
                week_ops = db.session.query(SyncOperation).filter(
                    SyncOperation.started_at >= week_start
                ).count()
                
                pending_count = db.session.query(SyncOperation).filter(
                    SyncOperation.status == 'PENDING'
                ).count()
                
                # System metrics
                try:
                    # Get latest system metrics
                    latest_metrics = db.session.query(SystemMetrics).order_by(
                        SystemMetrics.timestamp.desc()
                    ).first()
                    
                    disk_usage = latest_metrics.disk_usage if latest_metrics else 0
                    
                    # Get system uptime
                    uptime_seconds = psutil.boot_time()
                    uptime_text = str(datetime.timedelta(seconds=int(current_time.timestamp() - uptime_seconds)))
                    
                    # Get error count from last 24 hours
                    error_count = db.session.query(AuditEntry).filter(
                        AuditEntry.severity.in_(['error', 'critical']),
                        AuditEntry.timestamp >= (current_time - datetime.timedelta(hours=24))
                    ).count()
                    
                    # Get active user count (unique users with activity in last hour)
                    active_users = db.session.query(func.count(func.distinct(AuditEntry.username))).filter(
                        AuditEntry.timestamp >= (current_time - datetime.timedelta(hours=1))
                    ).scalar() or 0
                    
                except Exception as e:
                    logger.error(f"Error getting system metrics: {e}")
                    disk_usage = 0
                    uptime_text = "Unknown"
                    error_count = 0
                    active_users = 0
                
                # Role-specific data
                recent_approvals = 0
                oldest_pending_time = "N/A"
                today_changes = 0
                changes_by_dept = "N/A"
                critical_events = 0
                user_uploads = 0
                user_pending_uploads = 0
                last_upload_time = "N/A"
                
                # Assessor data
                if 'Assessor' in user['roles']:
                    # Get recent approvals
                    recent_approvals = db.session.query(AuditEntry).filter(
                        AuditEntry.event_type == 'sync_approved',
                        AuditEntry.timestamp >= today_start
                    ).count()
                    
                    # Get oldest pending operation
                    oldest_pending = db.session.query(SyncOperation).filter(
                        SyncOperation.status == 'PENDING'
                    ).order_by(SyncOperation.started_at.asc()).first()
                    
                    if oldest_pending and oldest_pending.started_at:
                        time_diff = current_time - oldest_pending.started_at
                        hours = int(time_diff.total_seconds() / 3600)
                        oldest_pending_time = f"{hours} hours" if hours < 24 else f"{int(hours/24)} days"
                
                # Auditor data
                if 'Auditor' in user['roles']:
                    # Get today's changes
                    today_changes = db.session.query(AuditEntry).filter(
                        AuditEntry.timestamp >= today_start
                    ).count()
                    
                    # Get critical events
                    critical_events = db.session.query(AuditEntry).filter(
                        AuditEntry.severity == 'critical',
                        AuditEntry.timestamp >= today_start
                    ).count()
                    
                    # Group changes by department (using username for now)
                    dept_counts = db.session.query(
                        AuditEntry.username, func.count(AuditEntry.id)
                    ).filter(
                        AuditEntry.timestamp >= today_start
                    ).group_by(AuditEntry.username).all()
                    
                    if dept_counts:
                        changes_by_dept = ", ".join([f"{dept[0]}: {dept[1]}" for dept in dept_counts[:3]])
                
                # Staff data
                if 'Staff' in user['roles']:
                    # Get user uploads
                    user_uploads = db.session.query(SyncOperation).filter(
                        SyncOperation.created_by == user['username'],
                        SyncOperation.started_at >= week_start
                    ).count()
                    
                    # Get pending user uploads
                    user_pending_uploads = db.session.query(SyncOperation).filter(
                        SyncOperation.created_by == user['username'],
                        SyncOperation.status == 'PENDING'
                    ).count()
                    
                    # Get last upload time
                    last_upload = db.session.query(SyncOperation).filter(
                        SyncOperation.created_by == user['username']
                    ).order_by(SyncOperation.started_at.desc()).first()
                    
                    if last_upload and last_upload.started_at:
                        last_upload_time = last_upload.started_at.strftime('%Y-%m-%d %H:%M:%S')
                
                # Get recent operations for table
                recent_ops = db.session.query(SyncOperation).order_by(
                    SyncOperation.started_at.desc()
                ).limit(10).all()
                
                recent_operations = []
                for op in recent_ops:
                    recent_operations.append({
                        'id': f"OP-{op.id:06d}" if isinstance(op.id, int) else str(op.id),
                        'timestamp': op.started_at.strftime('%Y-%m-%d %H:%M:%S') if op.started_at else 'N/A',
                        'filename': op.sync_type, # Placeholder, would come from file metadata
                        'property_count': op.total_records or 0,
                        'status': op.status.upper()
                    })
                
                # If no operations found, provide fallback data
                if not recent_operations:
                    recent_operations = [
                        {
                            'id': 'OP-000001',
                            'timestamp': current_time.strftime('%Y-%m-%d %H:%M:%S'),
                            'filename': 'No operations found',
                            'property_count': 0,
                            'status': 'N/A'
                        }
                    ]
                
                # Get sync status data
                if latest_sync:
                    last_sync_time = latest_sync.completed_at.strftime('%Y-%m-%d %H:%M:%S') if latest_sync.completed_at else 'In Progress'
                    sync_status = latest_sync.status.capitalize()
                    records_processed = latest_sync.processed_records
                else:
                    last_sync_time = 'Never'
                    sync_status = 'Not Started'
                    records_processed = 0
                
                context = {
                    'user': user,
                    'check_county_permission': check_county_permission,
                    'last_sync_time': last_sync_time,
                    'sync_status': sync_status,
                    'records_processed': records_processed,
                    'storage_usage': int(disk_usage) if disk_usage else 0,
                    'today_activity_count': today_ops,
                    'weekly_activity_count': week_ops,
                    'pending_approvals': pending_count,
                    'current_year': current_time.year,
                    'recent_operations': recent_operations,
                    
                    # IT Admin specific
                    'system_uptime': uptime_text,
                    'error_count': error_count,
                    'active_users': active_users,
                    
                    # Assessor specific
                    'recent_approvals': recent_approvals,
                    'oldest_pending_time': oldest_pending_time,
                    
                    # Auditor specific
                    'today_changes': today_changes,
                    'changes_by_dept': changes_by_dept,
                    'critical_events': critical_events,
                    
                    # Staff specific
                    'user_uploads': user_uploads,
                    'user_pending_uploads': user_pending_uploads,
                    'last_upload_time': last_upload_time
                }
                
                return render_template('county_dashboard.html', **context)
            else:
                user = get_current_user()
        else:
            user = get_current_user()
    except ImportError:
        user = get_current_user()
    except Exception as e:
        logger.error(f"Error in dashboard: {e}")
        # If we hit an exception, fall back to standard dashboard
        user = get_current_user()
        
    # Fallback to standard dashboard for non-County users
    if request.args.get('new_ui', '0') == '1':
        return render_template('dashboard_new.html', user=user)
    return render_template('dashboard.html', user=user)


@app.route('/dashboard/sync')
@requires_auth
def sync_dashboard():
    """Sync operations dashboard."""
    # Try to use County RBAC, otherwise fall back to standard auth
    try:
        from apps.backend.auth import requires_county_permission, get_current_county_user, COUNTY_RBAC_AVAILABLE
        
        if COUNTY_RBAC_AVAILABLE:
            # County user takes precedence if available
            county_user = get_current_county_user()
            if county_user:
                # If County RBAC is active, check permission to view sync dashboard
                if "view" not in county_user.get("permissions", []):
                    from apps.backend.auth import log_user_action
                    # Log the access attempt
                    log_user_action(
                        county_user["username"],
                        county_user["role"],
                        "DENIED:view_sync_dashboard"
                    )
                    return redirect(url_for('county_auth.county_login', 
                                          next=request.path,
                                          message="You need 'view' permission to access this page."))
                
                # User has permission, log the access
                from apps.backend.auth import log_user_action
                log_user_action(
                    county_user["username"],
                    county_user["role"],
                    "ACCESS:sync_dashboard"
                )
                user = county_user
            else:
                user = get_current_user()
        else:
            user = get_current_user()
    except ImportError:
        user = get_current_user()
    
    return render_template('sync_dashboard.html',
                          user=user,
                          sync_pairs=db.session.query(SyncPair).all(),
                          recent_operations=db.session.query(SyncOperation).order_by(
                              SyncOperation.started_at.desc()).limit(10).all())


@app.route('/sync/pairs')
@requires_auth
def sync_pairs():
    """Sync pairs management page."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission, COUNTY_RBAC_AVAILABLE
        if COUNTY_RBAC_AVAILABLE:
            user = get_current_county_user()
            if user:
                # Check permission to view sync pairs
                if not check_county_permission('view_sync_operations'):
                    flash('Permission denied: You do not have access to sync pairs management', 'error')
                    return redirect(url_for('dashboard'))
                
                import datetime
                current_time = datetime.datetime.now()
                
                # Get all sync pairs from database
                pairs = db.session.query(SyncPair).all()
                
                context = {
                    'user': user,
                    'check_county_permission': check_county_permission,
                    'current_year': current_time.year,
                    'sync_pairs': pairs
                }
                
                return render_template('sync_pairs.html', **context)
    except Exception as e:
        logger.error(f"Error in sync_pairs view: {e}")
        
    # Fall back to standard view if any error occurs
    flash('Error loading sync pairs management', 'error')
    return redirect(url_for('dashboard'))


@app.route('/sync/pairs/create', methods=['POST'])
@requires_auth
def create_sync_pair():
    """Create a new sync pair."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission
        
        user = get_current_county_user()
        if not user or not check_county_permission('create_sync_pairs'):
            flash('Permission denied: You do not have access to create sync pairs', 'error')
            return redirect(url_for('sync_pairs'))
        
        import json
        
        # Get form data
        name = request.form.get('name')
        description = request.form.get('description', '')
        sync_schedule = request.form.get('sync_schedule', 'manual')
        
        source_type = request.form.get('source_type')
        source_config = request.form.get('source_config', '{}')
        
        target_type = request.form.get('target_type')
        target_config = request.form.get('target_config', '{}')
        
        field_mappings = request.form.get('field_mappings', '{}')
        
        # Basic validation
        if not name or not source_type or not target_type:
            flash('Missing required fields', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Parse JSON fields
        try:
            source_config_json = json.loads(source_config)
            target_config_json = json.loads(target_config)
            field_mappings_json = json.loads(field_mappings)
        except json.JSONDecodeError:
            flash('Invalid JSON in configuration fields', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Create new sync pair
        new_pair = SyncPair(
            name=name,
            description=description,
            source_type=source_type,
            source_config=source_config_json,
            target_type=target_type,
            target_config=target_config_json,
            sync_schedule=sync_schedule,
            is_active=True,
            created_by=user.get('username')
        )
        
        db.session.add(new_pair)
        db.session.commit()
        
        # Log the action
        create_audit_log(
            event_type='sync_pair_created',
            resource_type='sync_pair',
            description=f"Created new sync pair: {name}",
            resource_id=str(new_pair.id),
            user_id=user.get('id'),
            username=user.get('username'),
            ip_address=request.remote_addr,
            severity='info',
            new_state={
                'id': new_pair.id,
                'name': name,
                'source_type': source_type,
                'target_type': target_type
            }
        )
        
        flash(f'Sync pair "{name}" created successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating sync pair: {e}")
        flash(f'Error creating sync pair: {str(e)}', 'error')
    
    return redirect(url_for('sync_pairs'))


@app.route('/sync/pairs/<int:pair_id>')
@requires_auth
def view_sync_pair(pair_id):
    """View details of a sync pair."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission
        
        if not check_county_permission('view_sync_pairs'):
            flash('Permission denied: You do not have access to view sync pair details', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Get the sync pair
        pair = db.session.query(SyncPair).filter(SyncPair.id == pair_id).first()
        
        if not pair:
            flash('Sync pair not found', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Get operations for this pair
        operations = db.session.query(SyncOperation).filter(
            SyncOperation.sync_pair_id == pair_id
        ).order_by(SyncOperation.started_at.desc()).limit(10).all()
        
        user = get_current_county_user()
        context = {
            'user': user,
            'check_county_permission': check_county_permission,
            'pair': pair,
            'operations': operations,
            'current_year': datetime.datetime.now().year
        }
        
        return render_template('sync_pair_details.html', **context)
        
    except Exception as e:
        logger.error(f"Error viewing sync pair: {e}")
        flash(f'Error viewing sync pair: {str(e)}', 'error')
        return redirect(url_for('sync_pairs'))


@app.route('/sync/pairs/<int:pair_id>/edit', methods=['GET', 'POST'])
@requires_auth
def edit_sync_pair(pair_id):
    """Edit a sync pair."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission
        
        if not check_county_permission('edit_sync_pairs'):
            flash('Permission denied: You do not have access to edit sync pairs', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Get the sync pair
        pair = db.session.query(SyncPair).filter(SyncPair.id == pair_id).first()
        
        if not pair:
            flash('Sync pair not found', 'error')
            return redirect(url_for('sync_pairs'))
        
        user = get_current_county_user()
        
        if request.method == 'POST':
            import json
            
            # Update fields
            previous_state = pair.to_dict()
            
            pair.name = request.form.get('name', pair.name)
            pair.description = request.form.get('description', pair.description)
            pair.sync_schedule = request.form.get('sync_schedule', pair.sync_schedule)
            
            # Parse JSON fields
            try:
                source_config = request.form.get('source_config')
                target_config = request.form.get('target_config')
                field_mappings = request.form.get('field_mappings')
                
                if source_config:
                    pair.source_config = json.loads(source_config)
                if target_config:
                    pair.target_config = json.loads(target_config)
                if field_mappings:
                    pair.field_mappings = json.loads(field_mappings)
            except json.JSONDecodeError:
                flash('Invalid JSON in configuration fields', 'error')
                return redirect(url_for('edit_sync_pair', pair_id=pair_id))
            
            db.session.commit()
            
            # Log the action
            create_audit_log(
                event_type='sync_pair_updated',
                resource_type='sync_pair',
                description=f"Updated sync pair: {pair.name}",
                resource_id=str(pair.id),
                user_id=user.get('id'),
                username=user.get('username'),
                ip_address=request.remote_addr,
                severity='info',
                previous_state=previous_state,
                new_state=pair.to_dict()
            )
            
            flash(f'Sync pair "{pair.name}" updated successfully', 'success')
            return redirect(url_for('sync_pairs'))
        else:
            # GET request - show edit form
            context = {
                'user': user,
                'check_county_permission': check_county_permission,
                'pair': pair,
                'current_year': datetime.datetime.now().year
            }
            
            return render_template('edit_sync_pair.html', **context)
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing sync pair: {e}")
        flash(f'Error editing sync pair: {str(e)}', 'error')
        return redirect(url_for('sync_pairs'))


@app.route('/sync/pairs/toggle-status', methods=['POST'])
@requires_auth
def toggle_sync_pair_status():
    """Enable or disable a sync pair."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission
        
        if not check_county_permission('manage_sync_pairs'):
            flash('Permission denied: You do not have access to manage sync pairs', 'error')
            return redirect(url_for('sync_pairs'))
        
        pair_id = request.form.get('sync_pair_id')
        active = request.form.get('active') == '1'
        
        if not pair_id:
            flash('Missing sync pair ID', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Get the sync pair
        pair = db.session.query(SyncPair).filter(SyncPair.id == pair_id).first()
        
        if not pair:
            flash('Sync pair not found', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Update status
        previous_state = pair.to_dict()
        pair.is_active = active
        db.session.commit()
        
        # Log the action
        user = get_current_county_user()
        create_audit_log(
            event_type='sync_pair_status_changed',
            resource_type='sync_pair',
            description=f"{'Enabled' if active else 'Disabled'} sync pair: {pair.name}",
            resource_id=str(pair.id),
            user_id=user.get('id'),
            username=user.get('username'),
            ip_address=request.remote_addr,
            severity='info',
            previous_state=previous_state,
            new_state=pair.to_dict()
        )
        
        flash(f'Sync pair "{pair.name}" {("enabled" if active else "disabled")} successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error toggling sync pair status: {e}")
        flash(f'Error toggling sync pair status: {str(e)}', 'error')
    
    return redirect(url_for('sync_pairs'))


@app.route('/sync/operations/run', methods=['POST'])
@requires_auth
def run_sync_operation():
    """Run a sync operation for a specific pair."""
    try:
        from apps.backend.auth import get_current_county_user, check_county_permission
        
        if not check_county_permission('execute_sync'):
            flash('Permission denied: You do not have access to run sync operations', 'error')
            return redirect(url_for('sync_pairs'))
        
        pair_id = request.form.get('sync_pair_id')
        
        if not pair_id:
            flash('Missing sync pair ID', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Get the sync pair
        pair = db.session.query(SyncPair).filter(SyncPair.id == pair_id).first()
        
        if not pair:
            flash('Sync pair not found', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Check if pair is active
        if not pair.is_active:
            flash('Cannot run sync for inactive pair', 'error')
            return redirect(url_for('sync_pairs'))
        
        # Create new sync operation
        user = get_current_county_user()
        operation = SyncOperation(
            sync_pair_id=pair.id,
            status='pending',
            sync_type='manual',
            started_at=datetime.datetime.now(),
            created_by=user.get('username')
        )
        
        db.session.add(operation)
        db.session.commit()
        
        # Log the action
        create_audit_log(
            event_type='sync_operation_started',
            resource_type='sync_operation',
            description=f"Started sync operation for pair: {pair.name}",
            resource_id=str(operation.id),
            operation_id=operation.id,
            user_id=user.get('id'),
            username=user.get('username'),
            ip_address=request.remote_addr,
            severity='info',
            new_state=operation.to_dict()
        )
        
        flash(f'Sync operation started for "{pair.name}"', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error starting sync operation: {e}")
        flash(f'Error starting sync operation: {str(e)}', 'error')
    
    return redirect(url_for('sync_pairs'))


@app.route('/new-sync')
@requires_auth
def new_sync_wizard():
    """New sync operation wizard."""
    # Try to use County RBAC, otherwise fall back to standard auth
    try:
        from apps.backend.auth import requires_county_permission, get_current_county_user, COUNTY_RBAC_AVAILABLE
        
        if COUNTY_RBAC_AVAILABLE:
            # County user takes precedence if available
            county_user = get_current_county_user()
            if county_user:
                # Check if user has permission to create new sync operations
                user_role = county_user.get("role")
                if user_role not in ["ITAdmin", "Staff"]:
                    from apps.backend.auth import log_user_action
                    # Log the access attempt
                    log_user_action(
                        county_user["username"],
                        user_role,
                        "DENIED:new_sync_wizard"
                    )
                    return redirect(url_for('county_auth.county_login', 
                                          next=request.path,
                                          message="You need Staff or ITAdmin role to access this page."))
                
                # User has permission, log the access
                from apps.backend.auth import log_user_action
                log_user_action(
                    county_user["username"],
                    user_role,
                    "ACCESS:new_sync_wizard"
                )
                user = county_user
            else:
                user = get_current_user()
        else:
            user = get_current_user()
    except ImportError:
        user = get_current_user()
    
    return render_template('new_sync_wizard.html', user=user)


@app.route('/test-metrics')
def test_metrics():
    """Test endpoint to check metrics (development only)."""
    metrics = db.session.query(SystemMetrics).order_by(
        SystemMetrics.timestamp.desc()).limit(5).all()
    result = []
    for metric in metrics:
        metric_dict = {
            'id': metric.id,
            'timestamp': metric.timestamp.isoformat(),
            'cpu_usage': metric.cpu_usage,
            'memory_usage': metric.memory_usage,
            'disk_usage': metric.disk_usage,
            'api_requests': metric.api_requests,
            'active_syncs': metric.active_syncs,
            'active_users': metric.active_users,
            'average_response_time': metric.average_response_time,
            'error_rate': metric.error_rate,
        }
        result.append(metric_dict)
    return jsonify(result)

@app.route('/dashboard/metrics')
@requires_auth
def metrics_dashboard():
    """Metrics dashboard."""
    user = get_current_user()
    return render_template('metrics_dashboard.html',
                          user=user,
                          system_metrics=db.session.query(SystemMetrics).order_by(
                              SystemMetrics.timestamp.desc()).limit(100).all())


@app.route('/dashboard/audit')
@requires_auth
def audit_dashboard():
    """Audit trail dashboard."""
    user = get_current_user()
    
    # Parse query parameters
    try:
        from_date = request.args.get('from_date')
        if from_date:
            from_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        
        to_date = request.args.get('to_date')
        if to_date:
            to_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    except ValueError:
        # If dates are invalid, ignore them
        from_date = None
        to_date = None
    
    event_type = request.args.get('event_type')
    resource_type = request.args.get('resource_type')
    severity = request.args.get('severity')
    
    # Build query
    query = db.session.query(AuditEntry)
    
    if from_date:
        query = query.filter(AuditEntry.timestamp >= from_date)
    
    if to_date:
        query = query.filter(AuditEntry.timestamp <= to_date)
    
    if event_type:
        query = query.filter(AuditEntry.event_type == event_type)
    
    if resource_type:
        query = query.filter(AuditEntry.resource_type == resource_type)
    
    if severity:
        query = query.filter(AuditEntry.severity == severity)
    
    # Get audit entries with pagination
    audit_entries = query.order_by(AuditEntry.timestamp.desc()).limit(100).all()
    
    # Get summary data for the dashboard
    event_type_counts = db.session.query(
        AuditEntry.event_type, 
        db.func.count(AuditEntry.id)
    ).group_by(AuditEntry.event_type).all()
    
    severity_counts = db.session.query(
        AuditEntry.severity, 
        db.func.count(AuditEntry.id)
    ).group_by(AuditEntry.severity).all()
    
    latest_entry = db.session.query(AuditEntry).order_by(
        AuditEntry.timestamp.desc()
    ).first()
    
    latest_errors = db.session.query(AuditEntry).filter(
        AuditEntry.severity.in_(['error', 'critical'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    summary = {
        "total_entries": db.session.query(AuditEntry).count(),
        "latest_timestamp": latest_entry.timestamp if latest_entry else None,
        "event_type_counts": dict(event_type_counts),
        "severity_counts": dict(severity_counts),
        "latest_errors": latest_errors
    }
    
    return render_template('audit_dashboard.html',
                          user=user,
                          audit_entries=audit_entries,
                          summary=summary)


@app.route('/architecture')
@requires_auth
def architecture_visualization():
    """Interactive system architecture visualization."""
    user = get_current_user()
    # Check if the user has requested the new UI
    if request.args.get('new_ui', '0') == '1':
        return render_template('architecture_new.html', user=user)
    return render_template('architecture.html', user=user)

@app.route('/logs')
@requires_auth
def view_logs():
    """View system logs page."""
    user = get_current_user()
    # Check if the user has requested the new UI
    if request.args.get('new_ui', '0') == '1':
        return render_template('logs_new.html', user=user)
    return render_template('logs.html', user=user)


@app.route('/api/docs')
def api_docs():
    """Redirect to the API documentation."""
    return redirect(f"{SYNCSERVICE_BASE_URL}/docs")


@app.route('/api/status')
def status():
    """
    API status endpoint providing overall system status.
    """
    syncservice_status = check_syncservice_status()
    
    # Check database connection
    try:
        # Simple database query to check connection
        db_status = db.session.execute(db.select(db.func.now())).scalar() is not None
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db_status = False
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api_gateway": "online",
            "sync_service": "online" if syncservice_status else "offline",
            "database": "online" if db_status else "offline"
        },
        "version": "0.1.0",
        "auto_recovery": {
            "enabled": True,
            "last_check": datetime.fromtimestamp(last_service_health_check_time).isoformat() if last_service_health_check_time > 0 else None,
            "check_interval": f"{SERVICE_HEALTH_CHECK_INTERVAL} seconds"
        }
    })


@app.route('/api/service/health-check', methods=['POST'])
@requires_auth
def trigger_health_check():
    """
    Manually trigger a service health check.
    
    This endpoint allows administrators to manually run a service health check
    and attempt recovery if needed.
    """
    user = get_current_user()
    
    # Run the health check
    try:
        # Create audit log for manual health check
        with app.app_context():
            create_audit_log(
                event_type="manual_health_check",
                resource_type="system",
                description="Manual service health check triggered by user",
                severity="info",
                user_id=getattr(user, 'id', None),
                username=getattr(user, 'username', None)
            )
        
        # Run the health check
        health_status = check_and_ensure_service_health()
        
        return jsonify({
            "success": True,
            "message": "Health check completed successfully" if health_status else "Health check completed with issues",
            "status": "healthy" if health_status else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {
                "syncservice_responding": check_syncservice_status(),
                "auto_recovery_enabled": True
            }
        })
    except Exception as e:
        logger.error(f"Error running manual health check: {str(e)}")
        return jsonify({
            "success": False,
            "message": f"Error running health check: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/health')
def health_check():
    """
    General health check endpoint.
    
    This is the main health check endpoint for the API Gateway,
    providing overall service health status.
    """
    # Check if SyncService is available
    syncservice_status = check_syncservice_status()
    
    # Check database connection
    try:
        # Simple database query to check connection
        db_status = db.session.execute(db.select(db.func.now())).scalar() is not None
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db_status = False
    
    # Check WebSocket server status
    websocket_status = False
    try:
        response = requests.get("http://0.0.0.0:8081/health", timeout=2)
        websocket_status = response.status_code == 200
    except Exception:
        websocket_status = False
    
    # Get system metrics using the safe system monitor
    system_metrics = {}
    try:
        monitor = SafeSystemMonitor()
        system_metrics = monitor.get_system_health()
    except Exception as e:
        logger.error(f"Error getting system metrics: {str(e)}")
    
    # Overall health status
    is_healthy = db_status  # API Gateway requires database to be healthy
    
    return jsonify({
        "service": "TerraFusion API Gateway",
        "status": "healthy" if is_healthy else "unhealthy",
        "version": "0.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api_gateway": "healthy",
            "sync_service": "healthy" if syncservice_status else "unhealthy",
            "database": "healthy" if db_status else "unhealthy",
            "websocket": "healthy" if websocket_status else "unhealthy"
        },
        "system": system_metrics
    }), 200 if is_healthy else 503

@app.route('/health/live')
def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Verifies that the API Gateway is running and responsive.
    """
    return jsonify({
        "status": "alive",
        "service": "TerraFusion API Gateway",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/metrics')
def get_metrics():
    """
    Metrics endpoint.
    
    This endpoint exposes metrics in plaintext format for monitoring systems.
    
    Since we've disabled the Prometheus metrics for stability,
    we're returning a simple plaintext representation of the most 
    important system metrics.
    """
    try:
        # Get the most recent system metrics from the database
        recent_metrics = db.session.query(SystemMetrics).order_by(
            SystemMetrics.timestamp.desc()).limit(1).first()
        
        if recent_metrics:
            # Format a simple plaintext representation
            metrics_text = f"""# HELP terrafusion_system_cpu_usage Current CPU usage percentage
# TYPE terrafusion_system_cpu_usage gauge
terrafusion_system_cpu_usage {recent_metrics.cpu_usage}

# HELP terrafusion_system_memory_usage Current memory usage percentage
# TYPE terrafusion_system_memory_usage gauge
terrafusion_system_memory_usage {recent_metrics.memory_usage}

# HELP terrafusion_system_disk_usage Current disk usage percentage
# TYPE terrafusion_system_disk_usage gauge
terrafusion_system_disk_usage {recent_metrics.disk_usage}

# HELP terrafusion_active_connections Number of active connections
# TYPE terrafusion_active_connections gauge
terrafusion_active_connections {recent_metrics.active_connections}

# HELP terrafusion_response_time Average API response time in seconds
# TYPE terrafusion_response_time gauge
terrafusion_response_time {recent_metrics.response_time}

# HELP terrafusion_error_count Total error count
# TYPE terrafusion_error_count counter
terrafusion_error_count {recent_metrics.error_count}
"""
            return Response(metrics_text, content_type="text/plain")
        else:
            return Response("# No metrics available", content_type="text/plain")
    except Exception as e:
        logger.error(f"Error generating metrics: {str(e)}")
        return Response(f"# Error generating metrics: {str(e)}", content_type="text/plain")
        
@app.route('/health/ready')
def readiness_check():
    """
    Kubernetes readiness probe endpoint.
    Verifies that the API Gateway is ready to accept traffic.
    """
    # Check if SyncService is available
    syncservice_status = check_syncservice_status()
    
    # Check database connection
    try:
        # Simple database query to check connection
        db_status = db.session.execute(db.select(db.func.now())).scalar() is not None
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db_status = False
    
    # Determine if we're ready based on component status
    is_ready = db_status  # We can function without SyncService, but not without DB
    
    if not is_ready:
        # Return 503 Service Unavailable if not ready
        return jsonify({
            "status": "not_ready",
            "reason": "One or more critical dependencies unavailable",
            "details": {
                "database": "up" if db_status else "down",
                "sync_service": "up" if syncservice_status else "down",
            },
            "timestamp": datetime.utcnow().isoformat()
        }), 503
    
    return jsonify({
        "status": "ready",
        "details": {
            "dependencies": {
                "database": "up",
                "sync_service": "up" if syncservice_status else "down",
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route('/api/sync-pairs', methods=['GET'])
@requires_auth
def get_sync_pairs():
    """Get all configured sync pairs."""
    pairs = db.session.query(SyncPair).all()
    return jsonify([pair.to_dict() for pair in pairs])


@app.route('/api/sync-pairs/<int:pair_id>', methods=['GET', 'PUT'])
@requires_auth
def get_sync_pair(pair_id):
    """Get or update a specific sync pair by ID."""
    pair = db.session.query(SyncPair).get_or_404(pair_id)
    
    if request.method == 'GET':
        return jsonify(pair.to_dict())
    
    # Handle PUT request to update sync pair
    if request.method == 'PUT':
        # Get the JSON data from the request
        data = request.json
        
        if not data:
            return jsonify({
                "error": "Missing request data",
                "message": "Request body must contain sync pair data"
            }), 400
        
        # Save previous state for audit log
        previous_state = pair.to_dict()
        
        # Update allowed fields
        if 'name' in data:
            pair.name = data['name']
        if 'description' in data:
            pair.description = data['description']
        if 'config' in data:
            pair.config = data['config']
        if 'active' in data:
            pair.active = data['active']
        
        # Save changes
        pair.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Create audit log entry
        user = get_current_user()
        create_audit_log(
            event_type="config_changed",
            resource_type="sync_pair",
            resource_id=str(pair_id),
            description=f"Updated sync configuration for {pair.name}",
            previous_state=previous_state,
            new_state=pair.to_dict(),
            severity="info",
            user_id=user.get('id') if user else None,
            username=user.get('username') if user else None
        )
        
        return jsonify(pair.to_dict())


@app.route('/api/sync-operations', methods=['GET', 'POST'])
@requires_auth
def get_sync_operations():
    """Get all sync operations, with optional filtering or start a new operation."""
    # Handle GET request
    if request.method == 'GET':
        pair_id = request.args.get('pair_id', type=int)
        status = request.args.get('status')
        
        query = db.session.query(SyncOperation)
        
        if pair_id:
            query = query.filter_by(sync_pair_id=pair_id)
        
        if status:
            query = query.filter_by(status=status)
        
        operations = query.order_by(SyncOperation.started_at.desc()).all()
        return jsonify([op.to_dict() for op in operations])
    
    # Handle POST request to start a new sync operation
    elif request.method == 'POST':
        data = request.json
        
        if not data:
            return jsonify({
                "error": "Missing request data",
                "message": "Request body must contain sync operation parameters"
            }), 400
        
        # Validate required fields
        if 'sync_pair_id' not in data:
            return jsonify({
                "error": "Missing sync_pair_id",
                "message": "sync_pair_id is required to start a sync operation"
            }), 400
        
        # Get the sync pair
        sync_pair = db.session.query(SyncPair).get(data['sync_pair_id'])
        if not sync_pair:
            return jsonify({
                "error": "Invalid sync_pair_id",
                "message": f"No sync pair found with ID {data['sync_pair_id']}"
            }), 404
        
        # Determine operation type (default to incremental)
        operation_type = data.get('operation_type', 'incremental')
        if operation_type not in ['full', 'incremental']:
            return jsonify({
                "error": "Invalid operation_type",
                "message": "operation_type must be 'full' or 'incremental'"
            }), 400
        
        # Create the sync operation
        operation = SyncOperation(
            sync_pair_id=sync_pair.id,
            operation_type=operation_type,
            status='pending',
            started_at=datetime.utcnow(),
            total_records=0,
            processed_records=0,
            successful_records=0,
            failed_records=0
        )
        
        # Save to database
        db.session.add(operation)
        db.session.commit()
        
        # Create audit log entry
        user = get_current_user()
        create_audit_log(
            event_type="sync_started",
            resource_type="sync_operation",
            resource_id=str(operation.id),
            operation_id=operation.id,
            description=f"{operation_type.capitalize()} synchronization started for {sync_pair.name}",
            new_state=operation.to_dict(),
            severity="info",
            user_id=user.get('id') if user else None,
            username=user.get('username') if user else None,
            correlation_id=f"sync-{operation.id}"
        )
        
        # In a real implementation, this would trigger the sync process
        # Here we'll just acknowledge the request
        
        return jsonify({
            "message": f"{operation_type.capitalize()} sync started for pair {sync_pair.name}",
            "operation": operation.to_dict()
        })


@app.route('/api/metrics/system', methods=['GET'])
@requires_auth
def get_system_metrics():
    """Get system metrics from the database."""
    limit = request.args.get('limit', 100, type=int)
    
    system_metrics = db.session.query(SystemMetrics).order_by(
        SystemMetrics.timestamp.desc()).limit(limit).all()
    
    # Also try to collect new metrics 
    if check_syncservice_status():
        try:
            collect_syncservice_metrics()
            logger.info("Collected new metrics from SyncService")
        except Exception as e:
            logger.error(f"Failed to collect new metrics: {str(e)}")
    
    return jsonify([metric.to_dict() for metric in system_metrics])

@app.route('/api/metrics/refresh', methods=['POST'])
@requires_auth
def refresh_metrics():
    """Manually trigger metrics collection from SyncService."""
    user = get_current_user()
    
    if not check_syncservice_status():
        return jsonify({
            "status": "error",
            "message": "SyncService is not available",
            "timestamp": datetime.utcnow().isoformat()
        }), 503
    
    # Create a thread to collect metrics in the background
    thread = threading.Thread(target=lambda: collect_metrics_safely())
    thread.daemon = True
    thread.start()
    
    # Create audit log for manual refresh
    create_audit_log(
        event_type="metrics_refresh_requested",
        resource_type="system_metrics",
        description="Manual metrics collection initiated by user",
        severity="info",
        user_id=user.get('id') if user else None,
        username=user.get('username') if user else None
    )
    
    return jsonify({
        "status": "success",
        "message": "Metrics collection initiated",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/api/architecture')
@requires_auth
def get_architecture_data():
    """
    API endpoint to provide system architecture data for visualization.
    
    Returns JSON data with nodes and links representing the system components
    and their relationships.
    
    For the new interactive visualization UI, this returns a different format
    optimized for D3.js or similar visualization libraries.
    """
    # Check if the request is for the new UI
    is_new_ui = request.args.get('new_ui', '0') == '1'
    
    # Check the status of services
    syncservice_status = check_syncservice_status()
    
    # Check database connection
    try:
        # Simple database query to check connection
        db_status = db.session.execute(db.select(db.func.now())).scalar() is not None
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        db_status = False
    
    # Get latest metrics
    try:
        latest_metrics = db.session.query(SystemMetrics).order_by(
            SystemMetrics.timestamp.desc()).first()
    except Exception:
        latest_metrics = None
    
    # Get recent sync operations
    try:
        recent_operations = db.session.query(SyncOperation).order_by(
            SyncOperation.started_at.desc()).limit(5).all()
    except Exception:
        recent_operations = []
    
    # Get sync pairs for data sources info
    try:
        sync_pairs = db.session.query(SyncPair).all()
    except Exception:
        sync_pairs = []
    
    # If using the new UI, return data formatted for the new visualization
    if is_new_ui:
        # Getting metrics for visualization
        cpu_usage = latest_metrics.cpu_usage if latest_metrics else 30.0
        memory_usage = latest_metrics.memory_usage if latest_metrics else 50.0
        
        # Determine health statuses
        api_gateway_status = "online"
        sync_service_status_str = "online" if syncservice_status else "offline"
        database_status_str = "online" if db_status else "offline"
        
        # Check resource thresholds
        if latest_metrics:
            if cpu_usage > 90 or memory_usage > 95:
                api_gateway_status = "critical"
            elif cpu_usage > 70 or memory_usage > 80:
                api_gateway_status = "warning"
        
        # Build list of external systems from sync pairs
        external_systems = []
        for pair in sync_pairs:
            if pair.config and 'source_system' in pair.config:
                source_id = f"source_{pair.config['source_system']}"
                if not any(s.get('id') == source_id for s in external_systems):
                    external_systems.append({
                        "id": source_id,
                        "name": pair.config.get('source_name', pair.config['source_system']),
                        "type": "external",
                        "system_type": "source",
                        "description": f"Source system for {pair.name}",
                        "status": "online"
                    })
                    
            if pair.config and 'target_system' in pair.config:
                target_id = f"target_{pair.config['target_system']}"
                if not any(s.get('id') == target_id for s in external_systems):
                    external_systems.append({
                        "id": target_id,
                        "name": pair.config.get('target_name', pair.config['target_system']),
                        "type": "external",
                        "system_type": "target",
                        "description": f"Target system for {pair.name}",
                        "status": pair.active and "online" or "offline"
                    })
        
        # Use default systems if none found
        if not external_systems:
            external_systems = [
                {
                    "id": "pacs",
                    "name": "PACS System",
                    "type": "external",
                    "system_type": "source",
                    "description": "Picture Archiving and Communication System",
                    "status": "online"
                },
                {
                    "id": "cama",
                    "name": "CAMA System",
                    "type": "external",
                    "system_type": "target",
                    "description": "Content and Asset Management Application",
                    "status": "warning"
                }
            ]
        
        # Build the nodes list for D3 visualization
        nodes = [
            {
                "id": "apiGateway",
                "name": "API Gateway",
                "type": "gateway",
                "description": "Flask-based API Gateway",
                "status": api_gateway_status,
                "metrics": {
                    "cpu": round(cpu_usage, 1),
                    "memory": round(memory_usage, 1),
                    "uptime": "99.9%",
                    "response_time": latest_metrics.response_time if latest_metrics else 0.1
                }
            },
            {
                "id": "syncService",
                "name": "SyncService",
                "type": "service",
                "description": "Core synchronization service",
                "status": sync_service_status_str,
                "metrics": {
                    "cpu": round(cpu_usage * 0.8, 1),
                    "memory": round(memory_usage * 1.2, 1),
                    "operations": len([op for op in recent_operations if op.status == 'running']),
                    "total_operations": len(recent_operations)
                }
            },
            {
                "id": "database",
                "name": "PostgreSQL",
                "type": "database",
                "description": "Primary data store",
                "status": database_status_str,
                "metrics": {
                    "disk_usage": round(latest_metrics.disk_usage if latest_metrics else 25.0, 1),
                    "connections": latest_metrics.active_connections if latest_metrics else 2,
                    "size_mb": 25
                }
            }
        ]
        
        # Add external systems to nodes
        nodes.extend(external_systems)
        
        # Build connections for visualization
        connections = [
            {
                "source": "apiGateway",
                "target": "syncService",
                "type": "http",
                "active": syncservice_status,
                "label": "HTTP REST"
            },
            {
                "source": "syncService",
                "target": "database",
                "type": "sql",
                "active": db_status,
                "label": "SQL"
            }
        ]
        
        # Add connections to external systems
        for system in external_systems:
            if system["system_type"] == "source":
                connections.append({
                    "source": system["id"],
                    "target": "syncService",
                    "type": "api",
                    "active": system["status"] == "online",
                    "label": "Data Source"
                })
            else:
                connections.append({
                    "source": "syncService",
                    "target": system["id"],
                    "type": "api",
                    "active": system["status"] == "online",
                    "label": "Data Target"
                })
        
        # Format operations data
        operations_data = []
        for op in recent_operations:
            operations_data.append({
                "id": op.id,
                "type": op.operation_type,
                "status": op.status,
                "started_at": op.started_at.isoformat() if op.started_at else None,
                "completed_at": op.completed_at.isoformat() if op.completed_at else None,
                "pair_id": op.sync_pair_id,
                "pair_name": next((p.name for p in sync_pairs if p.id == op.sync_pair_id), "Unknown"),
                "total_records": op.total_records,
                "processed_records": op.processed_records,
                "success_rate": round((op.successful_records / op.total_records * 100) if op.total_records > 0 else 0, 1)
            })
        
        # Create response for new UI
        response_data = {
            "nodes": nodes,
            "connections": connections,
            "operations": operations_data,
            "timestamp": datetime.utcnow().isoformat(),
            "system_health": {
                "status": "healthy" if syncservice_status and db_status and cpu_usage < 80 and memory_usage < 80 else "degraded",
                "last_checked": latest_metrics.timestamp.isoformat() if latest_metrics else datetime.utcnow().isoformat(),
                "metrics": {
                    "cpu_usage": round(cpu_usage, 1),
                    "memory_usage": round(memory_usage, 1),
                    "disk_usage": round(latest_metrics.disk_usage if latest_metrics else 25.0, 1)
                }
            }
        }
    else:
        # Original format for the existing visualization
        # Define node statuses based on health checks
        api_gateway_status = "normal"
        sync_service_status = "normal" if syncservice_status else "error"
        database_status = "normal" if db_status else "error"
        
        # Set warning thresholds
        cpu_warning = 70.0
        cpu_critical = 90.0
        memory_warning = 80.0
        memory_critical = 95.0
        
        # Get metrics for status evaluation
        if latest_metrics:
            cpu_usage = latest_metrics.cpu_usage
            memory_usage = latest_metrics.memory_usage
            
            # Set status based on resource usage
            if cpu_usage > cpu_critical or memory_usage > memory_critical:
                api_gateway_status = "error"
                sync_service_status = "error" if syncservice_status else "error"
            elif cpu_usage > cpu_warning or memory_usage > memory_warning:
                api_gateway_status = "warning"
                sync_service_status = "warning" if syncservice_status else "error"
        
        # Build the architecture data structure with nodes and links
        nodes = [
            {
                "id": "client",
                "name": "Client Applications",
                "type": "client",
                "description": "End-user applications that interact with the TerraFusion SyncService platform",
                "status": "normal"
            },
            {
                "id": "api_gateway",
                "name": "API Gateway",
                "type": "api",
                "description": "Flask-based API Gateway that handles authentication, routing, and proxying to the SyncService",
                "status": api_gateway_status,
                "metrics": {
                    "cpu_usage": f"{latest_metrics.cpu_usage:.1f}%" if latest_metrics else "N/A",
                    "memory_usage": f"{latest_metrics.memory_usage:.1f}%" if latest_metrics else "N/A",
                    "response_time": f"{latest_metrics.response_time:.3f}s" if latest_metrics else "N/A",
                    "error_count": str(latest_metrics.error_count) if latest_metrics else "N/A"
                } if latest_metrics else {}
            },
            {
                "id": "sync_service",
                "name": "SyncService",
                "type": "service",
                "description": "Core FastAPI-based service that implements the data synchronization and transformation logic",
                "status": sync_service_status,
                "metrics": {
                    "cpu_usage": f"{latest_metrics.cpu_usage:.1f}%" if latest_metrics else "N/A",
                    "memory_usage": f"{latest_metrics.memory_usage:.1f}%" if latest_metrics else "N/A",
                    "active_connections": str(latest_metrics.active_connections) if latest_metrics else "N/A",
                    "sync_operations": str(latest_metrics.sync_operations_count) if latest_metrics else "N/A"
                } if latest_metrics else {}
            },
            {
                "id": "database",
                "name": "PostgreSQL Database",
                "type": "database",
                "description": "Primary database storing configuration, metrics, audit entries, and operation state",
                "status": database_status,
                "metrics": {
                    "disk_usage": f"{latest_metrics.disk_usage:.1f}%" if latest_metrics else "N/A"
                } if latest_metrics else {}
            },
            {
                "id": "auth_service",
                "name": "Authentication Service",
                "type": "auth",
                "description": "Handles user authentication and authorization, integrated with County's Azure AD",
                "status": "normal"
            },
            {
                "id": "pacs_system",
                "name": "PACS System",
                "type": "service",
                "description": "Legacy Picture Archiving and Communication System",
                "status": "normal"
            },
            {
                "id": "cama_system",
                "name": "CAMA System",
                "type": "service",
                "description": "Computer Assisted Mass Appraisal System",
                "status": "normal"
            },
            {
                "id": "metrics_handler",
                "name": "Metrics Collector",
                "type": "service",
                "description": "Component responsible for collecting and storing system metrics",
                "status": "normal" if latest_metrics else "warning",
                "statusDetails": "Last collection: " + (latest_metrics.timestamp.strftime("%Y-%m-%d %H:%M:%S") if latest_metrics else "Never")
            },
            {
                "id": "self_healing",
                "name": "Self-Healing System",
                "type": "service",
                "description": "Autonomous recovery system with circuit breakers and retry orchestration",
                "status": "normal"
            }
        ]
        
        # Define the relationships between components
        links = [
            {
                "source": "client",
                "target": "api_gateway",
                "description": "HTTP/HTTPS requests"
            },
            {
                "source": "api_gateway",
                "target": "sync_service",
                "description": "Internal HTTP requests",
                "status": "error" if not syncservice_status else None
            },
            {
                "source": "api_gateway",
                "target": "database",
                "description": "SQL queries via SQLAlchemy",
                "status": "error" if not db_status else None
            },
            {
                "source": "api_gateway",
                "target": "auth_service",
                "description": "Authentication requests"
            },
            {
                "source": "sync_service",
                "target": "database",
                "description": "SQL queries via SQLAlchemy",
                "status": "error" if not db_status else None
            },
            {
                "source": "sync_service",
                "target": "pacs_system",
                "description": "Data extraction and synchronization"
            },
            {
                "source": "sync_service",
                "target": "cama_system",
                "description": "Data insertion and validation"
            },
            {
                "source": "metrics_handler",
                "target": "sync_service",
                "description": "Metrics collection",
                "status": "error" if not syncservice_status else None
            },
            {
                "source": "metrics_handler",
                "target": "database",
                "description": "Metrics storage",
                "status": "error" if not db_status else None
            },
            {
                "source": "self_healing",
                "target": "sync_service",
                "description": "Service monitoring and recovery",
                "status": "error" if not syncservice_status else None
            },
            {
                "source": "self_healing",
                "target": "database",
                "description": "State persistence",
                "status": "error" if not db_status else None
            }
        ]
        
        # Use original format for response
        response_data = {
            "nodes": nodes,
            "links": links,
            "timestamp": datetime.utcnow().isoformat(),
            "system_status": "healthy" if syncservice_status and db_status else "degraded"
        }
    
    # Create audit entry for architecture view access
    try:
        user = get_current_user()
        create_audit_log(
            event_type="architecture_view",
            resource_type="system",
            description="Architecture visualization data accessed",
            severity="info",
            user_id=getattr(user, 'id', None),
            username=getattr(user, 'username', None)
        )
    except Exception as e:
        logger.error(f"Failed to create audit log for architecture view: {str(e)}")
    
    return jsonify(response_data)


@app.route('/api/metrics/status')
@requires_auth
def get_metrics_status():
    """Get status information about metrics collection."""
    # Get the most recent metrics
    most_recent = db.session.query(SystemMetrics).order_by(
        SystemMetrics.timestamp.desc()).first()
    
    # Get timestamp of most recent collection
    now = datetime.utcnow()
    last_collection_time = most_recent.timestamp if most_recent else None
    time_since_last = (now - last_collection_time).total_seconds() if last_collection_time else None
    
    # Get metrics collection failure audit logs
    recent_failures = db.session.query(AuditEntry).filter(
        AuditEntry.event_type.in_(['metrics_collection_failed', 'metrics_collection_error'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    # Get metrics collection retry success logs
    recent_retries = db.session.query(AuditEntry).filter_by(
        event_type='metrics_collection_retry_success'
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    # Get count of metrics in the last 24 hours
    day_ago = now - timedelta(days=1)
    count_24h = db.session.query(SystemMetrics).filter(
        SystemMetrics.timestamp >= day_ago
    ).count()
    
    # Determine health status
    health_status = "healthy"
    health_message = "Metrics collection operating normally"
    
    if not most_recent:
        health_status = "critical"
        health_message = "No metrics have been collected"
    elif time_since_last and time_since_last > 300:  # 5 minutes
        health_status = "warning"
        health_message = f"No metrics collected in the last {int(time_since_last/60)} minutes"
    elif recent_failures and len(recent_failures) > 2:
        health_status = "warning"
        health_message = f"Multiple collection failures detected ({len(recent_failures)} recent failures)"
    
    return jsonify({
        "status": health_status,
        "message": health_message,
        "last_collection": last_collection_time.isoformat() if last_collection_time else None,
        "time_since_last_collection_seconds": time_since_last,
        "collections_last_24h": count_24h,
        "recent_failures": [failure.to_dict() for failure in recent_failures],
        "recent_retries": [retry.to_dict() for retry in recent_retries],
        "syncservice_available": check_syncservice_status(),
        "timestamp": now.isoformat()
    })


@app.route('/api/audit', methods=['GET'])
@requires_auth
def get_audit_entries():
    """
    Get audit trail entries with filtering options.
    
    Query parameters:
        - from_date: ISO-formatted date to filter events from
        - to_date: ISO-formatted date to filter events to
        - event_type: Type of event to filter (e.g., 'sync_started')
        - resource_type: Type of resource to filter (e.g., 'sync_pair')
        - resource_id: ID of resource to filter
        - operation_id: ID of sync operation to filter
        - severity: Severity level to filter (e.g., 'error')
        - limit: Maximum number of entries to return (default: 100)
    """
    # Parse query parameters
    try:
        from_date = request.args.get('from_date')
        if from_date:
            from_date = datetime.fromisoformat(from_date.replace('Z', '+00:00'))
        
        to_date = request.args.get('to_date')
        if to_date:
            to_date = datetime.fromisoformat(to_date.replace('Z', '+00:00'))
    except ValueError:
        return jsonify({
            "error": "Invalid date format",
            "message": "Dates must be in ISO format (YYYY-MM-DDTHH:MM:SS.sssZ)"
        }), 400
    
    event_type = request.args.get('event_type')
    resource_type = request.args.get('resource_type')
    resource_id = request.args.get('resource_id')
    operation_id = request.args.get('operation_id', type=int)
    severity = request.args.get('severity')
    limit = request.args.get('limit', 100, type=int)
    
    # Build query
    query = db.session.query(AuditEntry)
    
    if from_date:
        query = query.filter(AuditEntry.timestamp >= from_date)
    
    if to_date:
        query = query.filter(AuditEntry.timestamp <= to_date)
    
    if event_type:
        query = query.filter(AuditEntry.event_type == event_type)
    
    if resource_type:
        query = query.filter(AuditEntry.resource_type == resource_type)
    
    if resource_id:
        query = query.filter(AuditEntry.resource_id == resource_id)
    
    if operation_id:
        query = query.filter(AuditEntry.operation_id == operation_id)
    
    if severity:
        query = query.filter(AuditEntry.severity == severity)
    
    # Execute query with limit and order by timestamp
    entries = query.order_by(AuditEntry.timestamp.desc()).limit(limit).all()
    
    return jsonify([entry.to_dict() for entry in entries])


@app.route('/api/audit/<int:audit_id>', methods=['GET'])
@requires_auth
def get_audit_entry(audit_id):
    """Get a specific audit entry by ID."""
    entry = db.session.query(AuditEntry).get_or_404(audit_id)
    return jsonify(entry.to_dict())


@app.route('/api/audit/summary', methods=['GET'])
@requires_auth
def get_audit_summary():
    """
    Get audit trail summary statistics.
    
    Returns counts and latest events grouped by event type and severity.
    """
    # Get count by event type
    event_type_counts = db.session.query(
        AuditEntry.event_type, 
        db.func.count(AuditEntry.id)
    ).group_by(AuditEntry.event_type).all()
    
    # Get count by severity
    severity_counts = db.session.query(
        AuditEntry.severity, 
        db.func.count(AuditEntry.id)
    ).group_by(AuditEntry.severity).all()
    
    # Get latest entry timestamp
    latest_entry = db.session.query(AuditEntry).order_by(
        AuditEntry.timestamp.desc()
    ).first()
    
    # Get latest error events
    latest_errors = db.session.query(AuditEntry).filter(
        AuditEntry.severity.in_(['error', 'critical'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    return jsonify({
        "total_entries": db.session.query(AuditEntry).count(),
        "latest_timestamp": latest_entry.timestamp.isoformat() if latest_entry else None,
        "event_type_counts": dict(event_type_counts),
        "severity_counts": dict(severity_counts),
        "latest_errors": [error.to_dict() for error in latest_errors]
    })


@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@requires_auth
def proxy(path):
    """
    Proxy API requests to the SyncService.
    
    This function forwards requests to the SyncService and returns its responses.
    """
    if not check_syncservice_status():
        return jsonify({
            "error": "SyncService is not available",
            "message": "The SyncService component is currently offline."
        }), 503
    
    # Forward the request to the SyncService
    target_url = urljoin(f"{SYNCSERVICE_BASE_URL}/", path)
    
    try:
        # Forward the request with the same method, headers, and body
        response = requests.request(
            method=request.method,
            url=target_url,
            headers={key: value for key, value in request.headers
                    if key.lower() not in ['host', 'content-length']},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            timeout=10
        )
        
        # Create a Flask response from the SyncService response
        flask_response = Response(
            response.content,
            status=response.status_code,
            headers=dict(response.headers)
        )
        
        return flask_response
        
    except requests.RequestException as e:
        return jsonify({
            "error": "SyncService communication error",
            "message": str(e)
        }), 500


# Utility function for creating audit log entries
def create_audit_log(
    event_type: str,
    resource_type: str,
    description: str,
    resource_id: str = None,
    operation_id: int = None,
    previous_state: dict = None,
    new_state: dict = None,
    severity: str = "info",
    user_id: str = None,
    username: str = None,
    ip_address: str = None,
    correlation_id: str = None,
    **kwargs
) -> AuditEntry:
    """
    Create and save an audit log entry.
    
    Args:
        event_type: Type of event (e.g., 'sync_started', 'sync_completed', 'config_changed')
        resource_type: Type of resource (e.g., 'sync_pair', 'operation', 'system_config')
        description: Human-readable description of the event
        resource_id: ID of the resource (if applicable)
        operation_id: ID of the sync operation (if applicable)
        previous_state: JSON representation of previous state for tracking changes
        new_state: JSON representation of new state for tracking changes
        severity: Event severity ('info', 'warning', 'error', 'critical')
        user_id: ID of the user who performed the action (if available)
        username: Username of the user who performed the action (if available)
        correlation_id: Unique ID for tracing related events
    
    Returns:
        The created AuditEntry instance
    """
    # Get current user if available and not provided
    if not user_id or not username:
        current_user = get_current_user()
        if current_user:
            user_id = user_id or current_user.get('id')
            username = username or current_user.get('username')
    
    # Get client information from request
    ip_address = request.remote_addr if request else None
    user_agent = request.user_agent.string if request and request.user_agent else None
    
    # Create audit entry
    entry = AuditEntry(
        event_type=event_type,
        resource_type=resource_type,
        resource_id=resource_id,
        operation_id=operation_id,
        description=description,
        previous_state=previous_state,
        new_state=new_state,
        severity=severity,
        user_id=user_id,
        username=username,
        ip_address=ip_address,
        correlation_id=correlation_id
    )
    
    # Set user_agent separately to avoid compatibility issues
    if user_agent:
        entry.user_agent = user_agent
    
    # Save to database
    db.session.add(entry)
    db.session.commit()
    
    return entry


# Create database tables if they don't exist
with app.app_context():
    db.create_all()


# Add some initial data if the database is empty
def seed_initial_data():
    """Seed the database with initial data if it's empty."""
    with app.app_context():
        # Check if we have any sync pairs
        if db.session.query(SyncPair).count() == 0:
            # Add some sample sync pairs
            sample_pairs = [
                SyncPair(
                    name="PACS-CAMA Integration",
                    description="Synchronize property data between PACS and CAMA systems",
                    source_system="PACS",
                    target_system="CAMA",
                    config={
                        "entity_types": ["property", "owner", "valuation"],
                        "sync_interval_hours": 24,
                        "batch_size": 100
                    }
                ),
                SyncPair(
                    name="GIS-ERP Integration",
                    description="Sync geographical data with ERP system",
                    source_system="GIS",
                    target_system="ERP",
                    config={
                        "entity_types": ["location", "boundary", "zone"],
                        "sync_interval_hours": 48,
                        "batch_size": 50
                    }
                )
            ]
            
            for pair in sample_pairs:
                db.session.add(pair)
            
            # Add some sample operations
            sample_operations = [
                SyncOperation(
                    sync_pair_id=1,
                    operation_type="full",
                    status="completed",
                    started_at=datetime(2023, 1, 1, 8, 0, 0),
                    completed_at=datetime(2023, 1, 1, 10, 30, 0),
                    total_records=5000,
                    processed_records=5000,
                    successful_records=4950,
                    failed_records=50,
                    metrics={
                        "duration_seconds": 9000,
                        "avg_processing_time_ms": 1800,
                        "peak_memory_mb": 256
                    }
                ),
                SyncOperation(
                    sync_pair_id=1,
                    operation_type="incremental",
                    status="completed",
                    started_at=datetime(2023, 1, 2, 8, 0, 0),
                    completed_at=datetime(2023, 1, 2, 8, 45, 0),
                    total_records=150,
                    processed_records=150,
                    successful_records=148,
                    failed_records=2,
                    metrics={
                        "duration_seconds": 2700,
                        "avg_processing_time_ms": 1200,
                        "peak_memory_mb": 128
                    }
                )
            ]
            
            for op in sample_operations:
                db.session.add(op)
            
            # Add some system metrics
            sample_metrics = [
                SystemMetrics(
                    service="sync_service",
                    status="healthy",
                    timestamp=datetime(2023, 1, 1, 8, 0, 0),
                    cpu_usage=45.2,
                    memory_usage=60.5,
                    disk_usage=32.1,
                    active_connections=12,
                    response_time=0.85,
                    error_count=0,
                    sync_operations_count=1
                ),
                SystemMetrics(
                    service="sync_service",
                    status="healthy",
                    timestamp=datetime(2023, 1, 1, 9, 0, 0),
                    cpu_usage=78.3,
                    memory_usage=72.8,
                    disk_usage=32.2,
                    active_connections=15,
                    response_time=1.2,
                    error_count=2,
                    sync_operations_count=1
                )
            ]
            
            for metric in sample_metrics:
                db.session.add(metric)
            
            # Add sample audit entries
            sample_audit_entries = [
                AuditEntry(
                    timestamp=datetime(2023, 1, 1, 8, 0, 0),
                    user_id="system",
                    username="system",
                    event_type="sync_started",
                    resource_type="sync_operation",
                    resource_id="1",
                    operation_id=1,
                    description="Full synchronization started for PACS-CAMA Integration",
                    ip_address="127.0.0.1",
                    severity="info",
                    correlation_id="corr-123456"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 1, 10, 30, 0),
                    user_id="system",
                    username="system",
                    event_type="sync_completed",
                    resource_type="sync_operation",
                    resource_id="1",
                    operation_id=1,
                    description="Full synchronization completed for PACS-CAMA Integration: 4950 successful, 50 failed records",
                    ip_address="127.0.0.1",
                    severity="info",
                    correlation_id="corr-123456"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 1, 10, 30, 0),
                    user_id="system",
                    username="system",
                    event_type="error_detected",
                    resource_type="sync_record",
                    resource_id="property-12345",
                    operation_id=1,
                    description="Failed to sync property data: Invalid format in source system",
                    previous_state={"status": "pending"},
                    new_state={"status": "error", "error_code": "FORMAT_ERROR"},
                    ip_address="127.0.0.1",
                    severity="error",
                    correlation_id="corr-123456"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 2, 8, 0, 0),
                    user_id="admin",
                    username="admin",
                    event_type="sync_started",
                    resource_type="sync_operation",
                    resource_id="2",
                    operation_id=2,
                    description="Incremental synchronization started for PACS-CAMA Integration",
                    ip_address="192.168.1.100",
                    severity="info",
                    correlation_id="corr-789012"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 2, 8, 45, 0),
                    user_id="admin",
                    username="admin",
                    event_type="sync_completed",
                    resource_type="sync_operation",
                    resource_id="2",
                    operation_id=2,
                    description="Incremental synchronization completed for PACS-CAMA Integration: 148 successful, 2 failed records",
                    ip_address="192.168.1.100",
                    severity="info",
                    correlation_id="corr-789012"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 3, 14, 30, 0),
                    user_id="admin",
                    username="admin",
                    event_type="config_changed",
                    resource_type="sync_pair",
                    resource_id="1",
                    description="Updated sync configuration for PACS-CAMA Integration",
                    previous_state={"sync_interval_hours": 24, "batch_size": 100},
                    new_state={"sync_interval_hours": 12, "batch_size": 200},
                    ip_address="192.168.1.100",
                    severity="info"
                ),
                AuditEntry(
                    timestamp=datetime(2023, 1, 4, 9, 15, 0),
                    user_id="system",
                    username="system",
                    event_type="system_alert",
                    resource_type="system",
                    description="High CPU usage detected (85%)",
                    ip_address="127.0.0.1",
                    severity="warning"
                )
            ]
            
            for entry in sample_audit_entries:
                db.session.add(entry)
            
            db.session.commit()
            
            # Create a current audit entry using the utility function
            create_audit_log(
                event_type="system_startup",
                resource_type="system",
                description="Application initialized and database seeded with sample data",
                severity="info"
            )
            
            logger.info("Database seeded with initial sample data")


# Function to collect metrics on a periodic basis
def start_metrics_collection(interval_seconds=60):
    """
    Start collecting metrics from SyncService on a periodic basis.
    
    Args:
        interval_seconds: Interval between metrics collections in seconds
    """
    import threading
    
    def metrics_collector_thread():
        while True:
            try:
                # Only collect metrics if SyncService is running
                if check_syncservice_status():
                    logger.info("Collecting metrics from SyncService")
                    metrics = collect_syncservice_metrics()
                    if metrics:
                        logger.info("Successfully collected metrics")
                    else:
                        logger.warning("Failed to collect metrics")
                else:
                    logger.warning("SyncService not available, skipping metrics collection")
                
                # Sleep for the specified interval
                time.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Error in metrics collector thread: {str(e)}")
                # Sleep for a short interval and try again
                time.sleep(5)
    
    # Start the metrics collector thread as a daemon
    thread = threading.Thread(target=metrics_collector_thread, daemon=True)
    thread.start()
    logger.info(f"Started metrics collection thread with interval of {interval_seconds}s")
    return thread


if __name__ == '__main__':
    # Seed the database with initial data if it's empty
    seed_initial_data()
    
    # Try to collect metrics immediately if SyncService is available
    if check_syncservice_status():
        collect_syncservice_metrics()
    
    # Start periodic metrics collection in the background
    start_metrics_collection(interval_seconds=60)
    
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)