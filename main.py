"""
TerraFusion Platform - Enterprise Application

This module provides the Flask application for the TerraFusion Platform,
including the dashboard and API endpoints for GIS Export functionality.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import services
from gis_export import gis_export_service
from sync_service import sync_service

# Import Benton District Lookup service
from benton_district_lookup import BentonDistrictLookup

# Import database models
from models import db, init_db, County, User, GisExportJob, SyncJob, model_to_dict

# Import monitoring module
from monitoring import monitoring, track_gis_export_job, track_sync_job, track_export_file_size

# Import backup scheduler
from backup_scheduler import backup_scheduler, start_backup_service

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terrafusion-dev-key")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize database
init_db(app)

# Initialize monitoring
monitoring.init_app(app)

# Start backup service
start_backup_service()

# Ensure directories exist
os.makedirs("exports", exist_ok=True)
os.makedirs("syncs", exist_ok=True)

# Initialize Benton District Lookup service
district_lookup = BentonDistrictLookup()

# Route definitions
@app.route('/')
def index():
    """Root endpoint redirects to dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard_working.html')

@app.route('/admin')
def admin_panel():
    """Comprehensive admin panel for county administrators."""
    # Get system status information
    recent_gis_jobs = gis_export_service.list_jobs(limit=5)
    recent_sync_jobs = sync_service.list_jobs(limit=5)
    recent_backups = backup_scheduler.list_backups()[-5:] if backup_scheduler.list_backups() else []
    
    # Calculate summary statistics
    total_exports = len(gis_export_service.list_jobs(limit=1000))
    total_syncs = len(sync_service.list_jobs(limit=1000))
    total_backups = len(backup_scheduler.list_backups())
    
    return render_template('admin_panel.html',
                         gis_jobs=recent_gis_jobs,
                         sync_jobs=recent_sync_jobs,
                         backups=recent_backups,
                         stats={
                             'total_exports': total_exports,
                             'total_syncs': total_syncs,
                             'total_backups': total_backups,
                             'backup_service_running': backup_scheduler.running
                         })

@app.route('/gis/dashboard')
def gis_dashboard():
    """GIS Export dashboard view."""
    # In a real implementation, fetch data from database
    # For now, get data directly from the service
    recent_jobs = gis_export_service.list_jobs(limit=10)
    return render_template('gis_dashboard.html', gis_exports=recent_jobs)

@app.route('/sync/dashboard')
def sync_dashboard():
    """Sync Service dashboard view."""
    # In a real implementation, fetch data from database
    # For now, get data directly from the service
    recent_jobs = sync_service.list_jobs(limit=10)
    return render_template('sync_dashboard.html', sync_jobs=recent_jobs)

@app.route('/monitoring/dashboard')
def monitoring_dashboard():
    """Monitoring dashboard view for system performance and metrics."""
    return render_template('monitoring_dashboard.html')

@app.route('/backup/dashboard')
def backup_dashboard():
    """Backup management dashboard for county administrators."""
    backups = backup_scheduler.list_backups()
    return render_template('backup_dashboard.html', backups=backups)

