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
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("gis_export_tests")

def run_tests(test_file=None, verbose=False, test_marker=None):
    """
    Run the GIS Export plugin tests using pytest.
    
    Args:
        test_file: Optional specific test file to run
        verbose: Whether to run tests in verbose mode
        test_marker: Optional test marker to run only specific tests
        
    Returns:
        int: 0 if tests passed, non-zero otherwise
    """
    # Build pytest command
    command = ["python", "-m", "pytest"]
    
    # Add verbosity flags
    if verbose:
        command.extend(["-xvs"])
    else:
        command.extend(["-v"])
    
    # Add test marker if specified
    if test_marker:
        command.append(f"-m {test_marker}")
    
    # Add test file(s)
    if test_file:
        # If a specific file is provided, run just that file
        command.append(test_file)
    else:
        # Otherwise, run the fixed test file
        command.append("tests/plugins/fixed_test_gis_export_end_to_end.py")
    
    # Log the command
    logger.info(f"Running: {' '.join(command)}")
    
    try:
        # Run the tests and capture the output
        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        # Print the output
        print("\n--- Test Output ---")
        print(process.stdout)
        
        if process.stderr:
            print("\n--- Error Output ---")
            print(process.stderr)
        
        if process.returncode == 0:
            logger.info("GIS Export tests passed successfully!")
        else:
            logger.error(f"GIS Export tests failed with return code {process.returncode}")
        
        return process.returncode
    except Exception as e:
        logger.error(f"Failed to run tests: {e}")
        return 1

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run GIS Export plugin integration tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Run tests in verbose mode")
    parser.add_argument("--file", "-f", help="Specific test file to run")
    parser.add_argument("--marker", "-m", help="Run tests with specific marker (e.g., integration)")
    args = parser.parse_args()
    
    logger.info("Starting GIS Export plugin tests")
    
    # Record start time
    start_time = datetime.now()
    
    # Run the tests
    result = run_tests(
        test_file=args.file,
        verbose=args.verbose,
        test_marker=args.marker
    )
    
    # Record end time and calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Print summary
    if result == 0:
        logger.info(f"All tests passed in {duration:.2f} seconds!")
    else:
        logger.error(f"Tests failed after {duration:.2f} seconds!")
    
    # Exit with the test result code
    sys.exit(result)

if __name__ == "__main__":
    main()