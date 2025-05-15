#!/usr/bin/env python3
"""
GIS Export API Test Script

This script runs both the isolated metrics service and the main test script.
"""

import os
import sys
import time
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the GIS Export API test."""
    logger.info("Starting GIS Export API test...")
    
    try:
        # Start the isolated metrics service
        logger.info("Starting isolated metrics service...")
        metrics_process = subprocess.Popen(
            ["python", "isolated_gis_export_metrics.py", "--port", "8090"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Wait for the metrics service to start
        logger.info("Waiting for metrics service to start...")
        time.sleep(3)
        
        # Check if metrics service is running
        health_check = subprocess.run(
            ["curl", "-s", "http://0.0.0.0:8090/health"],
            capture_output=True,
            text=True
        )
        
        if "healthy" in health_check.stdout:
            logger.info("Metrics service is running.")
        else:
            logger.error("Metrics service is not running correctly.")
            return 1
        
        # Run the test script
        logger.info("Running test script...")
        test_process = subprocess.run(
            ["python", "run_fixed_gis_export_tests.py"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Test script output:\n{test_process.stdout}")
        
        if test_process.returncode != 0:
            logger.error(f"Test script failed with error:\n{test_process.stderr}")
            return test_process.returncode
        
        logger.info("GIS Export API test completed successfully!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
        return 1
    except Exception as e:
        logger.error(f"Error running test: {e}")
        return 1
    finally:
        # Clean up by terminating the metrics service
        if 'metrics_process' in locals():
            try:
                metrics_process.terminate()
                metrics_process.wait(timeout=5)
                logger.info("Metrics service terminated.")
            except:
                logger.error("Failed to terminate metrics service gracefully.")

if __name__ == "__main__":
    sys.exit(main())