#!/usr/bin/env python3
"""
Run Market Analysis Plugin Integration Tests

This script launches the integration tests for the Market Analysis plugin.
It sets up the environment and runs pytest with the appropriate arguments.

Usage:
    python run_market_analysis_tests.py
"""

import sys
import os
import subprocess
import pytest
import time

# Add parent directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ["TESTING"] = "True"

def run_market_analysis_tests():
    """Run the Market Analysis integration tests."""
    print("\n=== Running Market Analysis Integration Tests ===\n")
    
    # Run the tests using pytest
    test_args = [
        "terrafusion_platform/tests/integration/test_market_analysis_end_to_end.py",
        "-v",  # Verbose
        "-s",  # Don't capture stdout (so we can see print statements)
    ]

    try:
        result = pytest.main(test_args)
        return result == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    # Run the Market Analysis integration tests
    success = run_market_analysis_tests()
    
    if success:
        print("\n✅ Market Analysis integration tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Market Analysis integration tests failed.")
        sys.exit(1)