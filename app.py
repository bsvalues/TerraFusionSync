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

# Import Benton District Lookup service
from benton_district_lookup import BentonDistrictLookup

# Import NarratorAI service
from narrator_ai_plugin import analyze_gis_export_data, analyze_sync_data, get_ai_health

# Import enhanced UX endpoints
try:
    from enhanced_api_endpoints import register_enhanced_endpoints, register_error_handlers
    ENHANCED_ENDPOINTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Enhanced endpoints not available: {e}")
    ENHANCED_ENDPOINTS_AVAILABLE = False

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "terrafusion-dev-key")

# Ensure exports directory exists
os.makedirs("exports", exist_ok=True)

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
    return render_template('dashboard.html')

@app.route('/gis/dashboard')
def gis_dashboard():
    """GIS Export dashboard view."""
    # In a real implementation, fetch data from database
    # For now, get data directly from the service
    recent_jobs = gis_export_service.list_jobs(limit=10)
    return render_template('dashboard.html', gis_exports=recent_jobs)

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

# =============================================================================
# BENTON DISTRICT LOOKUP API ENDPOINTS
# =============================================================================

@app.route('/api/v1/district-lookup/coordinates', methods=['GET'])
def lookup_district_by_coordinates():
    """
    Lookup districts by latitude and longitude coordinates.
    
    Query Parameters:
        lat: Latitude (required)
        lon: Longitude (required)
    
    Example: /api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090
    """
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
    """
    Lookup districts by street address.
    
    Query Parameters:
        address: Street address (required)
    
    Example: /api/v1/district-lookup/address?address=123 Main St, Kennewick, WA
    """
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
    """
    List available districts.
    
    Query Parameters:
        type: Optional filter by district type (voting_precincts, fire_districts, school_districts)
    
    Example: /api/v1/district-lookup/districts?type=voting_precincts
    """
    try:
        district_type = request.args.get('type')
        result = district_lookup.list_districts(district_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing districts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup/districts/<district_type>/<district_id>', methods=['GET'])
def get_district_info(district_type, district_id):
    """
    Get detailed information about a specific district.
    
    Parameters:
        district_type: Type of district (voting_precincts, fire_districts, school_districts)
        district_id: District identifier
    
    Example: /api/v1/district-lookup/districts/voting_precincts/precinct_01
    """
    try:
        result = district_lookup.get_district_info(district_type, district_id)
        
        if result is None:
            return jsonify({
                "error": f"District not found: {district_type}/{district_id}"
            }), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error getting district info: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup', methods=['GET'])
def district_lookup_info():
    """
    Get information about the district lookup service.
    """
    return jsonify({
        "service": "Benton County District Lookup",
        "version": "1.0.0",
        "county": "Benton County, WA",
        "available_districts": list(district_lookup.districts.keys()),
        "endpoints": {
            "lookup_by_coordinates": "/api/v1/district-lookup/coordinates?lat={lat}&lon={lon}",
            "lookup_by_address": "/api/v1/district-lookup/address?address={address}",
            "list_districts": "/api/v1/district-lookup/districts",
            "get_district_info": "/api/v1/district-lookup/districts/{type}/{id}"
        },
        "usage_examples": {
            "coordinates": "curl 'http://localhost:5000/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090'",
            "address": "curl 'http://localhost:5000/api/v1/district-lookup/address?address=123 Main St, Kennewick, WA'",
            "list_all": "curl 'http://localhost:5000/api/v1/district-lookup/districts'",
            "list_voting": "curl 'http://localhost:5000/api/v1/district-lookup/districts?type=voting_precincts'"
        }
    })

# =============================================================================
# NARRATORAI (AI ASSISTANT) API ENDPOINTS
# =============================================================================

@app.route('/api/v1/ai/analyze/gis-export', methods=['POST'])
def ai_analyze_gis_export():
    """
    Get AI analysis and insights for a GIS export job.
    
    Request Body:
        job_id: GIS export job ID to analyze
    
    Example: POST /api/v1/ai/analyze/gis-export
    Body: {"job_id": "abc123"}
    """
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        
        if not job_id:
            return jsonify({
                "error": "job_id is required",
                "usage": "POST with JSON body containing job_id"
            }), 400
        
        # Get the GIS export job data
        try:
            job_data = gis_export_service.get_job_status(job_id)
        except FileNotFoundError:
            return jsonify({"error": f"GIS export job {job_id} not found"}), 404
        
        # Get AI analysis
        import asyncio
        analysis = asyncio.run(analyze_gis_export_data(job_data))
        
        if "error" in analysis:
            return jsonify({"error": f"AI analysis failed: {analysis['error']}"}), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in AI GIS export analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/analyze/sync-operation', methods=['POST'])
def ai_analyze_sync_operation():
    """
    Get AI analysis and insights for a sync operation.
    
    Request Body:
        operation_data: Sync operation data to analyze
    
    Example: POST /api/v1/ai/analyze/sync-operation
    """
    try:
        data = request.get_json() or {}
        operation_data = data.get('operation_data')
        
        if not operation_data:
            return jsonify({
                "error": "operation_data is required",
                "usage": "POST with JSON body containing operation_data"
            }), 400
        
        # Get AI analysis
        import asyncio
        analysis = asyncio.run(analyze_sync_data(operation_data))
        
        if "error" in analysis:
            return jsonify({"error": f"AI analysis failed: {analysis['error']}"}), 500
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in AI sync analysis: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/health', methods=['GET'])
def ai_health_check():
    """
    Check the health and status of the NarratorAI service.
    
    Example: GET /api/v1/ai/health
    """
    try:
        health_status = get_ai_health()
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error checking AI health: {str(e)}", exc_info=True)
        return jsonify({
            "service": "NarratorAI",
            "status": "error", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api/v1/ai/demo', methods=['GET'])
def ai_demo():
    """
    Demonstrate AI capabilities with sample data analysis.
    
    Example: GET /api/v1/ai/demo
    """
    try:
        # Sample GIS export data for demonstration
        sample_gis_data = {
            "job_id": "demo-job-123",
            "county_id": "benton-wa",
            "username": "demo-user@county.gov",
            "export_format": "geojson",
            "layers": ["parcels", "zoning", "roads"],
            "status": "COMPLETED",
            "file_size": 2456789,
            "created_at": "2025-05-27T10:00:00Z",
            "started_at": "2025-05-27T10:00:05Z",
            "completed_at": "2025-05-27T10:02:15Z",
            "message": "Export completed successfully"
        }
        
        # Get AI analysis
        import asyncio
        analysis = asyncio.run(analyze_gis_export_data(sample_gis_data))
        
        return jsonify({
            "demo_data": sample_gis_data,
            "ai_analysis": analysis,
            "message": "This is a demonstration of NarratorAI capabilities using sample data"
        })
        
    except Exception as e:
        logger.error(f"Error in AI demo: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Register enhanced UX endpoints and error handlers
if ENHANCED_ENDPOINTS_AVAILABLE:
    register_enhanced_endpoints(app)
    register_error_handlers(app)
    logger.info("✅ Enhanced UX endpoints registered")
else:
    logger.info("ℹ️  Running with basic endpoints only")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)