"""
TerraFusion Platform - Sync Service

This module provides the synchronization service that connects with county systems
and keeps data updated between different platforms.
"""

import os
import uuid
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncService:
    """
    Service class for handling synchronization between county systems.
    
    This service manages the synchronization of data between TerraFusion and
    various county systems, ensuring data consistency across platforms.
    """
    
    def __init__(self, storage_path: str = "syncs"):
        """
        Initialize the Sync Service.
        
        Args:
            storage_path: Directory to store sync job files and logs
        """
        self.storage_path = storage_path
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_path, exist_ok=True)
        logger.info(f"Sync Service initialized with storage path: {self.storage_path}")
    
    def create_sync_job(self, 
                       county_id: str, 
                       username: str, 
                       data_types: List[str],
                       source_system: str,
                       target_system: str,
                       parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new synchronization job.
        
        Args:
            county_id: County identifier
            username: Username of the requester
            data_types: Types of data to synchronize (parcels, owners, etc.)
            source_system: Source system identifier
            target_system: Target system identifier
            parameters: Additional parameters for the sync job
            
        Returns:
            Dictionary with job details including the job_id
        """
        # Create a unique job ID
        job_id = str(uuid.uuid4())
        
        # Create job object
        job = {
            "job_id": job_id,
            "county_id": county_id,
            "username": username,
            "data_types": data_types,
            "source_system": source_system,
            "target_system": target_system,
            "parameters": parameters or {},
            "status": "PENDING",
            "created_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "completed_at": None,
            "stats": {
                "records_read": 0,
                "records_processed": 0,
                "records_written": 0,
                "warnings": 0,
                "errors": 0
            },
            "message": "Sync job created and pending processing."
        }
        
        # Save job to storage
        self._save_job(job)
        
        logger.info(f"Created sync job {job_id} for county {county_id}")
        return job
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Get the status of a sync job.
        
        Args:
            job_id: ID of the sync job
            
        Returns:
            Dictionary with job details
            
        Raises:
            FileNotFoundError: If job with the given ID does not exist
        """
        return self._load_job(job_id)
    
    def process_job(self, job_id: str) -> Dict[str, Any]:
        """
        Process a synchronization job.
        
        This method handles the actual synchronization processing, including:
        - Connecting to source and target systems
        - Reading data from source
        - Applying transformations and business rules
        - Writing data to target
        
        Args:
            job_id: ID of the sync job
            
        Returns:
            Dictionary with updated job details
            
        Raises:
            FileNotFoundError: If job with the given ID does not exist
            ValueError: If job is not in PENDING status
        """
        # Load job
        job = self._load_job(job_id)
        
        # Validate job status
        if job["status"] != "PENDING":
            raise ValueError(f"Cannot process job {job_id} with status {job['status']}")
        
        # Update job status to PROCESSING
        job["status"] = "PROCESSING"
        job["started_at"] = datetime.utcnow().isoformat()
        job["message"] = "Sync job is being processed."
        self._save_job(job)
        
        logger.info(f"Processing sync job {job_id}")
        
        try:
            # Simulate processing time and results
            self._simulate_processing(job)
            
            # Update job with success
            job["status"] = "COMPLETED"
            job["completed_at"] = datetime.utcnow().isoformat()
            job["message"] = f"Sync completed successfully with {job['stats']['records_written']} records processed."
            
        except Exception as e:
            # Update job with error
            job["status"] = "FAILED"
            job["completed_at"] = datetime.utcnow().isoformat()
            job["message"] = f"Sync failed: {str(e)}"
            logger.error(f"Error processing sync job {job_id}: {e}", exc_info=True)
        
        # Save updated job
        self._save_job(job)
        logger.info(f"Finished processing sync job {job_id} with status {job['status']}")
        return job
    
    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a pending or processing sync job.
        
        Args:
            job_id: ID of the sync job
            
        Returns:
            Dictionary with updated job details
            
        Raises:
            FileNotFoundError: If job with the given ID does not exist
            ValueError: If job is already completed or failed
        """
        # Load job
        job = self._load_job(job_id)
        
        # Validate job status
        if job["status"] in ["COMPLETED", "FAILED"]:
            raise ValueError(f"Cannot cancel job {job_id} with status {job['status']}")
        
        # Update job status to CANCELLED
        job["status"] = "CANCELLED"
        job["completed_at"] = datetime.utcnow().isoformat()
        job["message"] = "Sync job cancelled by user."
        self._save_job(job)
        
        logger.info(f"Cancelled sync job {job_id}")
        return job
    
    def list_jobs(self, 
                 county_id: Optional[str] = None, 
                 status: Optional[str] = None,
                 username: Optional[str] = None,
                 limit: int = 100) -> List[Dict[str, Any]]:
        """
        List sync jobs with optional filtering.
        
        Args:
            county_id: Filter by county ID
            status: Filter by job status
            username: Filter by username
            limit: Maximum number of jobs to return
            
        Returns:
            List of job dictionaries
        """
        jobs = []
        
        # Find all job files
        os.makedirs(self.storage_path, exist_ok=True)
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.storage_path, filename), 'r') as f:
                        job = json.load(f)
                        
                        # Apply filters
                        if county_id and job.get("county_id") != county_id:
                            continue
                        if status and job.get("status") != status:
                            continue
                        if username and job.get("username") != username:
                            continue
                        
                        jobs.append(job)
                except Exception as e:
                    logger.error(f"Error reading job file {filename}: {e}")
        
        # Sort by creation date (newest first) and apply limit
        jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
        return jobs[:limit]
    
    def get_job_report(self, job_id: str) -> Dict[str, Any]:
        """
        Get a detailed report for a completed sync job.
        
        Args:
            job_id: ID of the sync job
            
        Returns:
            Dictionary with report details
            
        Raises:
            FileNotFoundError: If job with the given ID does not exist
            ValueError: If job is not completed
        """
        # Load job
        job = self._load_job(job_id)
        
        # Validate job status
        if job["status"] != "COMPLETED":
            raise ValueError(f"Cannot get report for job {job_id} with status {job['status']}")
        
        # Generate detailed report
        report = {
            "job_id": job["job_id"],
            "county_id": job["county_id"],
            "username": job["username"],
            "data_types": job["data_types"],
            "source_system": job["source_system"],
            "target_system": job["target_system"],
            "created_at": job["created_at"],
            "started_at": job["started_at"],
            "completed_at": job["completed_at"],
            "duration_seconds": self._calculate_duration(job),
            "stats": job["stats"],
            "summary": self._generate_summary(job)
        }
        
        return report
    
    def _save_job(self, job: Dict[str, Any]) -> None:
        """
        Save job details to a JSON file.
        
        Args:
            job: Job dictionary
        """
        job_id = job["job_id"]
        job_file = os.path.join(self.storage_path, f"{job_id}.json")
        
        with open(job_file, 'w') as f:
            json.dump(job, f, indent=2)
    
    def _load_job(self, job_id: str) -> Dict[str, Any]:
        """
        Load job details from a JSON file.
        
        Args:
            job_id: ID of the sync job
            
        Returns:
            Job dictionary
            
        Raises:
            FileNotFoundError: If job with the given ID does not exist
        """
        job_file = os.path.join(self.storage_path, f"{job_id}.json")
        
        if not os.path.exists(job_file):
            raise FileNotFoundError(f"Sync job {job_id} not found")
        
        with open(job_file, 'r') as f:
            return json.load(f)
    
    def _simulate_processing(self, job: Dict[str, Any]) -> None:
        """
        Simulate processing a sync job.
        
        This method simulates the process of synchronizing data between systems,
        updating the job stats as it goes. In a real implementation, this would
        actually connect to the source and target systems.
        
        Args:
            job: Job dictionary to update
        """
        # Simulate processing with random progress
        import random
        
        # Define parameters for simulation
        data_types = job["data_types"]
        county_id = job["county_id"]
        source_system = job["source_system"]
        target_system = job["target_system"]
        
        # Base records per data type
        base_records = {
            "parcels": 5000,
            "owners": 7500,
            "buildings": 8200,
            "permits": 1200,
            "taxes": 9000,
            "zoning": 300
        }
        
        total_records = 0
        for data_type in data_types:
            # Calculate records for this data type (with some randomness)
            if data_type in base_records:
                records = base_records[data_type]
                # Add some randomness (+/- 10%)
                records = int(records * random.uniform(0.9, 1.1))
                total_records += records
        
        # If data types not in our base list, add some random records
        if total_records == 0:
            total_records = random.randint(1000, 10000)
        
        # Simulate reading records
        job["stats"]["records_read"] = total_records
        
        # Simulate processing with some warnings and errors
        job["stats"]["records_processed"] = total_records
        job["stats"]["warnings"] = random.randint(0, int(total_records * 0.01))  # Up to 1% warnings
        job["stats"]["errors"] = random.randint(0, int(total_records * 0.005))  # Up to 0.5% errors
        
        # Calculate successful writes
        job["stats"]["records_written"] = job["stats"]["records_processed"] - job["stats"]["errors"]
        
        # Simulate processing time
        sleep_time = random.uniform(0.5, 2.0)  # Between 0.5 and 2 seconds
        time.sleep(sleep_time)
    
    def _calculate_duration(self, job: Dict[str, Any]) -> float:
        """
        Calculate the duration of a job in seconds.
        
        Args:
            job: Job dictionary
            
        Returns:
            Duration in seconds or 0 if start/end times not available
        """
        if not job.get("started_at") or not job.get("completed_at"):
            return 0
        
        try:
            start_time = datetime.fromisoformat(job["started_at"])
            end_time = datetime.fromisoformat(job["completed_at"])
            return (end_time - start_time).total_seconds()
        except (ValueError, TypeError):
            return 0
    
    def _generate_summary(self, job: Dict[str, Any]) -> List[str]:
        """
        Generate a summary of the sync job results.
        
        Args:
            job: Job dictionary
            
        Returns:
            List of summary strings
        """
        stats = job["stats"]
        summary = []
        
        # Add basic summary
        summary.append(f"Synchronized data from {job['source_system']} to {job['target_system']}")
        summary.append(f"Data types: {', '.join(job['data_types'])}")
        
        # Add stats summary
        summary.append(f"Read {stats['records_read']} records from source system")
        summary.append(f"Successfully wrote {stats['records_written']} records to target system")
        
        # Add warnings and errors
        if stats["warnings"] > 0:
            summary.append(f"Encountered {stats['warnings']} warnings during processing")
        if stats["errors"] > 0:
            summary.append(f"Encountered {stats['errors']} errors during processing")
        
        # Add efficiency stats
        if stats["records_read"] > 0:
            success_rate = (stats["records_written"] / stats["records_read"]) * 100
            summary.append(f"Success rate: {success_rate:.2f}%")
        
        return summary


# Create a singleton instance
sync_service = SyncService()