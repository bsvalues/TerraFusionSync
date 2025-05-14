#!/usr/bin/env python3
"""
Run GIS Export Tests.

This script runs the GIS Export tests and reports the results.
"""

import os
import sys
import subprocess
import argparse
import time
from datetime import datetime

def log(message):
    """Log a message with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_test(test_script, test_name=None, timeout=30):
    """Run a test script and return the result."""
    log(f"Running test: {test_script}" + (f" ({test_name})" if test_name else ""))
    
    command = [sys.executable, test_script]
    if test_name:
        command.extend(['--test', test_name])
    
    try:
        start_time = time.time()
        # Use a simpler approach to avoid ptrace issues in Replit
        result = os.system(" ".join(command))
        elapsed = time.time() - start_time
        # Convert result to process-like object
        class ProcessResult:
            def __init__(self, returncode):
                self.returncode = returncode
                self.stdout = ""
                self.stderr = ""
        
        process = ProcessResult(result // 256)
        
        if process.returncode == 0:
            log(f"✅ Test passed in {elapsed:.2f}s: {test_script}" + (f" ({test_name})" if test_name else ""))
            return True
        else:
            log(f"❌ Test failed with exit code {process.returncode}: {test_script}" + (f" ({test_name})" if test_name else ""))
            log("Test failed - see output above for details")
            return False
    except subprocess.TimeoutExpired:
        log(f"❌ Test timed out after {timeout}s: {test_script}" + (f" ({test_name})" if test_name else ""))
        return False
    except Exception as e:
        log(f"❌ Error running test: {e}")
        return False

def main():
    """Run all tests or a specific test."""
    parser = argparse.ArgumentParser(description="Run GIS Export tests")
    parser.add_argument("--script", help="Specific test script to run")
    parser.add_argument("--test", help="Specific test name to run")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    args = parser.parse_args()
    
    if args.script and os.path.exists(args.script):
        success = run_test(args.script, args.test)
        sys.exit(0 if success else 1)
    
    if args.all or not (args.script or args.test):
        log("Running all GIS Export tests")
        
        # Basic tests
        success = run_test("final_test.py")
        if not success:
            log("❌ Basic tests failed, aborting further tests")
            sys.exit(1)
        
        # API tests
        api_tests = [
            ("run_gis_export_api_test.py", "health"),
            ("run_gis_export_api_test.py", "create"),
            ("run_gis_export_api_test.py", "workflow")
        ]
        
        api_results = []
        for script, test in api_tests:
            if os.path.exists(script):
                result = run_test(script, test)
                api_results.append(result)
        
        if all(api_results):
            log("✅ All API tests passed")
        else:
            log("❌ Some API tests failed")
        
        log("GIS Export tests completed")
        sys.exit(0 if all(api_results) else 1)
    
    log("No valid test specified")
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()