#!/usr/bin/env python3
"""
Run reporting integration tests.

This script runs the reporting-specific integration tests for the TerraFusion platform.
"""

import os
import sys
import pytest
import asyncio


if __name__ == "__main__":
    # Add root directory to Python path for imports
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Set test environment variables if needed
    os.environ["PYTHONPATH"] = os.path.dirname(os.path.abspath(__file__))
    
    # Make sure asyncio runs properly
    if sys.platform == "win32" and sys.version_info >= (3, 8):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Run reporting tests only
    test_args = [
        "-xvs",  # Exit on first failure, verbose, output to console
        "terrafusion_platform/tests/integration/test_reporting_end_to_end.py",
        "terrafusion_platform/tests/integration/test_reporting_api_endpoints.py",
    ]
    
    # Check if we should run a specific test only
    if len(sys.argv) > 1 and sys.argv[1] == "--end-to-end-only":
        # Run only the end-to-end test
        test_args = [
            "-xvs",
            "terrafusion_platform/tests/integration/test_reporting_end_to_end.py",
        ]
        # Remove this argument to prevent it from being passed to pytest
        sys.argv.pop(1)
    elif len(sys.argv) > 1 and sys.argv[1] == "--api-only":
        # Run only the API endpoint tests
        test_args = [
            "-xvs",
            "terrafusion_platform/tests/integration/test_reporting_api_endpoints.py",
        ]
        # Remove this argument to prevent it from being passed to pytest
        sys.argv.pop(1)
    
    # Add any additional command line arguments
    test_args.extend(sys.argv[1:])
    
    # Run the tests
    print(f"Running tests with args: {test_args}")
    sys.exit(pytest.main(test_args))