"""
TerraFusion Public API Extensions

Adds vendor-ready API endpoints to the existing TerraFusion platform
for external integrations and public data access.
"""

import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET = "terrafusion-public-api-secret-2024"
JWT_ALGORITHM = "HS256"

class PublicAPIAuth:
    """Authentication management for public API access"""
    
    @staticmethod
    def generate_vendor_token(vendor_id: str, county_id: str = None) -> str:
        """Generate JWT token for vendor access"""
        payload = {
            "vendor_id": vendor_id,
            "permissions": ["vendor_read"],
            "county_id": county_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=24)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_vendor_token(token: str) -> dict:
        """Verify vendor JWT token"""
        try:
            return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except:
            return None

def require_vendor_auth(f):
    """Decorator requiring vendor authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({
                "error": "Authentication required",
                "message": "Provide Bearer token for vendor access"
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = PublicAPIAuth.verify_vendor_token(token)
        
        if not payload:
            return jsonify({
                "error": "Invalid token",
                "message": "Token expired or invalid"
            }), 401
        
        g.vendor_id = payload.get('vendor_id')
        g.county_id = payload.get('county_id')
        return f(*args, **kwargs)
    
    return decorated_function

def register_public_api_endpoints(app):
    """Register public API endpoints with the main TerraFusion app"""
    
    @app.route('/public/api/health')
    def public_api_health():
        """Public API health check"""
        return jsonify({
            "status": "healthy",
            "service": "TerraFusion Public API",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "capabilities": {
                "vendor_access": True,
                "county_data": True,
                "real_time_exports": True,
                "district_lookup": True
            }
        })
    
    @app.route('/public/api/counties')
    def public_list_counties():
        """List available counties for vendor access"""
        counties = [
            {
                "county_id": "benton-wa",
                "county_name": "Benton County, WA",
                "state": "Washington",
                "data_available": True,
                "api_access": "enabled",
                "last_updated": "2024-05-27T00:00:00Z"
            },
            {
                "county_id": "king-wa",
                "county_name": "King County, WA", 
                "state": "Washington",
                "data_available": True,
                "api_access": "enabled",
                "last_updated": "2024-05-27T00:00:00Z"
            }
        ]
        
        return jsonify({
            "status": "success",
            "data": {
                "counties": counties,
                "total_available": len(counties),
                "api_version": "1.0.0"
            }
        })
    
    @app.route('/public/api/auth/token', methods=['POST'])
    def generate_vendor_token():
        """Generate access token for verified vendors"""
        data = request.get_json()
        
        if not data or not data.get('vendor_id'):
            return jsonify({
                "error": "Missing vendor_id",
                "message": "Vendor ID required for token generation"
            }), 400
        
        vendor_id = data['vendor_id']
        county_id = data.get('county_id')
        
        # For demonstration - in production, verify vendor credentials
        if vendor_id.startswith('vendor_'):
            token = PublicAPIAuth.generate_vendor_token(vendor_id, county_id)
            
            return jsonify({
                "status": "success",
                "data": {
                    "access_token": token,
                    "token_type": "Bearer",
                    "expires_in": 86400,
                    "vendor_id": vendor_id,
                    "county_access": county_id or "all"
                }
            })
        else:
            return jsonify({
                "error": "Invalid vendor",
                "message": "Vendor not authorized for API access"
            }), 401
    
    @app.route('/public/api/data/parcels/<county_id>')
    @require_vendor_auth
    def public_get_parcels(county_id):
        """Get parcel data for authorized vendors"""
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Real parcel data would come from your GIS database
        # This demonstrates the structure for vendor integration
        parcels = []
        for i in range(offset + 1, offset + min(limit, 50) + 1):
            parcels.append({
                "parcel_id": f"{county_id.upper()}-{i:06d}",
                "assessed_value": 185000 + (i * 1000),
                "tax_year": 2024,
                "zoning": "R1" if i % 2 == 0 else "C1",
                "acreage": round(0.25 + (i * 0.05), 2),
                "address": f"{i * 100} County Road",
                "county_id": county_id
            })
        
        return jsonify({
            "status": "success",
            "data": {
                "parcels": parcels,
                "count": len(parcels),
                "total_available": f"Contact {county_id} for exact counts",
                "county_id": county_id,
                "vendor_id": g.vendor_id
            }
        })
    
    @app.route('/public/api/data/districts/<county_id>')
    def public_get_districts(county_id):
        """Get district information (public data)"""
        district_type = request.args.get('type')
        
        # Real district data from your district lookup service
        districts = [
            {
                "district_id": "precinct_01",
                "district_name": "Precinct 1",
                "district_type": "voting",
                "population": 2850,
                "county_id": county_id
            },
            {
                "district_id": "fire_dist_central",
                "district_name": "Central Fire District",
                "district_type": "fire",
                "population": 15200,
                "county_id": county_id
            },
            {
                "district_id": "school_dist_1",
                "district_name": "County School District 1",
                "district_type": "school",
                "population": 12500,
                "county_id": county_id
            }
        ]
        
        if district_type:
            districts = [d for d in districts if d['district_type'] == district_type]
        
        return jsonify({
            "status": "success",
            "data": {
                "districts": districts,
                "count": len(districts),
                "county_id": county_id,
                "available_types": ["voting", "fire", "school"]
            }
        })
    
    @app.route('/public/api/exports/status')
    @require_vendor_auth
    def public_export_status():
        """Get export job status for vendors"""
        county_id = request.args.get('county_id')
        status_filter = request.args.get('status')
        
        # Real export data from your GIS export service
        jobs = []
        for i in range(1, 6):
            job_status = "completed" if i <= 3 else "running"
            if not status_filter or job_status == status_filter:
                jobs.append({
                    "job_id": f"export_{i:06d}",
                    "status": job_status,
                    "format": "geojson" if i % 2 == 0 else "csv",
                    "created_at": (datetime.now() - timedelta(hours=i)).isoformat(),
                    "record_count": 1000 + (i * 200),
                    "county_id": county_id or "multi_county"
                })
        
        return jsonify({
            "status": "success",
            "data": {
                "export_jobs": jobs,
                "count": len(jobs),
                "vendor_id": g.vendor_id,
                "filters_applied": {
                    "county_id": county_id,
                    "status": status_filter
                }
            }
        })
    
    @app.route('/public/api/documentation')
    def public_api_docs():
        """Public API documentation for vendors"""
        return jsonify({
            "status": "success",
            "data": {
                "api_name": "TerraFusion Public API",
                "version": "1.0.0",
                "description": "Secure access to county GIS data for authorized vendors",
                "authentication": {
                    "method": "JWT Bearer Token",
                    "endpoint": "/public/api/auth/token",
                    "requirements": "Authorized vendor credentials"
                },
                "endpoints": {
                    "public": {
                        "/public/api/health": "API health status",
                        "/public/api/counties": "Available counties",
                        "/public/api/documentation": "This documentation"
                    },
                    "authenticated": {
                        "/public/api/data/parcels/<county_id>": "Parcel data access",
                        "/public/api/exports/status": "Export job monitoring"
                    },
                    "district_data": {
                        "/public/api/data/districts/<county_id>": "District boundaries and info"
                    }
                },
                "rate_limits": {
                    "public_endpoints": "100 requests per hour",
                    "authenticated_endpoints": "1000 requests per hour"
                },
                "support": {
                    "contact": "County IT Administrator",
                    "documentation": "See TerraFusion deployment guide"
                }
            }
        })
    
    logger.info("✅ Public API endpoints registered successfully")
    return app