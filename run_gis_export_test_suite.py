#!/usr/bin/env python
"""
GIS Export Plugin Test Suite Runner

This script runs a comprehensive test suite for the GIS Export plugin, including:
1. Quick simulation tests (format comparison)
2. Enhanced simulation tests (complex areas, simplification)
3. API endpoint tests (if SyncService is running)

Use this before pushing changes to validate all GIS Export functionality.
"""

import os
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

async def run_quick_tests():
    """Run the quick GIS export tests."""
    print_section("Running Quick GIS Export Tests")
    
    # Import functions from quick test module
    from quick_gis_export_test import test_simple_area, test_format_comparisons
    
    # Test 1: Simple area
    print_section("Test: Simple Area Export")
    simple_result = await test_simple_area()
    print("\nSimple Export Results:")
    print_result(
        "geojson", 
        simple_result['time'], 
        simple_result['size'], 
        simple_result['count'],
        simple_result['location']
    )
    
    # Test 2: Format comparison
    print_section("Test: Format Comparison")
    formats_result = await test_format_comparisons()
    print("\nFormat Comparison Results:")
    for fmt, data in formats_result.items():
        print_result(fmt, data['time'], data['size'], data['count'])
    
    return True

async def run_enhanced_tests():
    """Run the enhanced GIS export tests with complex scenarios."""
    print_section("Running Enhanced GIS Export Tests")
    
    # Only import if the file exists
    if os.path.exists("test_gis_export_enhanced.py"):
        # Import functions from enhanced test module
        from test_gis_export_enhanced import (
            test_export_with_simple_area,
            test_export_with_complex_area,
            test_export_with_different_formats,
            test_export_with_simplification
        )
        
        print_section("Test: Complex Area Export")
        await test_export_with_complex_area()
        
        print_section("Test: Format Comparison (Enhanced)")
        await test_export_with_different_formats()
        
        print_section("Test: Simplification Parameters")
        await test_export_with_simplification()
    else:
        logger.warning("Enhanced test file not found, skipping enhanced tests")
    
    return True

async def check_syncservice():
    """Check if SyncService is running and accessible."""
    import requests
    
    try:
        response = requests.get("http://0.0.0.0:8080/health", timeout=2)
        if response.status_code == 200:
            return True
    except Exception as e:
        logger.warning(f"SyncService not available: {e}")
    
    return False

async def run_api_tests():
    """Run tests against the actual API endpoints if SyncService is running."""
    print_section("Running API Integration Tests")
    
    syncservice_running = await check_syncservice()
    if not syncservice_running:
        logger.warning("SyncService not running, skipping API tests")
        return False
    
    # Import test module if it exists
    if os.path.exists("tests/plugins/test_gis_export.py"):
        try:
            sys.path.insert(0, ".")  # Ensure we can import from current directory
            from tests.plugins.test_gis_export import (
                test_create_gis_export_job,
                test_get_gis_export_job_status,
                test_get_all_gis_export_jobs
            )
            
            print_section("API Test: Create Export Job")
            await test_create_gis_export_job()
            
            print_section("API Test: Get Job Status")
            await test_get_gis_export_job_status()
            
            print_section("API Test: List All Jobs")
            await test_get_all_gis_export_jobs()
            
            return True
        except Exception as e:
            logger.error(f"Error running API tests: {e}")
            return False
    else:
        logger.warning("API test file not found, skipping API tests")
        return False

async def main():
    """Run all test suites for GIS Export plugin."""
    print_header("TerraFusion GIS Export Test Suite")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    success = True
    
    try:
        # Run quick simulation tests
        quick_success = await run_quick_tests()
        success = success and quick_success
        
        # Run enhanced tests if available
        enhanced_success = await run_enhanced_tests()
        success = success and enhanced_success
        
        # Run API tests if SyncService is running
        api_success = await run_api_tests()
        # Don't fail the whole suite if API tests are skipped
        if api_success is not None and not api_success:
            success = False
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        print_section("Test Suite Results")
        if success:
            print(f"✅ GIS Export test suite completed successfully in {execution_time:.2f} seconds")
        else:
            print(f"❌ Some GIS Export tests failed, check logs for details")
            print(f"Test suite ran for {execution_time:.2f} seconds")
    
    except Exception as e:
        logger.error(f"Error in test suite: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        success = False
    
    print_header("Test Suite Execution Complete")
    return 0 if success else 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user")
        sys.exit(130)