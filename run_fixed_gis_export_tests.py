#!/usr/bin/env python3
"""
Run fixed GIS Export plugin integration tests.

This script executes the fixed integration tests for the GIS Export plugin,
including the full end-to-end workflow tests.
"""

import os
import sys
import subprocess
import argparse

def main():
    """Run the fixed GIS Export plugin integration tests."""
    parser = argparse.ArgumentParser(description="Run fixed GIS Export plugin integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--show-output", "-s", action="store_true", help="Show test output")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--use-component", action="store_true", help="Use component tests instead of pytest")
    parser.add_argument("--host", default="localhost", help="Host where SyncService is running")
    args = parser.parse_args()
    
    # Set up environment variable for SyncService URL if using component tests
    if args.use_component:
        os.environ["SYNC_SERVICE_URL"] = f"http://{args.host}:8080"
    
    if args.use_component:
        print("Running component tests for GIS Export...")
        cmd = ["python", "test_gis_export_component.py", f"--host={args.host}"]
        try:
            subprocess.run(cmd, check=True)
            print("✅ GIS Export component tests passed")
            return 0
        except subprocess.CalledProcessError:
            print("❌ GIS Export component tests failed")
            return 1
    else:
        # Configure pytest command
        cmd = ["pytest"]
        
        # Add verbosity flag
        if args.verbose:
            cmd.append("-v")
        
        # Add output display flag
        if args.show_output:
            cmd.append("-s")
        
        if not args.skip_integration:
            print("Running fixed GIS Export integration tests...")
            # Use the fixed test file
            integration_cmd = cmd + ["tests/plugins/fixed_test_gis_export_end_to_end.py"]
            try:
                subprocess.run(integration_cmd, check=True)
                print("✅ Fixed GIS Export integration tests passed")
            except subprocess.CalledProcessError:
                print("❌ Fixed GIS Export integration tests failed")
                return 1
        
        print("All requested tests completed successfully")
        return 0

if __name__ == "__main__":
    sys.exit(main())