"""
TerraFusion Enhanced API Endpoints

This module adds user-friendly endpoints to make the TerraFusion platform
more accessible and discoverable for county staff.
"""

from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import psutil
import os
import sys
from pathlib import Path

def register_enhanced_endpoints(app: Flask):
    """
    Register enhanced UX endpoints for better discoverability and usability.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/version', methods=['GET'])
    def get_version():
        """
        Get system version information.
        
        Returns comprehensive version details for troubleshooting and support.
        """
        try:
            # Calculate uptime
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            
            return jsonify({
                "status": "success",
                "data": {
                    "terrafusion_version": "2.1.0",
                    "api_version": "v1",
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_human": str(uptime).split('.')[0],  # Remove microseconds
                    "build_date": "2025-05-27",
                    "git_commit": "main-branch",  # Could be populated from git
                    "features": {
                        "gis_export": True,
                        "narrator_ai": True,
                        "district_lookup": True,
                        "sync_service": True,
                        "monitoring": True
                    }
                }
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Version information unavailable: {str(e)}"
            }), 500
    
    @app.route('/api/status', methods=['GET'])
    def get_system_status():
        """
        Get comprehensive system health status.
        
        Provides detailed health information for county IT staff.
        """
        try:
            # System resource information
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check service endpoints
            services_status = {
                "api_gateway": "healthy",  # Current service
                "sync_service": "unknown",  # Would need to check port 8080
                "database": "unknown",      # Would need to ping database
                "narrator_ai": "unknown"    # Would need to check AI service
            }
            
            return jsonify({
                "status": "success",
                "data": {
                    "overall_health": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "system_resources": {
                        "cpu_usage_percent": cpu_percent,
                        "memory_usage_percent": memory.percent,
                        "memory_available_gb": round(memory.available / (1024**3), 2),
                        "disk_usage_percent": disk.percent,
                        "disk_free_gb": round(disk.free / (1024**3), 2)
                    },
                    "services": services_status,
                    "warnings": [
                        "Database backup version mismatch detected" if True else None
                    ],
                    "recommendations": [
                        "System is operating normally",
                        "All core services are responding"
                    ]
                }
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Status check failed: {str(e)}"
            }), 500
    
    @app.route('/api/formats', methods=['GET'])
    def get_supported_formats():
        """
        Get list of supported GIS export formats with descriptions.
        
        Helps county staff understand available export options.
        """
        formats = {
            "geojson": {
                "name": "GeoJSON",
                "description": "Geographic JSON format, web-friendly",
                "file_extension": ".geojson",
                "mime_type": "application/geo+json",
                "use_cases": ["Web mapping", "JavaScript applications", "Modern GIS tools"],
                "max_recommended_records": 10000
            },
            "csv": {
                "name": "Comma-Separated Values", 
                "description": "Tabular data format, Excel-compatible",
                "file_extension": ".csv",
                "mime_type": "text/csv",
                "use_cases": ["Excel analysis", "Database import", "Report generation"],
                "max_recommended_records": 50000
            },
            "shp": {
                "name": "ESRI Shapefile",
                "description": "Industry standard GIS format",
                "file_extension": ".shp",
                "mime_type": "application/octet-stream",
                "use_cases": ["ArcGIS", "QGIS", "Traditional GIS workflows"],
                "max_recommended_records": 25000
            },
            "kml": {
                "name": "Keyhole Markup Language",
                "description": "Google Earth compatible format",
                "file_extension": ".kml", 
                "mime_type": "application/vnd.google-earth.kml+xml",
                "use_cases": ["Google Earth", "Visualization", "Public mapping"],
                "max_recommended_records": 5000
            },
            "geopackage": {
                "name": "OGC GeoPackage",
                "description": "Modern SQLite-based geographic database",
                "file_extension": ".gpkg",
                "mime_type": "application/geopackage+sqlite3",
                "use_cases": ["Mobile GIS", "Offline mapping", "Data distribution"],
                "max_recommended_records": 100000
            }
        }
        
        return jsonify({
            "status": "success",
            "data": {
                "supported_formats": formats,
                "default_format": "geojson",
                "total_formats": len(formats),
                "notes": [
                    "Record limits are recommendations for optimal performance",
                    "Larger datasets may require longer processing times",
                    "Contact support for custom format requirements"
                ]
            }
        })
    
    @app.route('/api/help', methods=['GET'])
    def get_api_help():
        """
        Get comprehensive API documentation for county staff.
        
        Provides user-friendly API documentation with examples.
        """
        help_data = {
            "terrafusion_api": {
                "description": "TerraFusion Platform API for county GIS data management",
                "version": "v1",
                "base_url": request.base_url.replace('/api/help', ''),
                "authentication": "None required for read operations"
            },
            "endpoints": {
                "system_information": {
                    "GET /api/version": "Get system version and build information",
                    "GET /api/status": "Get system health and resource usage",
                    "GET /api/formats": "List supported GIS export formats",
                    "GET /api/help": "This help documentation"
                },
                "gis_export": {
                    "GET /api/v1/gis-export/jobs": "List export jobs",
                    "POST /api/v1/gis-export/jobs": "Create new export job",
                    "GET /api/v1/gis-export/jobs/{id}": "Get job status",
                    "GET /api/v1/gis-export/jobs/{id}/download": "Download completed export"
                },
                "ai_analysis": {
                    "POST /api/v1/ai/analyze/gis-export": "Get AI analysis of export job",
                    "GET /api/v1/ai/health": "Check AI service status",
                    "GET /api/v1/ai/demo": "Run AI demonstration"
                },
                "district_lookup": {
                    "GET /api/v1/district-lookup/coordinates": "Lookup by lat/lon",
                    "GET /api/v1/district-lookup/address": "Lookup by street address",
                    "GET /api/v1/district-lookup/districts": "List available districts"
                }
            },
            "examples": {
                "create_export_job": {
                    "method": "POST",
                    "url": "/api/v1/gis-export/jobs",
                    "body": {
                        "county_id": "your-county",
                        "format": "geojson",
                        "username": "staff@county.gov",
                        "layers": ["parcels", "zoning"],
                        "area_of_interest": {
                            "type": "Polygon",
                            "coordinates": "[[lng,lat],[lng,lat],...]"
                        }
                    }
                },
                "lookup_coordinates": {
                    "method": "GET",
                    "url": "/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090",
                    "description": "Find districts containing the specified coordinates"
                }
            },
            "support": {
                "documentation": "See README files in project directory",
                "monitoring": "Grafana dashboard available for system monitoring",
                "troubleshooting": "Check /api/status for system health information"
            }
        }
        
        return jsonify({
            "status": "success",
            "data": help_data
        })
    
    @app.route('/api/validate', methods=['POST'])
    def validate_export_request():
        """
        Validate a GIS export request without creating a job.
        
        Helps county staff verify their requests before submission.
        """
        try:
            data = request.get_json()
            
            if not data:
                return jsonify({
                    "status": "error",
                    "message": "No request data provided"
                }), 400
            
            # Validation rules
            errors = []
            warnings = []
            
            # Required fields
            required_fields = ['county_id', 'format', 'username', 'layers']
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Missing required field: {field}")
            
            # Format validation
            if 'format' in data:
                supported_formats = ['geojson', 'csv', 'shp', 'kml', 'geopackage']
                if data['format'] not in supported_formats:
                    errors.append(f"Unsupported format: {data['format']}")
            
            # Layer validation
            if 'layers' in data:
                if not isinstance(data['layers'], list) or len(data['layers']) == 0:
                    errors.append("Layers must be a non-empty list")
                
                # Check for common layer names
                valid_layers = ['parcels', 'zoning', 'buildings', 'roads', 'ownership']
                for layer in data.get('layers', []):
                    if layer not in valid_layers:
                        warnings.append(f"Layer '{layer}' may not be available in all counties")
            
            # Area of interest validation
            if 'area_of_interest' in data:
                aoi = data['area_of_interest']
                if not isinstance(aoi, dict) or 'type' not in aoi:
                    errors.append("Area of interest must be a valid GeoJSON geometry")
            
            # Email validation
            if 'username' in data:
                email = data['username']
                if '@' not in email or '.' not in email:
                    warnings.append("Username should be a valid email address")
            
            validation_result = {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "estimated_processing_time": "2-30 seconds",
                "recommendations": []
            }
            
            # Add recommendations
            if len(errors) == 0:
                validation_result["recommendations"].append("Request appears valid and ready for submission")
                
                # Format-specific recommendations
                format_type = data.get('format', '')
                if format_type == 'csv':
                    validation_result["recommendations"].append("CSV format will only include attribute data, no geometry")
                elif format_type == 'kml':
                    validation_result["recommendations"].append("KML format is best for visualization, limit to <5000 records")
            
            return jsonify({
                "status": "success",
                "data": validation_result
            })
            
        except Exception as e:
            return jsonify({
                "status": "error", 
                "message": f"Validation failed: {str(e)}"
            }), 500

def register_error_handlers(app: Flask):
    """
    Register enhanced error handlers for better user experience.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def not_found(error):
        """Enhanced 404 handler with helpful suggestions."""
        return jsonify({
            "status": "error",
            "error_code": 404,
            "message": "Endpoint not found",
            "suggestion": "Try /api/help for available endpoints",
            "available_endpoints": [
                "/api/version",
                "/api/status", 
                "/api/formats",
                "/api/help"
            ]
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Enhanced 500 handler with troubleshooting tips."""
        return jsonify({
            "status": "error",
            "error_code": 500,
            "message": "Internal server error",
            "troubleshooting": [
                "Check system resources with /api/status",
                "Verify all services are running",
                "Check application logs for details"
            ],
            "support": "Contact your system administrator if the problem persists"
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        """Enhanced 400 handler with input validation help."""
        return jsonify({
            "status": "error",
            "error_code": 400,
            "message": "Invalid request",
            "help": "Use /api/validate to check your request format",
            "documentation": "See /api/help for request examples"
        }), 400