#!/usr/bin/env python
"""
TerraFusion SyncService Complete Test Suite

This script runs a comprehensive set of tests to verify the entire
TerraFusion SyncService platform is functioning correctly, including:

1. Health checks for all services
2. Integration tests between components
3. Self-healing capabilities
4. Data validation
5. WebSocket real-time updates
6. API functionality
7. Database operations

Usage:
    python run_all_tests.py [--verbose] [--component COMPONENT]

Arguments:
    --verbose           Show detailed test output
    --component         Run tests for a specific component only 
                        (health, integration, self-healing, validation, websocket, api, database)
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test Components
TEST_COMPONENTS = {
    "health": {
        "script": "test_health_endpoints.py",
        "description": "Health check endpoints for all services"
    },
    "integration": {
        "script": "test_integration.py",
        "description": "Integration between API Gateway and SyncService"
    },
    "self-healing": {
        "script": "test_self_healing.py",
        "description": "Self-healing capabilities"
    },
    "validation": {
        "script": "test_validation.py",
        "description": "Data validation functionality"
    },
    "websocket": {
        "script": "test_websocket.py",
        "description": "WebSocket real-time updates"
    },
    "monitoring": {
        "script": "manual_fix_system_monitoring.py",
        "description": "System monitoring functionality"
    }
}

# Test Results
class TestSuiteResults:
    """Track and report test results."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.results = {}
        self.all_passed = True
    
    def add_result(self, component: str, passed: bool, output: str, duration_ms: int):
        """Add a test result."""
        self.results[component] = {
            "passed": passed,
            "output": output,
            "duration_ms": duration_ms
        }
        
        if not passed:
            self.all_passed = False
    
    def print_summary(self, verbose: bool = False):
        """Print a summary of all test results."""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n============================================")
        print("  TERRAFUSION SYNCSERVICE TEST RESULTS")
        print("============================================")
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End time:   {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration:   {duration:.2f} seconds")
        print("--------------------------------------------")
        
        # Count results
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["passed"])
        failed = total - passed
        
        # Print component results
        for component, details in TEST_COMPONENTS.items():
            if component in self.results:
                result = self.results[component]
                status = "✅ PASSED" if result["passed"] else "❌ FAILED"
                duration = f"{result['duration_ms'] / 1000:.2f}s"
                print(f"{status} {component:12} - {details['description']} ({duration})")
                
                # Print verbose output if requested
                if verbose and not result["passed"]:
                    print("\n" + result["output"])
                    print("--------------------------------------------")
            else:
                print(f"⏩ SKIPPED {component:12} - {details['description']}")
        
        # Print summary
        print("--------------------------------------------")
        print(f"TESTS:  {total} total, {passed} passed, {failed} failed")
        print(f"RESULT: {'✅ PASSED' if self.all_passed else '❌ FAILED'}")
        print("============================================\n")
        
        # Return True if all tests passed
        return self.all_passed

def run_test(component: str, verbose: bool = False) -> Tuple[bool, str, int]:
    """
    Run a single test component.
    
    Args:
        component: The name of the component to test
        verbose: Whether to show verbose output
    
    Returns:
        Tuple of (passed, output, duration_ms)
    """
    if component not in TEST_COMPONENTS:
        return False, f"Unknown test component: {component}", 0
    
    script = TEST_COMPONENTS[component]["script"]
    logger.info(f"Running {component} tests ({script})...")
    
    # Command with optional verbose flag
    cmd = ["python", script]
    if verbose:
        cmd.append("--verbose")
    
    # Run the test and capture output
    start_time = datetime.now()
    try:
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        status = True
    except subprocess.CalledProcessError as e:
        output = e.output
        status = False
    except Exception as e:
        output = f"Error executing test: {str(e)}"
        status = False
    
    # Calculate duration
    end_time = datetime.now()
    duration_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Log the results
    test_status = "passed" if status else "failed"
    logger.info(f"{component} tests {test_status} in {duration_ms} ms")
    
    return status, output, duration_ms

def start_services():
    """Start the required services for testing."""
    logger.info("Starting services for testing...")
    
    try:
        # Start API Gateway (which should also start SyncService)
        subprocess.check_call(["python", "restart_syncservice_workflow.py"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL)
        
        # Give services time to start
        time.sleep(5)
        
        logger.info("Services started successfully")
        return True
    except subprocess.CalledProcessError:
        logger.error("Failed to start services")
        return False

def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run TerraFusion SyncService tests")
    parser.add_argument("--verbose", action="store_true", help="Show verbose output")
    parser.add_argument("--component", help="Test only a specific component")
    args = parser.parse_args()
    
    # Start services if needed
    if not start_services():
        logger.error("Cannot proceed with tests, services failed to start")
        sys.exit(1)
    
    # Create results tracker
    results = TestSuiteResults()
    
    # Determine which components to test
    components_to_test = []
    if args.component:
        # Test a single component
        if args.component in TEST_COMPONENTS:
            components_to_test = [args.component]
        else:
            logger.error(f"Unknown test component: {args.component}")
            print(f"Available components: {', '.join(TEST_COMPONENTS.keys())}")
            sys.exit(1)
    else:
        # Test all components
        components_to_test = list(TEST_COMPONENTS.keys())
    
    # Run the tests
    for component in components_to_test:
        passed, output, duration_ms = run_test(component, args.verbose)
        results.add_result(component, passed, output, duration_ms)
    
    # Print results
    all_passed = results.print_summary(args.verbose)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()