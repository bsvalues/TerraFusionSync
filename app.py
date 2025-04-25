"""
TerraFusion SyncService API Gateway

This module provides the main Flask application that serves as the API Gateway
for the TerraFusion SyncService platform.
"""
import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

from flask import Flask, jsonify, request, render_template, redirect, url_for, Response, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

from models import db, SyncPair, SyncOperation, SystemMetrics
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

# SyncService connection settings
SYNCSERVICE_BASE_URL = "http://0.0.0.0:8080"


def ensure_syncservice_running() -> bool:
    """
    Ensure the SyncService is running.
    If not, attempt to start it in the background.
    
    Returns:
        bool: True if the SyncService is running or was started successfully
    """
    if check_syncservice_status():
        return True
    
    try:
        logger.info("SyncService not running, attempting to start it...")
        # This would typically start the service in a background process or workflow
        # For now, we'll just return False as we don't have direct process control
        return False
    except Exception as e:
        logger.error(f"Failed to start SyncService: {str(e)}")
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


@app.route('/api/sync-pairs/<int:pair_id>', methods=['GET'])
@requires_auth
def get_sync_pair(pair_id):
    """Get a specific sync pair by ID."""
    pair = SyncPair.query.get_or_404(pair_id)
    return jsonify(pair.to_dict())


@app.route('/api/sync-operations', methods=['GET'])
@requires_auth
def get_sync_operations():
    """Get all sync operations, with optional filtering."""
    pair_id = request.args.get('pair_id', type=int)
    status = request.args.get('status')
    
    query = SyncOperation.query
    
    if pair_id:
        query = query.filter_by(sync_pair_id=pair_id)
    
    if status:
        query = query.filter_by(status=status)
    
    operations = query.order_by(SyncOperation.started_at.desc()).all()
    return jsonify([op.to_dict() for op in operations])


@app.route('/api/metrics', methods=['GET'])
@requires_auth
def get_metrics():
    """Get system metrics."""
    limit = request.args.get('limit', 100, type=int)
    
    metrics = SystemMetrics.query.order_by(
        SystemMetrics.timestamp.desc()).limit(limit).all()
    
    return jsonify([metric.to_dict() for metric in metrics])


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
            
            db.session.commit()
            logger.info("Database seeded with initial sample data")


if __name__ == '__main__':
    # Seed the database with initial data if it's empty
    seed_initial_data()
    # Run the Flask development server
    app.run(host='0.0.0.0', port=5000, debug=True)