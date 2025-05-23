"""
TerraFusion Platform - Main Application

This module provides the Flask application for the TerraFusion Platform.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create SQLAlchemy base class
class Base(DeclarativeBase):
    pass

# Initialize Flask app and SQLAlchemy
db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terrafusion-dev-key")

# Configure ProxyFix for proper URL generation
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///terrafusion.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions
db.init_app(app)

# Setup database initialization with app context
with app.app_context():
    # Create tables
    db.create_all()

# Define models
class SyncPair(db.Model):
    """Model representing a synchronization pair between two systems."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    source_system = db.Column(db.String(50), nullable=False)
    target_system = db.Column(db.String(50), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    county_id = db.Column(db.String(50), nullable=False)
    config = db.Column(db.JSON)

class SyncOperation(db.Model):
    """Model representing a synchronization operation."""
    id = db.Column(db.Integer, primary_key=True)
    sync_pair_id = db.Column(db.Integer, db.ForeignKey('sync_pair.id'))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    records_processed = db.Column(db.Integer, default=0)
    records_created = db.Column(db.Integer, default=0)
    records_updated = db.Column(db.Integer, default=0)
    records_deleted = db.Column(db.Integer, default=0)
    errors = db.Column(db.Integer, default=0)
    error_details = db.Column(db.JSON)
    user_id = db.Column(db.String(50))
    
    # Relationship
    sync_pair = db.relationship('SyncPair', backref='operations')

class GisExportJob(db.Model):
    """Model representing a GIS export job."""
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True)
    county_id = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    export_format = db.Column(db.String(20), nullable=False)
    area_of_interest = db.Column(db.JSON, nullable=False)
    layers = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    download_url = db.Column(db.String(500))
    result_file_location = db.Column(db.String(500))
    result_file_size_kb = db.Column(db.Integer)
    result_record_count = db.Column(db.Integer)
    message = db.Column(db.String(500))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SystemMetric(db.Model):
    """Model representing system performance metrics."""
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(50), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    metric_metadata = db.Column(db.JSON)

class AuditEntry(db.Model):
    """Model representing an audit log entry."""
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)
    resource_id = db.Column(db.String(50))
    operation_id = db.Column(db.Integer)
    description = db.Column(db.Text, nullable=False)
    previous_state = db.Column(db.JSON)
    new_state = db.Column(db.JSON)
    severity = db.Column(db.String(20), default="info")
    user_id = db.Column(db.String(50))
    username = db.Column(db.String(100))
    ip_address = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    correlation_id = db.Column(db.String(36))

# Seed initial data
def seed_initial_data():
    """Seed the database with initial data."""
    # Check if we need to seed data
    if db.session.query(SyncPair).count() == 0:
        logger.info("Seeding initial data...")
        
        # Sample Sync Pairs
        sync_pairs = [
            {
                "name": "PACS-CAMA Integration",
                "description": "Synchronize property data between PACS and CAMA systems",
                "source_system": "PACS",
                "target_system": "CAMA",
                "active": True,
                "county_id": "benton-wa",
                "config": {
                    "entity_types": ["property", "owner", "valuation"],
                    "sync_interval_hours": 24,
                    "batch_size": 100
                }
            },
            {
                "name": "GIS-ERP Integration",
                "description": "Sync geographical data with ERP system",
                "source_system": "GIS",
                "target_system": "ERP",
                "active": True,
                "county_id": "benton-wa",
                "config": {
                    "entity_types": ["location", "boundary", "zone"],
                    "sync_interval_hours": 48,
                    "batch_size": 50
                }
            }
        ]
        
        for sync_pair_data in sync_pairs:
            sync_pair = SyncPair(**sync_pair_data)
            db.session.add(sync_pair)
        
        # Sample GIS Export Jobs
        gis_exports = [
            {
                "job_id": "abc123",
                "county_id": "benton-wa",
                "username": "admin",
                "export_format": "geojson",
                "area_of_interest": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "layers": ["parcels", "buildings"],
                "status": "COMPLETED",
                "created_at": datetime.utcnow() - timedelta(hours=1),
                "started_at": datetime.utcnow() - timedelta(minutes=55),
                "completed_at": datetime.utcnow() - timedelta(minutes=50),
                "download_url": "/api/v1/gis-export/download/abc123",
                "message": "Export completed successfully"
            }
        ]
        
        for export_data in gis_exports:
            export_job = GisExportJob(**export_data)
            db.session.add(export_job)
        
        # Sample Audit Entries
        audit_entries = [
            {
                "event_type": "sync_started",
                "resource_type": "sync_pair",
                "resource_id": "1",
                "description": "Sync operation started for PACS-CAMA Integration",
                "severity": "info",
                "username": "admin",
                "created_at": datetime.utcnow() - timedelta(hours=2)
            },
            {
                "event_type": "sync_completed",
                "resource_type": "sync_pair",
                "resource_id": "1",
                "description": "Sync operation completed successfully for PACS-CAMA Integration",
                "severity": "info",
                "username": "admin",
                "created_at": datetime.utcnow() - timedelta(hours=1, minutes=45)
            }
        ]
        
        for audit_data in audit_entries:
            audit_entry = AuditEntry(**audit_data)
            db.session.add(audit_entry)
        
        # Commit all changes
        db.session.commit()
        logger.info("Finished seeding initial data")

