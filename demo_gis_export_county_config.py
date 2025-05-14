#!/usr/bin/env python3
"""
TerraFusion Platform - GIS Export County Configuration Demo

This script demonstrates how the GIS Export plugin uses county-specific configurations
for format validation, default parameters, and other settings.

Created for demonstration purposes to showcase the county configuration features.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

# Configure logging with color support
try:
    from colorama import Fore, Style, init
    init()  # Initialize colorama
    
    # Define colored log formatter
    class ColoredFormatter(logging.Formatter):
        """Custom formatter with colors"""
        FORMAT = "%(asctime)s - %(message)s"
        
        def format(self, record):
            log_fmt = self.FORMAT
            formatter = logging.Formatter(log_fmt)
            if record.levelno == logging.INFO:
                log_fmt = f"{Fore.GREEN}%(asctime)s - %(message)s{Style.RESET_ALL}"
                formatter = logging.Formatter(log_fmt)
            elif record.levelno == logging.WARNING:
                log_fmt = f"{Fore.YELLOW}%(asctime)s - %(message)s{Style.RESET_ALL}"
                formatter = logging.Formatter(log_fmt)
            elif record.levelno == logging.ERROR:
                log_fmt = f"{Fore.RED}%(asctime)s - %(message)s{Style.RESET_ALL}"
                formatter = logging.Formatter(log_fmt)
            elif record.levelno == logging.DEBUG:
                log_fmt = f"{Fore.CYAN}%(asctime)s - %(message)s{Style.RESET_ALL}"
                formatter = logging.Formatter(log_fmt)
            
            formatter = logging.Formatter(log_fmt)
            return formatter.format(record)
    
    # Set up logging with the custom formatter
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )
except ImportError:
    # Fallback to regular logging if colorama is not available
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger(__name__)

# Demo county configurations for display purposes
DEMO_COUNTY_CONFIGS = {
    "benton_wa": {
        "available_formats": ["GeoJSON", "Shapefile", "KML"],
        "default_coordinate_system": "EPSG:4326",
        "max_export_area_sq_km": 750,
        "default_simplify_tolerance": 0.0001,
        "include_attributes_default": True
    },
    "clark_wa": {
        "available_formats": ["GeoJSON", "Shapefile", "GeoPackage", "FileGDB"],
        "default_coordinate_system": "EPSG:2927",  # NAD83(HARN) StatePlane Washington South FIPS 4602 Feet
        "max_export_area_sq_km": 1000,
        "default_simplify_tolerance": 0.0002,
        "include_attributes_default": True
    },
    "king_wa": {
        "available_formats": ["GeoJSON", "Shapefile", "KML", "GeoPackage", "CSV"],
        "default_coordinate_system": "EPSG:2926",  # NAD83(HARN) StatePlane Washington North FIPS 4601 Feet
        "max_export_area_sq_km": 2000,
        "default_simplify_tolerance": 0.00005,
        "include_attributes_default": True,
        "max_concurrent_exports": 10
    }
}

# Demo export requests for different counties
DEMO_EXPORT_REQUESTS = [
    {
        "county_id": "benton_wa",
        "format": "GeoJSON",
        "username": "county_user",
        "area_of_interest": {
            "type": "Polygon",
            "coordinates": [[
                [-119.48, 46.21],
                [-119.48, 46.26],
                [-119.42, 46.26],
                [-119.42, 46.21],
                [-119.48, 46.21]
            ]]
        },
        "layers": ["parcels", "zoning", "buildings"],
        "parameters": {
            "simplify_tolerance": 0.0002,
            "include_attributes": True,
            "coordinate_system": "EPSG:4326"
        }
    },
    {
        "county_id": "benton_wa",
        "format": "PDF",  # Invalid format for Benton County
        "username": "county_user",
        "area_of_interest": {
            "type": "Polygon",
            "coordinates": [[
                [-119.48, 46.21],
                [-119.48, 46.26],
                [-119.42, 46.26],
                [-119.42, 46.21],
                [-119.48, 46.21]
            ]]
        },
        "layers": ["parcels"],
        "parameters": None  # Will use defaults from county config
    },
    {
        "county_id": "clark_wa",
        "format": "GeoPackage",
        "username": "county_user",
        "area_of_interest": {
            "type": "Polygon",
            "coordinates": [[
                [-122.70, 45.63],
                [-122.70, 45.68],
                [-122.65, 45.68],
                [-122.65, 45.63],
                [-122.70, 45.63]
            ]]
        },
        "layers": ["parcels", "tax_districts", "hydrography"],
        "parameters": None  # Will use defaults from county config
    }
]

def show_county_config(county_id: str):
    """Display county configuration in a formatted way"""
    config = DEMO_COUNTY_CONFIGS.get(county_id)
    
    if not config:
        logger.error(f"County {county_id} not found in demo configurations")
        return
    
    logger.info(f"====== County Configuration: {county_id} ======")
    logger.info(f"Available formats: {', '.join(config['available_formats'])}")
    logger.info(f"Default coordinate system: {config['default_coordinate_system']}")
    logger.info(f"Maximum export area: {config['max_export_area_sq_km']} sq km")
    logger.info(f"Default simplify tolerance: {config['default_simplify_tolerance']}")
    logger.info(f"Include attributes by default: {config['include_attributes_default']}")
    
    # Show additional county-specific settings
    for key, value in config.items():
        if key not in ["available_formats", "default_coordinate_system", 
                      "max_export_area_sq_km", "default_simplify_tolerance", 
                      "include_attributes_default"]:
            logger.info(f"{key}: {value}")

def validate_export_request(request: Dict[str, Any]) -> bool:
    """Validate export request against county configuration"""
    county_id = request.get("county_id")
    export_format = request.get("format")
    
    if not county_id or not export_format:
        logger.error("Missing required fields in export request")
        return False
    
    config = DEMO_COUNTY_CONFIGS.get(county_id)
    if not config:
        logger.warning(f"County {county_id} not found in configurations, using defaults")
        return True
    
    # Format validation
    if export_format not in config["available_formats"]:
        logger.error(f"Format '{export_format}' is not supported for county {county_id}")
        logger.info(f"Supported formats: {', '.join(config['available_formats'])}")
        return False
    
    # Apply defaults if parameters are not provided
    if request.get("parameters") is None:
        logger.info(f"Using default parameters for county {county_id}")
        request["parameters"] = {
            "simplify_tolerance": config["default_simplify_tolerance"],
            "include_attributes": config["include_attributes_default"],
            "coordinate_system": config["default_coordinate_system"]
        }
    
    return True

def simulate_export_job(request: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate processing an export job"""
    county_id = request.get("county_id", "unknown")
    export_format = request.get("format", "unknown")
    
    # Generate a simulated job result
    job_id = f"job_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Determine status based on validation
    if validate_export_request(request):
        status = "COMPLETED"
        message = "Export completed successfully"
        
        # Simulate file generation - ensure format is a string
        file_extension = export_format.lower() if isinstance(export_format, str) else "unknown"
        file_location = f"https://storage.terrafusion.com/{county_id}/exports/{job_id}.{file_extension}"
        file_size_kb = len(request.get("layers", [])) * 1000  # 1MB per layer
        record_count = len(request.get("layers", [])) * 500  # 500 records per layer
    else:
        status = "FAILED"
        message = f"Export format '{export_format}' is not supported for county {county_id}"
        file_location = None
        file_size_kb = 0
        record_count = 0
    
    # Create a job result
    return {
        "job_id": job_id,
        "county_id": county_id,
        "export_format": export_format,
        "status": status,
        "message": message,
        "created_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat() if status in ["COMPLETED", "FAILED"] else None,
        "result": {
            "file_location": file_location,
            "file_size_kb": file_size_kb,
            "record_count": record_count
        } if status == "COMPLETED" else None
    }

