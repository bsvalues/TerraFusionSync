import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, jsonify, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

db.init_app(app)

from gis_export import gis_export_service
from benton_district_lookup import BentonDistrictLookup
from narrator_ai_plugin import analyze_gis_export_data, analyze_sync_data, get_ai_health

try:
    from exemption_seer_ai import analyze_exemption_data, get_exemption_seer_health
    EXEMPTION_SEER_AVAILABLE = True
except ImportError:
    EXEMPTION_SEER_AVAILABLE = False

try:
    from rbac_manager import rbac_manager, require_role
    RBAC_AVAILABLE = True
except ImportError:
    RBAC_AVAILABLE = False

os.makedirs("exports", exist_ok=True)
district_lookup = BentonDistrictLookup()

with app.app_context():
    try:
        import models
        db.create_all()
    except ImportError:
        pass

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/gis/dashboard')
def gis_dashboard():
    recent_jobs = gis_export_service.list_jobs(limit=10)
    return render_template('dashboard.html', gis_exports=recent_jobs)

@app.route('/district-lookup')
def district_lookup_dashboard():
    return render_template('district_lookup_dashboard.html')

@app.route('/ai-analysis')
def ai_analysis_dashboard():
    return render_template('ai_analysis_dashboard.html')

@app.route('/health')
def health_check():
    return {"status": "healthy", "service": "TerraFusion Platform", "version": "2.0.0"}

@app.route('/api/v1/gis-export/jobs', methods=['GET'])
def list_export_jobs():
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
    try:
        data = request.json
        
        required_fields = ['county_id', 'username', 'export_format', 'area_of_interest', 'layers']
        if data is not None:
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
        else:
            return jsonify({"error": "Missing request body"}), 400
        
        job = gis_export_service.create_export_job(
            county_id=data['county_id'],
            username=data['username'],
            export_format=data['export_format'],
            area_of_interest=data['area_of_interest'],
            layers=data['layers'],
            parameters=data.get('parameters')
        )
        
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
    try:
        result = gis_export_service.get_job_result(job_id)
        file_path = result.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({"error": "Export file not found"}), 404
        
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

@app.route('/api/v1/district-lookup/coordinates', methods=['GET'])
def lookup_district_by_coordinates():
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
    try:
        district_type = request.args.get('type')
        result = district_lookup.list_districts(district_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error listing districts: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/v1/district-lookup/districts/<district_type>/<district_id>', methods=['GET'])
def get_district_info(district_type, district_id):
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
    return jsonify({
        "service": "Benton County District Lookup",
        "version": "2.0.0",
        "county": "Benton County, WA",
        "available_districts": list(district_lookup.districts.keys()),
        "endpoints": {
            "lookup_by_coordinates": "/api/v1/district-lookup/coordinates?lat={lat}&lon={lon}",
            "lookup_by_address": "/api/v1/district-lookup/address?address={address}",
            "list_districts": "/api/v1/district-lookup/districts",
            "get_district_info": "/api/v1/district-lookup/districts/{type}/{id}"
        }
    })

@app.route('/api/v1/ai/analyze/gis-export', methods=['POST'])
def ai_analyze_gis_export():
    try:
        data = request.get_json() or {}
        job_id = data.get('job_id')
        
        if not job_id:
            return jsonify({
                "error": "job_id is required",
                "usage": "POST with JSON body containing job_id"
            }), 400
        
        try:
            job_data = gis_export_service.get_job_status(job_id)
        except FileNotFoundError:
            return jsonify({"error": f"GIS export job {job_id} not found"}), 404
        
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
    try:
        data = request.get_json() or {}
        operation_data = data.get('operation_data')
        
        if not operation_data:
            return jsonify({
                "error": "operation_data is required",
                "usage": "POST with JSON body containing operation_data"
            }), 400
        
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
    try:
        health_status = get_ai_health()
        return jsonify(health_status)
        
    except Exception as e:
        logger.error(f"Error checking AI health: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if EXEMPTION_SEER_AVAILABLE:
    @app.route('/api/v1/ai/analyze/exemption', methods=['POST'])
    def ai_analyze_exemption():
        try:
            data = request.get_json() or {}
            
            required_fields = ['parcel_id', 'exemption_type', 'exemption_code', 
                             'exemption_amount', 'property_description', 'owner_name', 
                             'assessment_year', 'exemption_reason']
            
            for field in required_fields:
                if field not in data:
                    return jsonify({"error": f"Missing required field: {field}"}), 400
            
            from exemption_seer_ai import analyze_exemption_data
            import asyncio
            analysis = asyncio.run(analyze_exemption_data(data))
            
            if "error" in analysis:
                return jsonify({"error": f"AI analysis failed: {analysis['error']}"}), 500
            
            return jsonify(analysis)
            
        except Exception as e:
            logger.error(f"Error in exemption analysis: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/api/v1/ai/exemption-seer/health', methods=['GET'])
    def exemption_seer_health():
        try:
            from exemption_seer_ai import get_exemption_seer_health
            health_status = get_exemption_seer_health()
            return jsonify(health_status)
        except Exception as e:
            logger.error(f"Error checking ExemptionSeer health: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

@app.route('/api/v1/ai/demo', methods=['GET'])
def ai_demo():
    demo_data = {
        "service": "TerraFusion AI Demo",
        "version": "2.0.0",
        "demo_gis_job": {
            "job_id": "demo_123",
            "county_id": "benton_wa",
            "export_format": "shapefile",
            "status": "completed",
            "created_at": "2024-01-15T10:30:00Z",
            "layers": ["parcels", "zoning", "roads"]
        },
        "available_ai_services": {
            "narrator_ai": True,
            "exemption_seer": EXEMPTION_SEER_AVAILABLE
        }
    }
    return jsonify(demo_data)

if RBAC_AVAILABLE:
    @app.route('/rbac/admin')
    def rbac_admin_dashboard():
        return render_template('rbac_admin.html')

    @app.route('/api/v1/rbac/users', methods=['GET'])
    def rbac_list_users():
        try:
            from rbac_manager import rbac_manager
            users = rbac_manager.list_users()
            return jsonify(users)
        except Exception as e:
            logger.error(f"Error listing users: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route('/api/v1/rbac/login', methods=['POST'])
    def rbac_login():
        try:
            data = request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({"error": "Username and password required"}), 400
            
            from rbac_manager import rbac_manager
            result = rbac_manager.authenticate_user(username, password)
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)
            return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)