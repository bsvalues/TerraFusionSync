#!/usr/bin/env python3
"""
TerraFusion Platform - GIS Export County Configuration Standalone Test

This script demonstrates the county-specific configuration features of the GIS Export plugin.
It avoids importing other plugins to prevent metric registration conflicts.
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import county configuration directly (avoid full package import)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Define a simplified version of the CountyGisExportConfig class
class CountyGisExportConfig:
    """Simplified version for testing only"""
    
    def __init__(self):
        """Initialize with hard-coded test data instead of loading from files"""
        self.configs = {
            "benton_wa": {
                "available_formats": ["GeoJSON", "Shapefile", "KML"],
                "default_coordinate_system": "EPSG:4326",
                "max_export_area_sq_km": 750,
                "default_simplify_tolerance": 0.0001,
                "include_attributes_default": True
            },
            # Use default values for nonexistent county
        }
        self.default_config = {
            "available_formats": ["GeoJSON", "Shapefile", "KML"],
            "default_coordinate_system": "EPSG:4326",
            "max_export_area_sq_km": 500,
            "default_simplify_tolerance": 0.0001,
            "include_attributes_default": True
        }
    
    def get_config(self, county_id: str) -> Dict[str, Any]:
        """Get config for a county, falling back to defaults if needed"""
        return self.configs.get(county_id, self.default_config)
    
    def get_available_formats(self, county_id: str) -> List[str]:
        """Get available formats for a county"""
        config = self.get_config(county_id)
        return config["available_formats"]
    
    def validate_export_format(self, county_id: str, format_name: str) -> bool:
        """Check if format is valid for this county"""
        valid_formats = self.get_available_formats(county_id)
        return format_name in valid_formats
    
    def get_default_coordinate_system(self, county_id: str) -> str:
        """Get default coordinate system for a county"""
        config = self.get_config(county_id)
        return config["default_coordinate_system"]
    
    def get_max_export_area(self, county_id: str) -> float:
        """Get maximum export area in square kilometers"""
        config = self.get_config(county_id)
        return config["max_export_area_sq_km"]
    
    def get_default_parameters(self, county_id: str) -> Dict[str, Any]:
        """Get default export parameters for a county"""
        config = self.get_config(county_id)
        return {
            "simplify_tolerance": config["default_simplify_tolerance"],
            "include_attributes": config["include_attributes_default"],
            "coordinate_system": config["default_coordinate_system"]
        }

def main():
    """Main test function"""
    logger.info("===== GIS Export County Configuration Standalone Test =====")
    
    # Test counties - one that exists and one that doesn't
    counties = ["benton_wa", "nonexistent_county"]
    
    # Test formats - some valid, some invalid
    formats = ["GeoJSON", "Shapefile", "KML", "INVALID_FORMAT"]
    
    # Create the config handler
    county_config = CountyGisExportConfig()
    
    # Test format validation for each county
    for county_id in counties:
        logger.info(f"\nCounty: {county_id}")
        
        # Get available formats
        available_formats = county_config.get_available_formats(county_id)
        logger.info(f"Available formats: {', '.join(available_formats)}")
        
        # Test each format
        for format_name in formats:
            is_valid = county_config.validate_export_format(county_id, format_name)
            if is_valid:
                logger.info(f"✅ Format '{format_name}' is valid for county {county_id}")
            else:
                logger.info(f"❌ Format '{format_name}' is NOT valid for county {county_id}")
        
        # Get default parameters
        default_params = county_config.get_default_parameters(county_id)
        logger.info(f"Default parameters: {json.dumps(default_params, indent=2)}")
        
        # Get max export area
        max_area = county_config.get_max_export_area(county_id)
        logger.info(f"Max export area: {max_area} sq km")
    
    logger.info("\n===== Test Complete =====")

if __name__ == "__main__":
    main()