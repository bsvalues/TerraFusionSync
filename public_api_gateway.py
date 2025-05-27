"""
TerraFusion Public API Gateway

A secure GraphQL/REST API gateway for external vendor access and public data transparency.
Provides authenticated access to county GIS data with proper permissions and rate limiting.
"""

import os
import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Any

from flask import Flask, request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import graphene
from graphene import ObjectType, String, Int, Float, List as GrapheneList, Field, Schema
from flask_graphql import GraphQLView

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app for public API
public_api = Flask(__name__)
public_api.secret_key = os.environ.get("PUBLIC_API_SECRET", "terrafusion-public-api-key")

# Rate limiting
limiter = Limiter(
    app=public_api,
    key_func=get_remote_address,
    default_limits=["1000 per hour", "100 per minute"]
)

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "terrafusion-jwt-secret")
JWT_ALGORITHM = "HS256"

class APIPermissions:
    """Defines permission levels for public API access"""
    
    PUBLIC_READ = "public_read"          # Public data, no auth required
    VENDOR_READ = "vendor_read"          # Authenticated vendor access
    COUNTY_READ = "county_read"          # County staff access
    ADMIN_READ = "admin_read"            # Administrative access

class AuthToken:
    """JWT token management for API authentication"""
    
    @staticmethod
    def generate_token(user_id: str, permissions: List[str], county_id: str = None, expires_hours: int = 24) -> str:
        """Generate JWT token with permissions and expiration"""
        payload = {
            "user_id": user_id,
            "permissions": permissions,
            "county_id": county_id,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=expires_hours)
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

