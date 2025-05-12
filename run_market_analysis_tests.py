#!/usr/bin/env python
"""
Run Market Analysis Plugin Integration Tests

This script launches the integration tests for the Market Analysis plugin.
It sets up the environment and runs pytest with the appropriate arguments.

Usage:
    python run_market_analysis_tests.py
"""
import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("market_analysis_tests")

def run_market_analysis_tests():
    """Run the Market Analysis integration tests."""
    logger.info("Running Market Analysis integration tests...")
    
    # Set up the Python path to include project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the Python path is set correctly
    python_path = os.environ.get("PYTHONPATH", "")
    if current_dir not in python_path:
        if python_path:
            os.environ["PYTHONPATH"] = f"{current_dir}:{python_path}"
        else:
            os.environ["PYTHONPATH"] = current_dir
    
    # Run pytest with specific parameters
    try:
        # Command to run pytest targeting the Market Analysis test module
        pytest_cmd = [
            "python", "-m", "pytest",
            "terrafusion_platform/tests/integration/test_market_analysis_end_to_end.py",
            "-v",  # Verbose output
            "--asyncio-mode=auto",  # Required for async tests
            "-m", "integration",  # Run only tests marked as 'integration'
        ]
        
        logger.info(f"Executing: {' '.join(pytest_cmd)}")
        
        # Run pytest and capture output
        result = subprocess.run(
            pytest_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Don't raise exception, we handle it below
        )
        
        # Print output
        print("\n=== Pytest Output ===")
        print(result.stdout)
        
        if result.stderr:
            print("\n=== Pytest Errors ===")
            print(result.stderr)
        
        # Report the final status
        if result.returncode == 0:
            logger.info("Market Analysis tests completed successfully!")
            return True
        else:
            logger.error(f"Market Analysis tests failed with exit code {result.returncode}")
            return False
        
    except Exception as e:
        logger.error(f"Failed to run Market Analysis tests: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_market_analysis_tests()
    sys.exit(0 if success else 1)