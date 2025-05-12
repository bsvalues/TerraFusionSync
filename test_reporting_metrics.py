#!/usr/bin/env python3
"""
Script to generate test data for report metrics visualization in Grafana.
This will trigger report jobs with various statuses to populate the Prometheus metrics.
"""

import argparse
import random
import requests
import time
import logging
import json
import sys
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("report-test-generator")

# Configuration
SYNCSERVICE_URL = "http://0.0.0.0:8080"
REPORT_TYPES = ["property_summary", "tax_assessment", "market_valuation", "FAILING_REPORT_SIM"]
COUNTY_IDS = ["county1", "county2", "demo_county"]


def submit_report_job(report_type: str, county_id: str, parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Submit a new report job to the SyncService.
    
    Args:
        report_type: Type of report to generate
        county_id: County ID for the report
        parameters: Additional parameters for the report
        
    Returns:
        Response from the API or None if failed
    """
    url = f"{SYNCSERVICE_URL}/plugins/v1/reporting/run"
    
    payload = {
        "report_type": report_type,
        "county_id": county_id,
        "parameters": parameters
    }
    
    try:
        logger.info(f"Submitting report job: {payload}")
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Successfully submitted report job: {result.get('report_id')}")
        return result
    except Exception as e:
        logger.error(f"Failed to submit report job: {e}")
        return None


def generate_random_parameters() -> Dict[str, Any]:
    """
    Generate random parameters for report jobs.
    
    Returns:
        Dictionary with random parameters
    """
    property_ids = [f"PROP{random.randint(1000, 9999)}" for _ in range(random.randint(1, 5))]
    
    return {
        "property_ids": property_ids,
        "include_history": random.choice([True, False]),
        "format": random.choice(["pdf", "csv", "json"]),
        "max_records": random.randint(10, 100),
        "start_date": "2025-01-01",
        "end_date": "2025-05-12"
    }


def generate_test_data(num_jobs: int, interval_sec: float):
    """
    Generate test data by submitting report jobs.
    
    Args:
        num_jobs: Number of jobs to submit
        interval_sec: Interval between job submissions in seconds
    """
    submitted_jobs = []
    
    # Submit initial batch of jobs
    for i in range(num_jobs):
        report_type = random.choice(REPORT_TYPES)
        county_id = random.choice(COUNTY_IDS)
        parameters = generate_random_parameters()
        
        result = submit_report_job(report_type, county_id, parameters)
        if result:
            submitted_jobs.append(result)
        
        # Add some randomness to the interval
        sleep_time = interval_sec * (0.8 + 0.4 * random.random())
        time.sleep(sleep_time)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate test report jobs for metrics visualization")
    parser.add_argument("--jobs", type=int, default=10, help="Number of jobs to submit")
    parser.add_argument("--interval", type=float, default=2.0, help="Interval between job submissions in seconds")
    
    args = parser.parse_args()
    
    logger.info(f"Starting test data generation with {args.jobs} jobs at {args.interval}s intervals")
    generate_test_data(args.jobs, args.interval)
    logger.info("Test data generation complete")


if __name__ == "__main__":
    main()