def require_permission(required_permission: str):
    """Decorator to require specific permissions for API endpoints"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Allow public access for PUBLIC_READ
            if required_permission == APIPermissions.PUBLIC_READ:
                g.user_permissions = [APIPermissions.PUBLIC_READ]
                g.county_id = None
                return f(*args, **kwargs)
            
            # Check for Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({
                    "error": "Authentication required",
                    "message": "Please provide a valid API token"
                }), 401
            
            token = auth_header.split(' ')[1]
            payload = AuthToken.verify_token(token)
            
            if not payload:
                return jsonify({
                    "error": "Invalid token",
                    "message": "Token is expired or invalid"
                }), 401
            
            # Check permissions
            user_permissions = payload.get('permissions', [])
            if required_permission not in user_permissions:
                return jsonify({
                    "error": "Insufficient permissions",
                    "message": f"Required permission: {required_permission}"
                }), 403
            
            # Store user info in request context
            g.user_id = payload.get('user_id')
            g.user_permissions = user_permissions
            g.county_id = payload.get('county_id')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# GraphQL Schema Definitions

class ParcelData(ObjectType):
    """GraphQL type for parcel information"""
    parcel_id = String(description="Unique parcel identifier")
    owner_name = String(description="Property owner name")
    assessed_value = Float(description="Current assessed value")
    tax_year = Int(description="Tax assessment year")
    zoning = String(description="Zoning classification")
    acreage = Float(description="Property size in acres")
    building_sqft = Int(description="Building square footage")
    address = String(description="Property address")
    county_id = String(description="County identifier")

class DistrictInfo(ObjectType):
    """GraphQL type for district information"""
    district_id = String(description="District identifier")
    district_name = String(description="District name")
    district_type = String(description="Type of district (voting, fire, school)")
    boundaries = String(description="GeoJSON boundaries")
    population = Int(description="District population")
    county_id = String(description="County identifier")

class ExportJobStatus(ObjectType):
    """GraphQL type for GIS export job status"""
    job_id = String(description="Export job identifier")
    status = String(description="Job status (pending, running, completed, failed)")
    format = String(description="Export format")
    created_at = String(description="Job creation timestamp")
    completed_at = String(description="Job completion timestamp")
    record_count = Int(description="Number of records exported")
    file_size = Int(description="Export file size in bytes")
    county_id = String(description="County identifier")

class CountyStats(ObjectType):
    """GraphQL type for county statistics"""
    county_id = String(description="County identifier")
    county_name = String(description="County name")
    total_parcels = Int(description="Total number of parcels")
    total_districts = Int(description="Total number of districts")
    export_jobs_today = Int(description="Export jobs completed today")
    system_uptime = String(description="System uptime percentage")
    last_updated = String(description="Last data update timestamp")

class PublicQuery(ObjectType):
    """Root GraphQL query for public API access"""
    
    # Public data endpoints (no auth required)
    county_stats = Field(CountyStats, county_id=String(required=True),
                        description="Get public statistics for a county")
    
    districts = GrapheneList(DistrictInfo, 
                           county_id=String(required=True),
                           district_type=String(),
                           description="List districts in a county")
    
    # Authenticated endpoints
    parcels = GrapheneList(ParcelData,
                          county_id=String(required=True),
                          limit=Int(default_value=100),
                          offset=Int(default_value=0),
                          description="List parcels (requires authentication)")
    
    export_jobs = GrapheneList(ExportJobStatus,
                              county_id=String(),
                              status=String(),
                              limit=Int(default_value=50),
                              description="List GIS export jobs (requires authentication)")
    
    def resolve_county_stats(self, info, county_id):
        """Resolve county statistics (public data)"""
        # In production, this would query your actual database
        return CountyStats(
            county_id=county_id,
            county_name=f"{county_id.title()} County",
            total_parcels=15420,
            total_districts=25,
            export_jobs_today=12,
            system_uptime="99.8%",
            last_updated=datetime.now().isoformat()
        )
    
    def resolve_districts(self, info, county_id, district_type=None):
        """Resolve district information (public data)"""
        # Sample district data - in production, query from your district lookup service
        districts = [
            DistrictInfo(
                district_id="precinct_01",
                district_name="Precinct 1",
                district_type="voting",
                boundaries='{"type":"Polygon","coordinates":[...]}',
                population=2850,
                county_id=county_id
            ),
            DistrictInfo(
                district_id="fire_district_1",
                district_name="Central Fire District",
                district_type="fire",
                boundaries='{"type":"Polygon","coordinates":[...]}',
                population=15200,
                county_id=county_id
            )
        ]
        
        if district_type:
            districts = [d for d in districts if d.district_type == district_type]
        
        return districts
    
    def resolve_parcels(self, info, county_id, limit=100, offset=0):
        """Resolve parcel data (requires authentication)"""
        # Check authentication via context
        user_permissions = getattr(g, 'user_permissions', [])
        if APIPermissions.VENDOR_READ not in user_permissions:
            raise Exception("Vendor authentication required for parcel data")
        
        # Sample parcel data - in production, query from your GIS database
        parcels = [
            ParcelData(
                parcel_id=f"PARCEL_{i:06d}",
                owner_name=f"Property Owner {i}",
                assessed_value=185000 + (i * 1000),
                tax_year=2024,
                zoning="R1" if i % 2 == 0 else "C1",
                acreage=0.25 + (i * 0.1),
                building_sqft=1850 + (i * 100),
                address=f"{i * 100} Main Street",
                county_id=county_id
            )
            for i in range(offset + 1, offset + limit + 1)
        ]
        
        return parcels
    
    def resolve_export_jobs(self, info, county_id=None, status=None, limit=50):
        """Resolve export job status (requires authentication)"""
        user_permissions = getattr(g, 'user_permissions', [])
        if APIPermissions.VENDOR_READ not in user_permissions:
            raise Exception("Vendor authentication required for export job data")
        
        # Sample export job data
        jobs = [
            ExportJobStatus(
                job_id=f"job_{i:06d}",
                status="completed" if i % 3 != 0 else "running",
                format="geojson" if i % 2 == 0 else "csv",
                created_at=(datetime.now() - timedelta(hours=i)).isoformat(),
                completed_at=(datetime.now() - timedelta(hours=i-1)).isoformat() if i % 3 != 0 else None,
                record_count=1000 + (i * 100),
                file_size=50000 + (i * 5000),
                county_id=county_id or "sample_county"
            )
            for i in range(1, limit + 1)
        ]
        
        if county_id:
            jobs = [j for j in jobs if j.county_id == county_id]
        if status:
            jobs = [j for j in jobs if j.status == status]
        
        return jobs

# Create GraphQL schema
public_schema = Schema(query=PublicQuery)

# REST API Endpoints

@public_api.route('/public/api/v1/health')
@limiter.limit("10 per minute")
def public_health():
    """Public health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "TerraFusion Public API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })

@public_api.route('/public/api/v1/counties')
@require_permission(APIPermissions.PUBLIC_READ)
@limiter.limit("100 per hour")
def list_counties():
    """List available counties (public data)"""
    counties = [
        {
            "county_id": "benton-wa",
            "county_name": "Benton County, WA",
            "state": "Washington",
            "api_access": "available",
            "last_updated": "2024-05-27T10:00:00Z"
        },
        {
            "county_id": "king-wa", 
            "county_name": "King County, WA",
            "state": "Washington",
            "api_access": "available",
            "last_updated": "2024-05-27T09:30:00Z"
        }
    ]
    
    return jsonify({
        "status": "success",
        "data": {
            "counties": counties,
            "total_count": len(counties)
        }
    })

@public_api.route('/public/api/v1/auth/token', methods=['POST'])
@limiter.limit("5 per minute")
def generate_api_token():
    """Generate API token for vendor access"""
    data = request.get_json()
    
    if not data or not data.get('vendor_id') or not data.get('api_key'):
        return jsonify({
            "error": "Missing credentials",
            "message": "vendor_id and api_key are required"
        }), 400
    
    vendor_id = data['vendor_id']
    api_key = data['api_key']
    
    # In production, verify vendor credentials against database
    # For demo, accept specific test credentials
    if vendor_id == "test_vendor" and api_key == "test_api_key_2024":
        token = AuthToken.generate_token(
            user_id=vendor_id,
            permissions=[APIPermissions.VENDOR_READ],
            county_id=data.get('county_id'),
            expires_hours=24
        )
        
        return jsonify({
            "status": "success",
            "data": {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 86400,  # 24 hours
                "permissions": [APIPermissions.VENDOR_READ]
            }
        })
    else:
        return jsonify({
            "error": "Invalid credentials",
            "message": "Vendor credentials not found or invalid"
        }), 401

@public_api.route('/public/api/v1/documentation')
@require_permission(APIPermissions.PUBLIC_READ)
def api_documentation():
    """API documentation and usage guide"""
    return jsonify({
        "status": "success",
        "data": {
            "api_version": "1.0.0",
            "description": "TerraFusion Public API for county data access",
            "authentication": {
                "method": "JWT Bearer Token",
                "endpoint": "/public/api/v1/auth/token",
                "description": "Request token using vendor credentials"
            },
            "endpoints": {
                "graphql": {
                    "url": "/public/graphql",
                    "method": "POST",
                    "description": "GraphQL endpoint for flexible data queries",
                    "authentication": "Bearer token required for authenticated data"
                },
                "rest": {
                    "counties": "/public/api/v1/counties",
                    "health": "/public/api/v1/health",
                    "documentation": "/public/api/v1/documentation"
                }
            },
            "rate_limits": {
                "authenticated": "1000 requests per hour",
                "public": "100 requests per hour"
            },
            "data_types": {
                "parcels": "Property ownership and assessment data",
                "districts": "Voting, fire, and school district boundaries",
                "export_jobs": "GIS data export job status and results",
                "statistics": "Public county statistics and metrics"
            }
        }
    })

# Add GraphQL endpoint
public_api.add_url_rule(
    '/public/graphql',
    view_func=GraphQLView.as_view(
        'graphql',
        schema=public_schema,
        graphiql=True  # Enable GraphiQL explorer
    )
)

@public_api.errorhandler(429)
def rate_limit_handler(e):
    """Handle rate limit exceeded"""
    return jsonify({
        "error": "Rate limit exceeded",
        "message": "Too many requests. Please slow down and try again later."
    }), 429

@public_api.errorhandler(500)
def internal_error_handler(e):
    """Handle internal server errors"""
    logger.error(f"Internal server error: {e}")
    return jsonify({
        "error": "Internal server error",
        "message": "An unexpected error occurred. Please try again later."
    }), 500

if __name__ == '__main__':
    logger.info("🌐 Starting TerraFusion Public API Gateway...")
    public_api.run(host='0.0.0.0', port=8000, debug=True)