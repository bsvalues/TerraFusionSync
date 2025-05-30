#!/usr/bin/env python3
"""
Run tests for TerraFusion SyncService.

This script helps run the test suite for the TerraFusion SyncService.
It is especially helpful for running async tests that require special consideration.
"""

import os
import sys
import asyncio
import pytest
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("tests")

def run_specific_tests(test_path):
    """Run specific tests based on the given path."""
    logger.info(f"Running tests from: {test_path}")
    
    # Add pytest arguments for better output
    pytest_args = [
        "-v",  # verbose
        "--tb=native",  # traceback style
        "-xvs",  # exit on first failure, verbose, no capture
        test_path
    ]
    
    # Run pytest
    result = pytest.main(pytest_args)
    
    return result

def run_all_tests():
    """Run all tests in the tests directory."""
    logger.info("Running all tests")
    
    pytest_args = [
        "-v",
        "--tb=native",
        "-xvs",
        "tests/"
    ]
    
    # Run pytest
    result = pytest.main(pytest_args)
    
    return result

def run_plugin_tests():
    """Run all plugin tests."""
    logger.info("Running plugin tests")
    
    pytest_args = [
        "-v",
        "--tb=native",
        "-xvs",
        "tests/plugins/"
    ]
    
    # Run pytest
    result = pytest.main(pytest_args)
    
    return result

def run_reporting_tests():
    """Run reporting plugin tests."""
    logger.info("Running reporting plugin tests")
    
    pytest_args = [
        "-v",
        "--tb=native",
        "-xvs",
        "tests/plugins/test_reporting.py"
    ]
    
    # Run pytest
    result = pytest.main(pytest_args)
    
    return result

if __name__ == "__main__":
    # Check for specific test path
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
        exit_code = run_specific_tests(test_path)
    else:
        # Default to running all tests
        exit_code = run_reporting_tests()
    
    sys.exit(exit_code)