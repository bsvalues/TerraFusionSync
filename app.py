"""
TerraFusion Platform - Enterprise Application

This module provides the Flask application for the TerraFusion Platform,
including the dashboard and API endpoints for GIS Export functionality.
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, abort

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import GIS Export service
from gis_export import gis_export_service

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terrafusion-dev-key")

# Ensure exports directory exists
os.makedirs("exports", exist_ok=True)

# Route definitions
@app.route('/')
def index():
    """Root endpoint redirects to dashboard."""
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Main dashboard view."""
    return render_template('dashboard.html')

@app.route('/gis/dashboard')
def gis_dashboard():
    """GIS Export dashboard view."""
    # In a real implementation, fetch data from database
    # For now, get data directly from the service
    recent_jobs = gis_export_service.list_jobs(limit=10)
    return render_template('dashboard.html', gis_exports=recent_jobs)

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
            parameters=data.get('parameters')
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
        
        return send_file(file_path, as_attachment=True, download_name=filename)
    except FileNotFoundError:
        return jsonify({"error": f"Export job {job_id} not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Error downloading GIS export for job {job_id}: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)