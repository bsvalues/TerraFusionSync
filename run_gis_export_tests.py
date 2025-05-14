#!/usr/bin/env python3
"""
Run GIS Export plugin integration tests.

This script executes the integration tests for the GIS Export plugin,
including the full end-to-end workflow tests.
"""

import os
import sys
import subprocess
import argparse

def main():
    """Run the GIS Export plugin integration tests."""
    parser = argparse.ArgumentParser(description="Run GIS Export plugin integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--show-output", "-s", action="store_true", help="Show test output")
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration tests")
    args = parser.parse_args()
    
    # Configure test command
    cmd = ["pytest"]
    
    # Add verbosity flag
    if args.verbose:
        cmd.append("-v")
    
    # Add output display flag
    if args.show_output:
        cmd.append("-s")
    
    if not args.skip_unit:
        print("Running GIS Export unit tests...")
        unit_cmd = cmd + ["tests/plugins/test_gis-export.py"]
        try:
            subprocess.run(unit_cmd, check=True)
            print("✅ GIS Export unit tests passed")
        except subprocess.CalledProcessError:
            print("❌ GIS Export unit tests failed")
            return 1
        except FileNotFoundError:
            print("⚠️ Unit test file not found, skipping")
    
    if not args.skip_integration:
        print("Running GIS Export integration tests...")
        integration_cmd = cmd + ["tests/plugins/test_gis-export_end_to_end.py"]
        try:
            subprocess.run(integration_cmd, check=True)
            print("✅ GIS Export integration tests passed")
        except subprocess.CalledProcessError:
            print("❌ GIS Export integration tests failed")
            return 1
    
    print("All requested tests completed successfully")
    return 0

if __name__ == "__main__":
    sys.exit(main())