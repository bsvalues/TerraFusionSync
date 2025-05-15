#!/usr/bin/env python3
"""
This script runs the isolated GIS Export metrics server in a workflow.
"""

import os
import sys
import time
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run the isolated metrics service workflow."""
    logger.info("Starting GIS Export isolated metrics service...")
    
    try:
        # Start the FastAPI server process
        process = subprocess.Popen(
            ["python", "isolated_gis_export_metrics.py", "--port", "8090"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Give it time to start up
        time.sleep(3)
        
        # Check if it's running properly
        health_check = subprocess.run(
            ["curl", "-s", "http://0.0.0.0:8090/health"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Health check response: {health_check.stdout}")
        
        # Check metrics endpoint
        metrics_check = subprocess.run(
            ["curl", "-s", "http://0.0.0.0:8090/metrics"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Metrics endpoint response: {metrics_check.stdout}")
        
        # Register a sample job
        sample_job = {
            "job_id": "test-123",
            "county_id": "benton_wa",
            "format": "GeoJSON",
        }
        
        submit_job = subprocess.run(
            ["curl", "-s", "-X", "POST", 
             "-H", "Content-Type: application/json",
             "-d", f'{{"job_id": "test-123", "county_id": "benton_wa", "format": "GeoJSON"}}',
             "http://0.0.0.0:8090/record/job_submitted"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Job submission response: {submit_job.stdout}")
        
        # Check metrics after submission
        after_submit = subprocess.run(
            ["curl", "-s", "http://0.0.0.0:8090/metrics"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Metrics after job submission: {after_submit.stdout}")
        
        # Complete the job
        complete_job = subprocess.run(
            ["curl", "-s", "-X", "POST", 
             "-H", "Content-Type: application/json",
             "-d", f'{{"job_id": "test-123", "duration_seconds": 5, "file_size_kb": 1024, "record_count": 100}}',
             "http://0.0.0.0:8090/record/job_completed"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Job completion response: {complete_job.stdout}")
        
        # Final metrics check
        final_metrics = subprocess.run(
            ["curl", "-s", "http://0.0.0.0:8090/metrics"],
            capture_output=True,
            text=True
        )
        
        logger.info(f"Final metrics: {final_metrics.stdout}")
        
        # Keep the server running
        logger.info("GIS Export metrics server is running. Press Ctrl+C to terminate.")
        
        # Process server logs
        while True:
            line = process.stdout.readline()
            if not line:
                break
            logger.info(f"Server log: {line.strip()}")
        
        # Wait for the server process to terminate
        process.wait()
        logger.info(f"Server process exited with code {process.returncode}")
        
    except KeyboardInterrupt:
        logger.info("Terminating metrics server...")
        try:
            process.terminate()
            process.wait(timeout=5)
        except:
            logger.error("Failed to terminate server gracefully")
    except Exception as e:
        logger.error(f"Error running metrics server: {e}")
        if 'process' in locals():
            try:
                process.terminate()
            except:
                pass

if __name__ == "__main__":
    main()