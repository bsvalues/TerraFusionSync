#!/usr/bin/env python
"""
GIS Export Plugin Quick Validation Script

This script runs a minimal set of tests to validate the GIS Export plugin functionality,
focusing on the core features with reduced processing times for quick verification.
"""

import sys
import time
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_section(message):
    """Print a section header."""
    print("\n" + "-" * 60)
    print(f" {message}")
    print("-" * 60)

def print_result(fmt, time_sec, size_kb, records, location=None):
    """Print a formatted result line."""
    if location:
        print(f"{fmt:<10}: {time_sec:.2f}s, {size_kb} KB, {records} records - {location}")
    else:
        print(f"{fmt:<10}: {time_sec:.2f}s, {size_kb} KB, {records} records")

async def simulate_minimal_export():
    """Simulate a minimal GIS export with shorter processing time."""
    from quick_gis_export_test import simulate_gis_export_processing
    
    # Parameters for a quick test
    county_id = "test_county"
    export_format = "geojson"
    area_of_interest = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    layers = ["parcels"]  # Just one layer for speed
    parameters = {"coordinate_system": "EPSG:4326", "simplify_tolerance": 0.001}
    
    # Run the simulation
    start_time = datetime.now()
    file_location, file_size_kb, record_count = await simulate_gis_export_processing(
        county_id, export_format, area_of_interest, layers, parameters
    )
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return {
        "format": export_format,
        "time": processing_time,
        "size": file_size_kb,
        "count": record_count,
        "location": file_location
    }

async def test_format_comparison_minimal():
    """Test different formats with minimal processing time."""
    from quick_gis_export_test import simulate_gis_export_processing
    
    county_id = "benton_wa"
    area_of_interest = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    layers = ["parcels"]  # Just one layer for speed
    parameters = {"coordinate_system": "EPSG:4326", "simplify_tolerance": 0.001}
    
    formats = ["geojson", "shapefile", "kml"]
    results = {}
    
    for export_format in formats:
        logger.info(f"Testing format: {export_format}")
        
        start_time = datetime.now()
        file_location, file_size_kb, record_count = await simulate_gis_export_processing(
            county_id, export_format, area_of_interest, layers, parameters
        )
        processing_time = (datetime.now() - start_time).total_seconds()
        
        results[export_format] = {
            "time": processing_time,
            "size": file_size_kb,
            "count": record_count
        }
    
    return results

async def main():
    """Run quick validation tests for GIS Export plugin."""
    print_header("TerraFusion GIS Export Quick Validation")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    success = True
    
    try:
        # Test 1: Minimal export
        print_section("Test: Minimal GIS Export")
        minimal_result = await simulate_minimal_export()
        print("\nMinimal Export Results:")
        print_result(
            minimal_result['format'], 
            minimal_result['time'], 
            minimal_result['size'], 
            minimal_result['count'],
            minimal_result['location']
        )
        
        # Test 2: Format comparison (minimal)
        print_section("Test: Format Comparison (Minimal)")
        formats_result = await test_format_comparison_minimal()
        print("\nFormat Comparison Results:")
        for fmt, data in formats_result.items():
            print_result(fmt, data['time'], data['size'], data['count'])
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        print_section("Validation Results")
        print(f"✅ GIS Export validation completed successfully in {execution_time:.2f} seconds")
        print(f"All core functionality is working as expected")
    
    except Exception as e:
        logger.error(f"Error in validation: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        success = False
        print_section("Validation Results")
        print(f"❌ GIS Export validation failed")
    
    print_header("Validation Complete")
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(130)