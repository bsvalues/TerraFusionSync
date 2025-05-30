#!/usr/bin/env python3
"""
TerraFusion GIS Export Demo Script

This script demonstrates how to interact with the GIS Export plugin API,
providing a simple command-line interface for county staff to test exports.
"""

import os
import sys
import json
import time
import argparse
import requests
from typing import Dict, List, Any, Optional


def check_health(base_url):
    """Check the health of the GIS Export plugin."""
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error checking health: {str(e)}")
        sys.exit(1)


def create_export_job(base_url, county_id, export_format, username, area_of_interest, layers, parameters):
    """Create a new GIS export job."""
    try:
        data = {
            "county_id": county_id,
            "username": username,
            "export_format": export_format,
            "area_of_interest": area_of_interest,
            "layers": layers,
            "parameters": parameters or {}
        }
        
        response = requests.post(
            f"{base_url}/api/v1/gis-export/jobs",
            json=data
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error creating export job: {str(e)}")
        if hasattr(e, 'response') and e.response and e.response.text:
            print(f"Response: {e.response.text}")
        sys.exit(1)


def check_job_status(base_url, job_id):
    """Check the status of a GIS export job."""
    try:
        response = requests.get(f"{base_url}/api/v1/gis-export/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error checking job status: {str(e)}")
        sys.exit(1)


def get_job_results(base_url, job_id):
    """Get the results of a completed GIS export job."""
    try:
        # Verify job is completed first
        job = check_job_status(base_url, job_id)
        if job["status"] != "COMPLETED":
            print(f"Job is not completed. Current status: {job['status']}")
            return None
        
        # Download the file
        print(f"Downloading export file from {base_url}/api/v1/gis-export/download/{job_id}")
        
        response = requests.get(
            f"{base_url}/api/v1/gis-export/download/{job_id}",
            stream=True
        )
        response.raise_for_status()
        
        # Get filename from content-disposition header if available
        content_disposition = response.headers.get('Content-Disposition', '')
        filename = None
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"')
        
        if not filename:
            # Use job ID and export format as fallback
            export_format = job.get("export_format", "unknown")
            filename = f"export_{job_id}.{export_format}"
        
        # Save the file
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Export file saved as: {filename}")
        return filename
    except Exception as e:
        print(f"Error getting job results: {str(e)}")
        sys.exit(1)


def cancel_job(base_url, job_id):
    """Cancel a running GIS export job."""
    try:
        response = requests.post(f"{base_url}/api/v1/gis-export/jobs/{job_id}/cancel")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error cancelling job: {str(e)}")
        sys.exit(1)


def list_jobs(base_url, county_id=None, status=None, limit=None):
    """List GIS export jobs with optional filtering."""
    try:
        params = {}
        if county_id:
            params['county_id'] = county_id
        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit
            
        response = requests.get(
            f"{base_url}/api/v1/gis-export/jobs",
            params=params
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error listing jobs: {str(e)}")
        sys.exit(1)


def wait_for_job_completion(base_url, job_id, timeout_seconds=60, check_interval=2):
    """Wait for a job to complete, with timeout."""
    start_time = time.time()
    while True:
        job = check_job_status(base_url, job_id)
        
        if job["status"] in ["COMPLETED", "FAILED", "CANCELLED"]:
            return job
        
        if time.time() - start_time > timeout_seconds:
            print(f"Timeout waiting for job completion. Current status: {job['status']}")
            return job
        
        print(f"Job status: {job['status']}. Waiting {check_interval} seconds...")
        time.sleep(check_interval)


def run_complete_workflow(base_url, county_id, export_format, username, area_of_interest, layers, parameters, timeout_seconds=60):
    """Run a complete GIS export workflow from job creation to result retrieval."""
    print(f"Creating GIS export job for county {county_id}...")
    job = create_export_job(
        base_url, county_id, export_format, username, area_of_interest, layers, parameters
    )
    job_id = job["job_id"]
    print(f"Job created with ID: {job_id}")
    
    print("Waiting for job completion...")
    job = wait_for_job_completion(base_url, job_id, timeout_seconds)
    
    if job["status"] == "COMPLETED":
        print("Job completed successfully!")
        return get_job_results(base_url, job_id)
    else:
        print(f"Job did not complete successfully. Final status: {job['status']}")
        print(f"Message: {job.get('message', 'No message provided')}")
        return None


def main():
    """Main function to parse arguments and run the selected operation."""
    parser = argparse.ArgumentParser(description="TerraFusion GIS Export Demo CLI")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL for TerraFusion API")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check API health")
    
    # Create job command
    create_parser = subparsers.add_parser("create", help="Create a new export job")
    create_parser.add_argument("--county", required=True, help="County ID")
    create_parser.add_argument("--format", required=True, choices=["shapefile", "geojson", "kml", "geopackage", "csv"], help="Export format")
    create_parser.add_argument("--username", required=True, help="Username of the requester")
    create_parser.add_argument("--layers", required=True, nargs="+", help="Layers to export")
    create_parser.add_argument("--aoi", help="File containing GeoJSON area of interest")
    create_parser.add_argument("--parameters", help="File containing JSON parameters")
    
    # Get job status command
    status_parser = subparsers.add_parser("status", help="Get job status")
    status_parser.add_argument("job_id", help="Job ID")
    
    # List jobs command
    list_parser = subparsers.add_parser("list", help="List export jobs")
    list_parser.add_argument("--county", help="Filter by county ID")
    list_parser.add_argument("--status", choices=["PENDING", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"], help="Filter by status")
    list_parser.add_argument("--limit", type=int, default=10, help="Maximum number of jobs to return")
    
    # Download results command
    download_parser = subparsers.add_parser("download", help="Download job results")
    download_parser.add_argument("job_id", help="Job ID")
    
    # Cancel job command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a job")
    cancel_parser.add_argument("job_id", help="Job ID")
    
    # Run complete workflow command
    workflow_parser = subparsers.add_parser("workflow", help="Run complete export workflow")
    workflow_parser.add_argument("--county", required=True, help="County ID")
    workflow_parser.add_argument("--format", required=True, choices=["shapefile", "geojson", "kml", "geopackage", "csv"], help="Export format")
    workflow_parser.add_argument("--username", required=True, help="Username of the requester")
    workflow_parser.add_argument("--layers", required=True, nargs="+", help="Layers to export")
    workflow_parser.add_argument("--aoi", help="File containing GeoJSON area of interest")
    workflow_parser.add_argument("--parameters", help="File containing JSON parameters")
    workflow_parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds")
    
    args = parser.parse_args()
    
    # Default area of interest (if not provided)
    default_aoi = {
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
    }
    
    # Execute the selected command
    if args.command == "health":
        result = check_health(args.url)
        print(json.dumps(result, indent=2))
        
    elif args.command == "create":
        # Load area of interest from file or use default
        aoi = default_aoi
        if args.aoi:
            with open(args.aoi, 'r') as f:
                aoi = json.load(f)
        
        # Load parameters from file or use empty dict
        parameters = {}
        if args.parameters:
            with open(args.parameters, 'r') as f:
                parameters = json.load(f)
        
        job = create_export_job(
            args.url, args.county, args.format, args.username, aoi, args.layers, parameters
        )
        print(json.dumps(job, indent=2))
        
    elif args.command == "status":
        job = check_job_status(args.url, args.job_id)
        print(json.dumps(job, indent=2))
        
    elif args.command == "list":
        jobs = list_jobs(args.url, args.county, args.status, args.limit)
        print(json.dumps(jobs, indent=2))
        
    elif args.command == "download":
        filename = get_job_results(args.url, args.job_id)
        if filename:
            print(f"Downloaded file: {filename}")
        
    elif args.command == "cancel":
        job = cancel_job(args.url, args.job_id)
        print(json.dumps(job, indent=2))
        
    elif args.command == "workflow":
        # Load area of interest from file or use default
        aoi = default_aoi
        if args.aoi:
            with open(args.aoi, 'r') as f:
                aoi = json.load(f)
        
        # Load parameters from file or use empty dict
        parameters = {}
        if args.parameters:
            with open(args.parameters, 'r') as f:
                parameters = json.load(f)
        
        filename = run_complete_workflow(
            args.url, args.county, args.format, args.username, aoi, args.layers,
            parameters, args.timeout
        )
        if filename:
            print(f"Complete workflow executed successfully. Output file: {filename}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()