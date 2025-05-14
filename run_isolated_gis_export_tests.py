#!/usr/bin/env python3
"""
TerraFusion GIS Export Plugin Test Runner

This script runs the isolated GIS Export plugin tests to avoid metrics registration
conflicts with other tests.
"""

import argparse
import os
import subprocess
import sys
import time

def run_gis_export_tests(host="localhost"):
    """Run the isolated GIS Export tests."""
    print(f"🔄 Running isolated GIS Export plugin tests against {host}...")
    
    # Set environment variables to avoid conflicts
    env = os.environ.copy()
    env["TEST_HOST"] = host
    
    # Run the isolated test script
    cmd = ["python", "isolated_test_gis_export_end_to_end.py", "--host", host]
    
    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Tests completed successfully!")
        print(proc.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Tests failed with exit code {e.returncode}")
        print(f"Error details:")
        print(e.stdout)
        print(e.stderr)
        return e.returncode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run isolated GIS Export plugin tests")
    parser.add_argument("--host", default="localhost", 
                        help="Host where SyncService is running (default: localhost)")
    args = parser.parse_args()
    
    sys.exit(run_gis_export_tests(args.host))