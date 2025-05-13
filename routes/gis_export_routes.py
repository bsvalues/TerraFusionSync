"""
TerraFusion API Gateway - GIS Export Routes

This module defines routes for the GIS Export functionality, forwarding requests
to the TerraFusion SyncService GIS Export plugin.
"""

import logging
from flask import Blueprint, request, jsonify, current_app, session
from functools import wraps

# Import the sync service client for making API calls
from services.sync_service_client import SyncServiceClient

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for GIS Export routes
gis_export_bp = Blueprint('gis_export', __name__, url_prefix='/api/v1/gis-export')

# Get sync service client
sync_service = SyncServiceClient()

# Helper for requiring authentication
def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        # This is a placeholder - implement proper auth check based on your auth system
        if 'user_id' not in session:
            logger.warning(f"Unauthenticated access attempt to {request.path}")
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# Define routes
@gis_export_bp.route('/run', methods=['POST'])
@require_auth
def run_gis_export():
    """Submit a new GIS export job."""
    try:
        # Validate request content type
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        # Get request payload
        payload = request.get_json()
        
        # Log the request
        logger.info(f"Received GIS export job request: {payload}")
        
        # Forward request to SyncService
        response, status_code = sync_service.post("/plugins/v1/gis-export/run", payload)
        
        # Log the response
        logger.info(f"GIS export job response: status={status_code}")
        
        # Return the response from SyncService
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error processing GIS export job request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@gis_export_bp.route('/status/<job_id>', methods=['GET'])
@require_auth
def get_gis_export_status(job_id):
    """Get the status of a GIS export job."""
    try:
        # Log the request
        logger.info(f"Received request for GIS export job status: {job_id}")
        
        # Forward request to SyncService
        response, status_code = sync_service.get(f"/plugins/v1/gis-export/status/{job_id}")
        
        # Return the response from SyncService
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error getting GIS export job status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@gis_export_bp.route('/list', methods=['GET'])
@require_auth
def list_gis_export_jobs():
    """List GIS export jobs with optional filtering."""
    try:
        # Get query parameters
        county_id = request.args.get('county_id')
        export_format = request.args.get('export_format')
        status = request.args.get('status')
        limit = request.args.get('limit', 20)
        offset = request.args.get('offset', 0)
        
        # Build query parameters
        params = {}
        if county_id:
            params['county_id'] = county_id
        if export_format:
            params['export_format'] = export_format
        if status:
            params['status'] = status
        params['limit'] = limit
        params['offset'] = offset
        
        # Forward request to SyncService
        response, status_code = sync_service.get("/plugins/v1/gis-export/list", params=params)
        
        # Return the response from SyncService
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error listing GIS export jobs: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@gis_export_bp.route('/results/<job_id>', methods=['GET'])
@require_auth
def get_gis_export_results(job_id):
    """Get the results of a completed GIS export job."""
    try:
        # Log the request
        logger.info(f"Received request for GIS export job results: {job_id}")
        
        # Forward request to SyncService
        response, status_code = sync_service.get(f"/plugins/v1/gis-export/results/{job_id}")
        
        # Return the response from SyncService
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error getting GIS export job results: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@gis_export_bp.route('/cancel/<job_id>', methods=['POST'])
@require_auth
def cancel_gis_export_job(job_id):
    """Cancel a pending or running GIS export job."""
    try:
        # Log the request
        logger.info(f"Received request to cancel GIS export job: {job_id}")
        
        # Forward request to SyncService
        response, status_code = sync_service.post(f"/plugins/v1/gis-export/cancel/{job_id}")
        
        # Return the response from SyncService
        return jsonify(response), status_code
        
    except Exception as e:
        logger.error(f"Error cancelling GIS export job: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500