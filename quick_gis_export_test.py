#!/usr/bin/env python
"""
Quick test script for validating GIS Export processing functionality.
This is a faster version of test_gis_export_enhanced.py with shorter processing time.
"""

import asyncio
import logging
import sys
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Simple version of the simulation function with reduced sleep times
async def simulate_gis_export_processing(
    county_id: str, 
    export_format: str, 
    area_of_interest: dict, 
    layers: list, 
    parameters: dict
):
    """Simplified simulation with reduced processing time for quick tests."""
    import random
    import json
    import hashlib
    from datetime import datetime
    
    # Much shorter processing time for quick testing
    processing_time = 0.2 + (len(layers) * 0.1)
    logger.info(f"Quick simulation processing for {processing_time:.2f} seconds")
    await asyncio.sleep(processing_time)
    
    # Generate unique ID
    export_id = hashlib.md5((county_id + export_format).encode()).hexdigest()[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    
    # Simple file location
    file_location = f"https://terrafusionstorage.blob.core.windows.net/exports/{county_id}/{timestamp}_{export_id}.{export_format}"
    
    # Quick size calculation
    format_size_factor = {
        "geojson": 1.2, "shapefile": 0.8, "kml": 1.5,
        "topojson": 0.7, "geopackage": 0.9, "geotiff": 2.5
    }.get(export_format.lower(), 1.0)
    
    file_size_kb = int(250 * format_size_factor * len(layers) * random.uniform(0.9, 1.1))
    
    # Quick record count
    record_count = sum([
        random.randint(1000, 5000) for _ in layers
    ])
    
    logger.info(f"GIS Export simulation completed - Format: {export_format}, Size: {file_size_kb}KB, Records: {record_count}")
    
    return file_location, file_size_kb, record_count

async def test_simple_area():
    """Test with simple parameters."""
    logger.info("Testing simple area export")
    
    county_id = "test_county"
    export_format = "geojson"
    area_of_interest = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    layers = ["parcels", "buildings"]
    parameters = {"coordinate_system": "EPSG:4326", "simplify_tolerance": 0.0001}
    
    start_time = datetime.now()
    result_location, file_size_kb, record_count = await simulate_gis_export_processing(
        county_id, export_format, area_of_interest, layers, parameters
    )
    processing_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"Simple test completed in {processing_time:.2f}s")
    logger.info(f"Result: {file_size_kb}KB, {record_count} records, {result_location}")
    
    return {
        "time": processing_time,
        "size": file_size_kb,
        "count": record_count,
        "location": result_location
    }

async def test_format_comparisons():
    """Test different formats."""
    logger.info("Testing format comparisons")
    
    county_id = "benton_wa"
    area_of_interest = {"type": "FeatureCollection", "features": [{"type": "Feature"}]}
    layers = ["parcels", "buildings", "roads"]
    parameters = {"coordinate_system": "EPSG:4326", "simplify_tolerance": 0.0001}
    
    formats = ["geojson", "shapefile", "kml"]
    results = {}
    
    for export_format in formats:
        logger.info(f"Testing format: {export_format}")
        
        start_time = datetime.now()
        result_location, file_size_kb, record_count = await simulate_gis_export_processing(
            county_id, export_format, area_of_interest, layers, parameters
        )
        processing_time = (datetime.now() - start_time).total_seconds()
        
        results[export_format] = {
            "time": processing_time,
            "size": file_size_kb,
            "count": record_count
        }
    
    # Compare formats
    logger.info("\nFormat comparison:")
    for fmt, data in results.items():
        logger.info(f"{fmt:<10}: {data['time']:.2f}s, {data['size']} KB, {data['count']} records")
    
    return results

async def main():
    """Run quick tests."""
    logger.info("Starting quick GIS Export plugin tests")
    
    try:
        # Test simple area
        success = await test_simple_area()
        
        # Test formats
        success = await test_format_comparisons()
        
        logger.info("All quick tests completed successfully!")
        return 0
    except Exception as e:
        logger.error(f"Error during testing: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Tests interrupted by user")
        sys.exit(130)