@app.route('/district-lookup')
def district_lookup_dashboard():
    """District lookup dashboard view."""
    return render_template('district_lookup_dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "TerraFusion Platform", "version": "1.0.0"}

# GIS Export API endpoints
@app.route('/api/v1/gis-export/jobs', methods=['GET'])
def list_export_jobs():
    """List GIS export jobs with optional filtering."""
    county_id = request.args.get('county_id')
    status = request.args.get('status')
    username = request.args.get('username')
    limit = request.args.get('limit', 100, type=int)
    
    try:
        jobs = gis_export_service.list_jobs(
            county_id=county_id, 
            status=status, 
            username=username, 
            limit=limit
        )
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"Error listing GIS export jobs: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/gis-export/jobs', methods=['POST'])
def create_export_job():
    """Create a new GIS export job."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['county_id', 'username', 'export_format', 'area_of_interest', 'layers']
        if data is not None:
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
        else:
            return jsonify({"error": "Missing request body"}), 400
        
        # Create job
        job = gis_export_service.create_export_job(
            county_id=data['county_id'],
            username=data['username'],
            export_format=data['export_format'],
            area_of_interest=data['area_of_interest'],
            layers=data['layers'],
            parameters=data.get('parameters', {})
        )
        
        # Track the GIS export job creation in metrics
        track_gis_export_job(
            status="created",
            county=data['county_id'],
            export_format=data['export_format']
        )
        
        # Start processing the job (in a real application, this would be done by a background worker)
        processed_job = gis_export_service.process_job(job['job_id'])
        
        return jsonify(processed_job), 201
    except ValueError as e:
        logger.error(f"Validation error creating GIS export job: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating GIS export job: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/gis-export/jobs/<job_id>', methods=['GET'])
def get_export_job(job_id):
    """Get the status of a specific GIS export job."""
    try:
        job = gis_export_service.get_job_status(job_id)
        return jsonify(job)
    except FileNotFoundError:
        return jsonify({"error": f"Export job {job_id} not found"}), 404
    except Exception as e:
        logger.error(f"Error getting GIS export job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/gis-export/jobs/<job_id>/cancel', methods=['POST'])
def cancel_export_job(job_id):
    """Cancel a GIS export job."""
    try:
        job = gis_export_service.cancel_job(job_id)
        return jsonify(job)
    except FileNotFoundError:
        return jsonify({"error": f"Export job {job_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error cancelling GIS export job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/gis-export/download/<job_id>', methods=['GET'])
def download_export(job_id):
    """Download a completed GIS export file."""
    try:
        result = gis_export_service.get_job_result(job_id)
        file_path = result.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Export file not found"}), 404
        
        # Set filename based on county and format
        county_id = result.get('county_id', 'unknown')
        export_format = result.get('export_format', 'unknown')
        filename = f"{county_id}_export.{export_format}"
        
        # Track file size metrics
        file_size = os.path.getsize(file_path)
        track_export_file_size(export_format, file_size)
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except FileNotFoundError:
        return jsonify({"error": f"Export job {job_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error downloading GIS export for job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Sync Service API endpoints
@app.route('/api/v1/sync/jobs', methods=['GET'])
def list_sync_jobs():
    """List sync jobs with optional filtering."""
    county_id = request.args.get('county_id')
    status = request.args.get('status')
    username = request.args.get('username')
    limit = request.args.get('limit', 100, type=int)
    
    try:
        jobs = sync_service.list_jobs(
            county_id=county_id, 
            status=status, 
            username=username, 
            limit=limit
        )
        return jsonify(jobs)
    except Exception as e:
        logger.error(f"Error listing sync jobs: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sync/jobs', methods=['POST'])
def create_sync_job():
    """Create a new sync job."""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['county_id', 'username', 'data_types', 'source_system', 'target_system']
        if data is not None:
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
        else:
            return jsonify({"error": "Missing request body"}), 400
        
        # Create job
        job = sync_service.create_sync_job(
            county_id=data['county_id'],
            username=data['username'],
            data_types=data['data_types'],
            source_system=data['source_system'],
            target_system=data['target_system'],
            parameters=data.get('parameters', {})
        )
        
        # Track the sync job creation in metrics
        track_sync_job(
            status="created",
            county=data['county_id'],
            source=data['source_system'],
            target=data['target_system']
        )
        
        # Start processing the job (in a real application, this would be done by a background worker)
        processed_job = sync_service.process_job(job['job_id'])
        
        return jsonify(processed_job), 201
    except ValueError as e:
        logger.error(f"Validation error creating sync job: {str(e)}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error creating sync job: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sync/jobs/<job_id>', methods=['GET'])
def get_sync_job(job_id):
    """Get the status of a specific sync job."""
    try:
        job = sync_service.get_job_status(job_id)
        return jsonify(job)
    except FileNotFoundError:
        return jsonify({"error": f"Sync job {job_id} not found"}), 404
    except Exception as e:
        logger.error(f"Error getting sync job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sync/jobs/<job_id>/cancel', methods=['POST'])
def cancel_sync_job(job_id):
    """Cancel a sync job."""
    try:
        job = sync_service.cancel_job(job_id)
        return jsonify(job)
    except FileNotFoundError:
        return jsonify({"error": f"Sync job {job_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error cancelling sync job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/sync/jobs/<job_id>/report', methods=['GET'])
def get_sync_report(job_id):
    """Get a detailed report for a completed sync job."""
    try:
        report = sync_service.get_job_report(job_id)
        return jsonify(report)
    except FileNotFoundError:
        return jsonify({"error": f"Sync job {job_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error getting report for sync job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Backup Management API endpoints
@app.route('/api/v1/backup/list', methods=['GET'])
def list_backups():
    """List all available backups."""
    try:
        backups = backup_scheduler.list_backups()
        return jsonify(backups)
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/backup/create', methods=['POST'])
def create_backup():
    """Create a manual backup."""
    try:
        data = request.json or {}
        backup_type = data.get('type', 'all')
        
        results = {}
        
        if backup_type in ['all', 'database']:
            results['database'] = backup_scheduler.backup_database()
        
        if backup_type in ['all', 'files']:
            results['files'] = backup_scheduler.backup_files()
        
        if backup_type in ['all', 'config']:
            results['config'] = backup_scheduler.backup_configuration()
        
        return jsonify({
            "message": "Backup operation completed",
            "results": results
        })
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/backup/status', methods=['GET'])
def backup_status():
    """Get backup system status."""
    try:
        backups = backup_scheduler.list_backups()
        
        # Calculate backup statistics
        total_backups = len(backups)
        total_size = sum(backup.get('file_size', 0) for backup in backups)
        
        backup_counts = {}
        for backup in backups:
            backup_type = backup.get('type', 'unknown')
            backup_counts[backup_type] = backup_counts.get(backup_type, 0) + 1
        
        # Get most recent backup
        recent_backup = None
        if backups:
            recent_backup = max(backups, key=lambda x: x.get('timestamp', ''))
        
        return jsonify({
            "scheduler_running": backup_scheduler.running,
            "total_backups": total_backups,
            "total_size_bytes": total_size,
            "backup_counts": backup_counts,
            "most_recent_backup": recent_backup,
            "backup_directory": str(backup_scheduler.backup_dir)
        })
    except Exception as e:
        logger.error(f"Error getting backup status: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# =============================================================================
# BENTON DISTRICT LOOKUP API ENDPOINTS
# =============================================================================

@app.route('/api/v1/district-lookup/coordinates', methods=['GET'])
def lookup_district_by_coordinates():
    """Lookup districts by latitude and longitude coordinates."""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({
                "error": "Both 'lat' and 'lon' parameters are required",
                "usage": "/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090"
            }), 400
        
        try:
            latitude = float(lat)
            longitude = float(lon)
        except ValueError:
            return jsonify({
                "error": "Invalid coordinates. Latitude and longitude must be valid numbers",
                "provided": {"lat": lat, "lon": lon}
            }), 400
        
        result = district_lookup.lookup_by_coordinates(latitude, longitude)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in district lookup by coordinates: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup/address', methods=['GET'])
def lookup_district_by_address():
    """Lookup districts by street address."""
    try:
        address = request.args.get('address')
        
        if not address:
            return jsonify({
                "error": "Address parameter is required",
                "usage": "/api/v1/district-lookup/address?address=123 Main St, Kennewick, WA"
            }), 400
        
        result = district_lookup.lookup_by_address(address)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in district lookup by address: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup/districts', methods=['GET'])
def list_districts():
    """List available districts."""
    try:
        district_type = request.args.get('type')
        result = district_lookup.list_districts(district_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing districts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup', methods=['GET'])
def district_lookup_info():
    """Get information about the district lookup service."""
    return jsonify({
        "service": "Benton County District Lookup",
        "version": "1.0.0",
        "county": "Benton County, WA",
        "available_districts": list(district_lookup.districts.keys()),
        "endpoints": {
            "lookup_by_coordinates": "/api/v1/district-lookup/coordinates?lat={lat}&lon={lon}",
            "lookup_by_address": "/api/v1/district-lookup/address?address={address}",
            "list_districts": "/api/v1/district-lookup/districts"
        },
        "usage_examples": {
            "coordinates": "curl 'http://localhost:5000/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090'",
            "address": "curl 'http://localhost:5000/api/v1/district-lookup/address?address=123 Main St, Kennewick, WA'"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)