def main():
    """Main demo function"""
    logger.info("====== TerraFusion Platform - GIS Export County Configuration Demo ======")
    logger.info("This demo shows how the GIS Export plugin uses county-specific configurations")
    
    # Show all county configurations
    logger.info("\n=== Available County Configurations ===")
    for county_id in DEMO_COUNTY_CONFIGS:
        show_county_config(county_id)
        logger.info("")
    
    # Process demo export requests
    logger.info("\n=== Processing Demo Export Requests ===")
    for i, request in enumerate(DEMO_EXPORT_REQUESTS, 1):
        logger.info(f"\nRequest #{i}:")
        logger.info(f"County: {request['county_id']}")
        logger.info(f"Format: {request['format']}")
        logger.info(f"Layers: {', '.join(request.get('layers', []))}")
        
        # Process the request
        logger.info("\nValidating request...")
        result = simulate_export_job(request)
        
        # Show result
        logger.info("\nResult:")
        logger.info(f"Status: {result['status']}")
        logger.info(f"Message: {result['message']}")
        
        if result.get("result"):
            logger.info(f"File: {result['result']['file_location']}")
            logger.info(f"Size: {result['result']['file_size_kb']} KB")
            logger.info(f"Records: {result['result']['record_count']}")
        
        logger.info("=" * 50)
    
    logger.info("\nDemo complete!")

if __name__ == "__main__":
    main()