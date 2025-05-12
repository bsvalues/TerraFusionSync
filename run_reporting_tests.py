#!/usr/bin/env python3
"""
Run reporting plugin tests for TerraFusion SyncService.

This script provides a specialized environment for running the reporting plugin tests,
configured to properly handle async test cases.
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
logger = logging.getLogger("reporting_tests")

def run_reporting_tests():
    """Run tests for the reporting plugin."""
    logger.info("Running reporting plugin tests")
    
    # Configure asyncio for pytest
    os.environ["PYTEST_ASYNCIO_MODE"] = "auto"
    
    pytest_args = [
        "-v",
        "--tb=native",
        "--asyncio-mode=auto",  # Use auto mode for asyncio
        "-xvs",
        "tests/plugins/test_reporting.py"
    ]
    
    # Run pytest
    result = pytest.main(pytest_args)
    
    return result

if __name__ == "__main__":
    # Run the reporting tests
    exit_code = run_reporting_tests()
    sys.exit(exit_code)