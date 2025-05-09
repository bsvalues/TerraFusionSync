#!/usr/bin/env python3
"""
Run integration tests for the TerraFusion Reporting API

This script runs integration tests specifically for the reporting plugin endpoints.
"""

import os
import sys
import subprocess
from pathlib import Path


def is_test_db_configured():
    """Check if the TEST_DATABASE_URL is set in the environment variables."""
    return bool(os.environ.get("TEST_DATABASE_URL"))


def get_test_database_url():
    """Get the TEST_DATABASE_URL from .env file if available."""
    default_db_url = os.environ.get("DATABASE_URL")
    if not default_db_url:
        print("ERROR: No DATABASE_URL found in environment. Database URL is required.")
        return None
    
    # Default to using the same database as DATABASE_URL but with _test suffix
    # This assumes the default URL is not already a test database.
    if "postgresql://" in default_db_url:
        # For postgres URLs, add _test to the database name
        db_parts = default_db_url.split('/')
        if len(db_parts) > 3:  # Ensure we have enough parts to modify
            db_name = db_parts[-1].split('?')[0]  # Get the db name without query params
            if not db_name.endswith('_test'):
                db_parts[-1] = db_name + '_test' + (('?' + db_parts[-1].split('?')[1]) if '?' in db_parts[-1] else '')
                test_db_url = '/'.join(db_parts)
                return test_db_url
    
    # Fallback to the same database, which is not ideal for testing
    print("WARNING: Could not create a TEST_DATABASE_URL. Using the same database for tests.")
    return default_db_url


def run_tests(test_path=None):
    """Run the integration tests for the reporting plugin."""
    # The path where our tests are located
    if test_path is None:
        test_path = "terrafusion_platform/tests/integration/test_reporting_end_to_end.py"
    
    # Ensure the test file exists
    if not Path(test_path).exists():
        print(f"ERROR: Test file not found at {test_path}")
        return False
    
    # Make sure pytest is available
    try:
        import pytest
    except ImportError:
        print("Installing pytest...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pytest", "pytest-asyncio"])
    
    # Ensure TEST_DATABASE_URL is set
    if not is_test_db_configured():
        test_db_url = get_test_database_url()
        if test_db_url:
            os.environ["TEST_DATABASE_URL"] = test_db_url
            print(f"Set TEST_DATABASE_URL to: {test_db_url}")
        else:
            print("ERROR: Failed to determine TEST_DATABASE_URL")
            return False
    
    # Run the tests with pytest
    print(f"\nRunning tests from: {test_path}")
    cmd = [
        sys.executable, "-m", "pytest", 
        test_path, 
        "-v",  # verbose output
        "--asyncio-mode=auto"  # autodetect asyncio mode
    ]
    
    result = subprocess.run(cmd)
    return result.returncode == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)