# Routes
@app.route('/')
def index():
    """Root endpoint redirects to dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')

@app.route('/sync/dashboard')
def sync_dashboard():
    """Sync operations dashboard."""
    sync_pairs = SyncPair.query.all()
    recent_operations = SyncOperation.query.order_by(SyncOperation.created_at.desc()).limit(10).all()
    return render_template('sync_dashboard.html', sync_pairs=sync_pairs, operations=recent_operations)

@app.route('/gis/dashboard')
def gis_dashboard():
    """GIS export dashboard."""
    recent_exports = GisExportJob.query.order_by(GisExportJob.created_at.desc()).limit(10).all()
    return render_template('gis_dashboard.html', exports=recent_exports)

@app.route('/sync/pairs')
def sync_pairs():
    """Sync pairs management page."""
    sync_pairs = SyncPair.query.all()
    return render_template('sync_pairs.html', sync_pairs=sync_pairs)

@app.route('/sync/operations')
def sync_operations():
    """View sync operations."""
    operations = SyncOperation.query.order_by(SyncOperation.created_at.desc()).all()
    return render_template('sync_operations.html', operations=operations)

@app.route('/api/sync/pairs', methods=['GET'])
def api_sync_pairs():
    """API endpoint to get sync pairs."""
    sync_pairs = SyncPair.query.all()
    result = []
    for pair in sync_pairs:
        result.append({
            'id': pair.id,
            'name': pair.name,
            'description': pair.description,
            'source_system': pair.source_system,
            'target_system': pair.target_system,
            'active': pair.active,
            'county_id': pair.county_id,
            'config': pair.config
        })
    return jsonify(result)

@app.route('/api/sync/operations', methods=['GET'])
def api_sync_operations():
    """API endpoint to get sync operations."""
    operations = SyncOperation.query.order_by(SyncOperation.created_at.desc()).limit(50).all()
    result = []
    for op in operations:
        result.append({
            'id': op.id,
            'sync_pair_id': op.sync_pair_id,
            'status': op.status,
            'created_at': op.created_at.isoformat() if op.created_at else None,
            'started_at': op.started_at.isoformat() if op.started_at else None,
            'completed_at': op.completed_at.isoformat() if op.completed_at else None,
            'records_processed': op.records_processed,
            'records_created': op.records_created,
            'records_updated': op.records_updated,
            'records_deleted': op.records_deleted,
            'errors': op.errors
        })
    return jsonify(result)

@app.route('/api/gis/exports', methods=['GET'])
def api_gis_exports():
    """API endpoint to get GIS export jobs."""
    exports = GisExportJob.query.order_by(GisExportJob.created_at.desc()).limit(50).all()
    result = []
    for exp in exports:
        result.append({
            'id': exp.id,
            'job_id': exp.job_id,
            'county_id': exp.county_id,
            'username': exp.username,
            'export_format': exp.export_format,
            'status': exp.status,
            'created_at': exp.created_at.isoformat() if exp.created_at else None,
            'completed_at': exp.completed_at.isoformat() if exp.completed_at else None,
            'download_url': exp.download_url
        })
    return jsonify(result)

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'TerraFusion Platform',
        'version': '1.0.0'
    })

# Initialize application
with app.app_context():
    db.create_all()
    seed_initial_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)