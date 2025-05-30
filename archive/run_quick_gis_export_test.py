#!/usr/bin/env python
"""
Run quick test for GIS Export plugin.
This script directly executes the quick_gis_export_test.py logic for cleaner output.
"""

import sys
import time
import asyncio
from datetime import datetime
import logging

# Disable the default logging from the test script
logging.basicConfig(level=logging.WARNING)

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_section(message):
    """Print a section header."""
    print("\n" + "-" * 40)
    print(f" {message}")
    print("-" * 40)

def print_result(fmt, time_sec, size_kb, records):
    """Print a formatted result line."""
    print(f"{fmt:<10}: {time_sec:.2f}s, {size_kb} KB, {records} records")

# Import the test functions
from quick_gis_export_test import simulate_gis_export_processing, test_simple_area, test_format_comparisons

async def run_test():
    """Run the quick GIS export test with nice formatting."""
    print_header("Running Quick GIS Export Plugin Test")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    start_time = time.time()
    success = True
    
    try:
        # Test 1: Simple area
        print_section("Test: Simple Area Export")
        simple_result = await test_simple_area()
        print("\nSimple Export Results:")
        print_result("geojson", simple_result['time'], simple_result['size'], simple_result['count'])
        
        # Test 2: Format comparison
        print_section("Test: Format Comparison")
        formats_result = await test_format_comparisons()
        print("\nFormat Comparison Results:")
        for fmt, data in formats_result.items():
            print_result(fmt, data['time'], data['size'], data['count'])
            
        # Calculate execution time
        execution_time = time.time() - start_time
        
        print_section("Test Results")
        print(f"✅ GIS Export test completed successfully in {execution_time:.2f} seconds")
        
    except Exception as e:
        success = False
        print_section("Test Results")
        print(f"❌ GIS Export test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print_header("Test Execution Complete")
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(run_test())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)