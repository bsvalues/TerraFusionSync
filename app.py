"""
TerraFusion SyncService API Gateway

This module provides the main Flask application that serves as the API Gateway
for the TerraFusion SyncService platform.
"""
import os
import json
import logging
import requests
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from flask import Flask, jsonify, request, render_template, redirect, url_for, Response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from models import db, SyncPair, SyncOperation, SystemMetrics, AuditEntry

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
# Import authentication module
try:
    from apps.backend.api.auth import requires_auth, init_auth_routes, get_current_user
except ImportError:
    # Provide fallback if auth module isn't available
    logging.warning("Auth module not available, using fallback implementation")
    
    def requires_auth(f):
        """Fallback auth decorator that doesn't require authentication."""
        return f
    
    def init_auth_routes(app):
        """Fallback auth routes initializer."""
        pass
    
    def get_current_user():
        """Fallback current user function."""
        return None

# Create and configure the Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terraFusionSyncServiceSecret")

# Configure the database connection
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the database with the Flask app
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
        # Run the service health check in a separate thread
        thread = threading.Thread(target=lambda: check_and_ensure_service_health())
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
            timestamp=timestamp,
            cpu_usage=system_data.get("cpu_usage_percent", 0.0),
            memory_usage=system_data.get("memory_usage_percent", 0.0),
            disk_usage=system_data.get("disk_usage_percent", 0.0),
            active_connections=system_data.get("active_connections", 0),
            response_time=metrics_data.get("performance", {}).get("response_time_avg_ms", 0.0) / 1000,
            error_count=metrics_data.get("performance", {}).get("error_count", 0),
            sync_operations_count=metrics_data.get("performance", {}).get("sync_operations_count", 0)
        )
        
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
                        "active_connections": metrics.active_connections,
                        "error_count": metrics.error_count,
                        "sync_operations_count": metrics.sync_operations_count
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


@app.route('/')
def root():
    """Root endpoint for the API Gateway."""
    return render_template('index.html', 
                          service_status=check_syncservice_status(),
                          sync_pairs=SyncPair.query.all())


@app.route('/dashboard')
@requires_auth
def dashboard():
    """Main dashboard view."""
    user = get_current_user()
    return render_template('dashboard.html', user=user)


@app.route('/dashboard/sync')
@requires_auth
def sync_dashboard():
    """Sync operations dashboard."""
    user = get_current_user()
    return render_template('sync_dashboard.html',
                          user=user,
                          sync_pairs=SyncPair.query.all(),
                          recent_operations=SyncOperation.query.order_by(
                              SyncOperation.started_at.desc()).limit(10).all())


@app.route('/dashboard/metrics')
@requires_auth
def metrics_dashboard():
    """Metrics dashboard."""
    user = get_current_user()
    return render_template('metrics_dashboard.html',
                          user=user,
                          system_metrics=SystemMetrics.query.order_by(
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
    query = AuditEntry.query
    
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
    
    latest_entry = AuditEntry.query.order_by(
        AuditEntry.timestamp.desc()
    ).first()
    
    latest_errors = AuditEntry.query.filter(
        AuditEntry.severity.in_(['error', 'critical'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    summary = {
        "total_entries": AuditEntry.query.count(),
        "latest_timestamp": latest_entry.timestamp if latest_entry else None,
        "event_type_counts": dict(event_type_counts),
        "severity_counts": dict(severity_counts),
        "latest_errors": latest_errors
    }
    
    return render_template('audit_dashboard.html',
                          user=user,
                          audit_entries=audit_entries,
                          summary=summary)


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
    
    return jsonify({
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api_gateway": "online",
            "sync_service": "online" if syncservice_status else "offline",
            "database": "online"  # This would normally check the database connection
        },
        "version": "0.1.0"
    })

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
        recent_metrics = SystemMetrics.query.order_by(
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
    pairs = SyncPair.query.all()
    return jsonify([pair.to_dict() for pair in pairs])


@app.route('/api/sync-pairs/<int:pair_id>', methods=['GET', 'PUT'])
@requires_auth
def get_sync_pair(pair_id):
    """Get or update a specific sync pair by ID."""
    pair = SyncPair.query.get_or_404(pair_id)
    
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
        
        query = SyncOperation.query
        
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
        sync_pair = SyncPair.query.get(data['sync_pair_id'])
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


@app.route('/api/metrics', methods=['GET'])
@requires_auth
@app.route('/api/system-metrics')
def get_system_metrics():
    """Get system metrics from the database."""
    limit = request.args.get('limit', 100, type=int)
    
    system_metrics = SystemMetrics.query.order_by(
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

@app.route('/api/metrics/status')
@requires_auth
def get_metrics_status():
    """Get status information about metrics collection."""
    # Get the most recent metrics
    most_recent = SystemMetrics.query.order_by(
        SystemMetrics.timestamp.desc()).first()
    
    # Get timestamp of most recent collection
    now = datetime.utcnow()
    last_collection_time = most_recent.timestamp if most_recent else None
    time_since_last = (now - last_collection_time).total_seconds() if last_collection_time else None
    
    # Get metrics collection failure audit logs
    recent_failures = AuditEntry.query.filter(
        AuditEntry.event_type.in_(['metrics_collection_failed', 'metrics_collection_error'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    # Get metrics collection retry success logs
    recent_retries = AuditEntry.query.filter_by(
        event_type='metrics_collection_retry_success'
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    # Get count of metrics in the last 24 hours
    day_ago = now - timedelta(days=1)
    count_24h = SystemMetrics.query.filter(
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
    query = AuditEntry.query
    
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
    entry = AuditEntry.query.get_or_404(audit_id)
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
    latest_entry = AuditEntry.query.order_by(
        AuditEntry.timestamp.desc()
    ).first()
    
    # Get latest error events
    latest_errors = AuditEntry.query.filter(
        AuditEntry.severity.in_(['error', 'critical'])
    ).order_by(AuditEntry.timestamp.desc()).limit(5).all()
    
    return jsonify({
        "total_entries": AuditEntry.query.count(),
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


# Initialize authentication routes
init_auth_routes(app)

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
    correlation_id: str = None
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
        user_agent=user_agent,
        correlation_id=correlation_id
    )
    
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
        if SyncPair.query.count() == 0:
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