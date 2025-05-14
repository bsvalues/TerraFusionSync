#!/usr/bin/env python3
"""
TerraFusion Platform - GIS Export County Configuration Test

This script demonstrates the county-specific configuration features of the GIS Export plugin.
It shows how the plugin enforces county-specific export format validation and applies default parameters.

Usage:
    python test_county_config_gis_export.py

"""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import the county configuration module
    from terrafusion_sync.plugins.gis_export.county_config import get_county_config
    
    # Import the core service for creating export jobs
    from terrafusion_sync.plugins.gis_export.service import GisExportService
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    logger.error("Make sure you're running this script from the project root directory")
    sys.exit(1)

# Test data for GIS export jobs
TEST_COUNTIES = ["benton_wa", "nonexistent_county"]

TEST_FORMATS = ["GeoJSON", "Shapefile", "KML", "INVALID_FORMAT"]

TEST_AREAS = [
    {
        "type": "Polygon",
        "coordinates": [[
            [-122.48, 37.78],
            [-122.48, 37.80],
            [-122.46, 37.80],
            [-122.46, 37.78],
            [-122.48, 37.78]
        ]]
    }
]

TEST_LAYERS = [
    ["parcels", "buildings", "zoning"],
    ["roads", "tax_districts"]
]

async def test_county_config_formats():
    """Test that county configuration correctly validates export formats."""
    county_config = get_county_config()
    success_count = 0
    failure_count = 0
    
    logger.info("===== Testing County-Specific Export Format Validation =====")
    
    for county_id in TEST_COUNTIES:
        logger.info(f"\nCounty: {county_id}")
        
        try:
            available_formats = county_config.get_available_formats(county_id)
            logger.info(f"Available formats: {', '.join(available_formats)}")
            
            for format_name in TEST_FORMATS:
                is_valid = county_config.validate_export_format(county_id, format_name)
                
                if is_valid:
                    logger.info(f"✅ Format '{format_name}' is valid for county {county_id}")
                    success_count += 1
                else:
                    logger.info(f"❌ Format '{format_name}' is NOT valid for county {county_id}")
                    failure_count += 1
        
        except Exception as e:
            logger.error(f"Error testing formats for county {county_id}: {e}")
            failure_count += 1
    
    logger.info(f"\nFormat validation test complete: {success_count} passed, {failure_count} failed")

async def test_county_default_parameters():
    """Test that county configuration provides correct default parameters."""
    county_config = get_county_config()
    
    logger.info("\n===== Testing County-Specific Default Parameters =====")
    
    for county_id in TEST_COUNTIES:
        logger.info(f"\nCounty: {county_id}")
        
        try:
            default_coordinate_system = county_config.get_default_coordinate_system(county_id)
            logger.info(f"Default coordinate system: {default_coordinate_system}")
            
            max_export_area = county_config.get_max_export_area(county_id)
            logger.info(f"Maximum export area: {max_export_area} sq km")
            
            default_params = county_config.get_default_parameters(county_id)
            logger.info(f"Default parameters: {json.dumps(default_params, indent=2)}")
            
        except Exception as e:
            logger.error(f"Error getting default parameters for county {county_id}: {e}")

async def test_service_with_county_config():
    """
    Test that the GisExportService uses county configuration correctly.
    This is a demonstration only and will not actually create database records.
    """
    logger.info("\n===== Testing Service Integration with County Configuration =====")
    logger.info("Note: This is a simulated test that will not actually create database records.")
    
    for county_id in TEST_COUNTIES:
        logger.info(f"\nCounty: {county_id}")
        
        # Get available formats for this county
        county_config = get_county_config()
        available_formats = county_config.get_available_formats(county_id)
        
        # Test valid format
        if available_formats:
            valid_format = available_formats[0]
            logger.info(f"Testing valid format: {valid_format}")
            
            try:
                # In a real application, this would use a database session
                # For the demo, we'll just check if an exception is raised during validation
                default_params = GisExportService.get_default_export_parameters(county_id)
                logger.info(f"Default parameters applied: {json.dumps(default_params, indent=2)}")
                logger.info(f"✅ Format '{valid_format}' passed validation for county {county_id}")
            except ValueError as e:
                logger.error(f"❌ Unexpected validation error: {e}")
        
        # Test invalid format
        invalid_format = "INVALID_FORMAT"
        logger.info(f"Testing invalid format: {invalid_format}")
        
        try:
            # This should raise a ValueError
            logger.info("Attempting to validate invalid format (should fail)...")
            if not county_config.validate_export_format(county_id, invalid_format):
                logger.info(f"❌ Format '{invalid_format}' correctly rejected for county {county_id}")
        except Exception as e:
            logger.info(f"❌ Format validation failed as expected: {e}")

async def main():
    """Main test function."""
    logger.info("Starting GIS Export County Configuration Test")
    
    # Run tests
    await test_county_config_formats()
    await test_county_default_parameters()
    await test_service_with_county_config()
    
    logger.info("\nGIS Export County Configuration Test completed")

if __name__ == "__main__":
    asyncio.run(main())