"""
TerraFusion SyncService - Market Analysis Plugin - Service

This module provides the core business logic for the Market Analysis plugin.
It handles job management, data processing, and result generation.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Awaitable
import asyncio

from sqlalchemy import select, desc, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from terrafusion_sync.plugins.market_analysis.models import MarketAnalysisJob
from terrafusion_sync.plugins.market_analysis.metrics import (
    update_running_jobs,
    record_job_completion,
    record_job_failure,
    record_job_creation
)

# Configure logger
logger = logging.getLogger(__name__)

class MarketAnalysisService:
    """
    Service for managing market analysis jobs and processing analysis requests.
    This service acts as a coordinator between the API layer and the data processing logic.
    """
    
    def __init__(self, get_session_factory):
        """
        Initialize the service with a session factory function.
        
        Args:
            get_session_factory: Callable that returns an async database session
        """
        self.get_session = get_session_factory
        logger.info("Market Analysis service initialized")
    
    async def create_job(self, county_id: str, analysis_type: str, parameters: Dict[str, Any]) -> str:
        """
        Create a new market analysis job and return the job ID.
        
        Args:
            county_id: ID of the county for which to run the analysis
            analysis_type: Type of analysis to perform
            parameters: Parameters specific to the analysis type
            
        Returns:
            str: Job ID of the created job
        """
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        # Create job record
        async with self.get_session() as session:
            job = MarketAnalysisJob(
                job_id=job_id,
                county_id=county_id,
                analysis_type=analysis_type,
                parameters_json=json.dumps(parameters),
                status="PENDING",
                message="Job created and queued for processing",
                created_at=now,
                updated_at=now
            )
            
            session.add(job)
            await session.commit()
            
        # Record metric
        record_job_creation(county_id, analysis_type)
        
        # Start background processing
        asyncio.create_task(self._process_job_async(job_id))
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a job.
        
        Args:
            job_id: ID of the job to check
            
        Returns:
            dict or None: Job details if found, None otherwise
        """
        async with self.get_session() as session:
            job = await self._get_job(session, job_id)
            
            if not job:
                return None
            
            return self._job_to_dict(job)
    
    async def get_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the result of a completed job.
        
        Args:
            job_id: ID of the job
            
        Returns:
            dict or None: Job details with results if found and completed, None otherwise
        """
        async with self.get_session() as session:
            job = await self._get_job(session, job_id)
            
            if not job:
                return None
            
            result = self._job_to_dict(job)
            
            # Add parsed parameters and results
            try:
                result["parameters"] = json.loads(job.parameters_json) if job.parameters_json else {}
            except (json.JSONDecodeError, TypeError):
                result["parameters"] = {}
                
            try:
                result["results"] = json.loads(job.result_json) if job.result_json else {}
            except (json.JSONDecodeError, TypeError):
                result["results"] = {}
                
            return result
    
    async def list_jobs(self, county_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List jobs, optionally filtered by county.
        
        Args:
            county_id: Optional county ID to filter jobs by
            limit: Maximum number of jobs to return
            
        Returns:
            list: List of job details dictionaries
        """
        async with self.get_session() as session:
            query = select(MarketAnalysisJob).order_by(desc(MarketAnalysisJob.created_at)).limit(limit)
            
            if county_id:
                query = query.filter(MarketAnalysisJob.county_id == county_id)
            
            result = await session.execute(query)
            jobs = result.scalars().all()
            
            return [self._job_to_dict(job) for job in jobs]
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job if it's still pending or running.
        
        Args:
            job_id: ID of the job to cancel
            
        Returns:
            bool: True if job was cancelled, False otherwise
        """
        async with self.get_session() as session:
            job = await self._get_job(session, job_id)
            
            if not job or job.status not in ["PENDING", "RUNNING"]:
                return False
            
            # Update job status
            job.status = "CANCELLED"
            job.message = "Job cancelled by user"
            job.updated_at = datetime.utcnow()
            
            await session.commit()
            
            return True
    
    async def cleanup_stale_jobs(self, max_age_hours: int = 24) -> int:
        """
        Update status of jobs that have been stuck in RUNNING state.
        
        Args:
            max_age_hours: Maximum age in hours for a running job before it's considered stale
            
        Returns:
            int: Number of jobs updated
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async with self.get_session() as session:
            # Find running jobs that haven't been updated recently
            query = select(MarketAnalysisJob).filter(
                and_(
                    MarketAnalysisJob.status == "RUNNING",
                    MarketAnalysisJob.updated_at < cutoff_time
                )
            )
            
            result = await session.execute(query)
            stale_jobs = result.scalars().all()
            
            # Update job statuses
            for job in stale_jobs:
                job.status = "FAILED"
                job.message = f"Job timed out after {max_age_hours} hours"
                job.updated_at = datetime.utcnow()
            
            if stale_jobs:
                await session.commit()
                
            return len(stale_jobs)
    
    async def _process_job_async(self, job_id: str) -> None:
        """
        Process a job asynchronously in the background.
        
        This method is designed to be run as a background task.
        
        Args:
            job_id: ID of the job to process
        """
        logger.info(f"Starting processing of job {job_id}")
        
        try:
            async with self.get_session() as session:
                # Get the job
                job = await self._get_job(session, job_id)
                
                if not job:
                    logger.warning(f"Job {job_id} not found, cannot process")
                    return
                
                # Update status to RUNNING
                job.status = "RUNNING"
                job.message = "Job is being processed"
                job.started_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                await session.commit()
                
                # Process based on job type
                parameters = {}
                try:
                    parameters = json.loads(job.parameters_json) if job.parameters_json else {}
                except (json.JSONDecodeError, TypeError):
                    logger.warning(f"Failed to parse parameters for job {job_id}")
                
                # Update metrics
                county_id_str = str(job.county_id) if job.county_id else "unknown"
                analysis_type_str = str(job.analysis_type) if job.analysis_type else "unknown"
                update_running_jobs(county_id_str, analysis_type_str)
                
                # Process based on analysis type
                try:
                    if job.analysis_type == "price_trend_by_zip":
                        result = await self._process_price_trend(job.county_id, parameters)
                    elif job.analysis_type == "comparable_market_area":
                        result = await self._process_comparable_market(job.county_id, parameters)
                    elif job.analysis_type == "sales_velocity":
                        result = await self._process_sales_velocity(job.county_id, parameters)
                    elif job.analysis_type == "market_valuation":
                        result = await self._process_market_valuation(job.county_id, parameters)
                    elif job.analysis_type == "price_per_sqft":
                        result = await self._process_price_per_sqft(job.county_id, parameters)
                    else:
                        raise ValueError(f"Unknown analysis type: {job.analysis_type}")
                    
                    # Update job with result
                    job.status = "COMPLETED"
                    job.message = "Job completed successfully"
                    job.result_json = json.dumps(result)
                    # Summary is a simplified version of the result for quick access
                    job.result_summary_json = json.dumps(self._create_summary(result))
                    job.completed_at = datetime.utcnow()
                    job.updated_at = datetime.utcnow()
                    
                    # Update metrics
                    county_id_str = str(job.county_id) if job.county_id else "unknown"
                    analysis_type_str = str(job.analysis_type) if job.analysis_type else "unknown"
                    record_job_completion(county_id_str, analysis_type_str)
                    
                except Exception as e:
                    logger.exception(f"Error processing job {job_id}: {str(e)}")
                    
                    # Update job with error
                    job.status = "FAILED"
                    job.message = f"Error: {str(e)}"
                    job.completed_at = datetime.utcnow()
                    job.updated_at = datetime.utcnow()
                    
                    # Update metrics
                    county_id_str = str(job.county_id) if job.county_id else "unknown"
                    analysis_type_str = str(job.analysis_type) if job.analysis_type else "unknown"
                    record_job_failure(county_id_str, analysis_type_str)
                
                # Save changes
                await session.commit()
                logger.info(f"Finished processing job {job_id}, status={job.status}")
                
        except Exception as e:
            logger.exception(f"Unhandled error processing job {job_id}: {str(e)}")
    
    async def _get_job(self, session: AsyncSession, job_id: str) -> Optional[MarketAnalysisJob]:
        """
        Get a job by ID.
        
        Args:
            session: Database session
            job_id: ID of the job to get
            
        Returns:
            MarketAnalysisJob or None: Job if found, None otherwise
        """
        query = select(MarketAnalysisJob).filter(MarketAnalysisJob.job_id == job_id)
        result = await session.execute(query)
        return result.scalars().first()
    
    def _job_to_dict(self, job: MarketAnalysisJob) -> Dict[str, Any]:
        """
        Convert a job model to a dictionary representation.
        
        Args:
            job: Job model to convert
            
        Returns:
            dict: Dictionary representation of the job
        """
        def serialize_datetime(dt):
            """Serialize a datetime object to ISO format string."""
            return dt.isoformat() if dt else None
        
        return {
            "job_id": job.job_id,
            "county_id": job.county_id,
            "analysis_type": job.analysis_type,
            "status": job.status,
            "message": job.message,
            "created_at": serialize_datetime(job.created_at),
            "updated_at": serialize_datetime(job.updated_at),
            "started_at": serialize_datetime(job.started_at),
            "completed_at": serialize_datetime(job.completed_at)
        }
    
    def _create_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of the result for quick access.
        
        Args:
            result: Full result dictionary
            
        Returns:
            dict: Summary dictionary
        """
        summary = {}
        
        # Include key metrics in summary
        if "average_price" in result:
            summary["average_price"] = result["average_price"]
        if "median_price" in result:
            summary["median_price"] = result["median_price"]
        if "sample_size" in result:
            summary["sample_size"] = result["sample_size"]
            
        # Add analysis-specific metrics
        if "trend_direction" in result:
            summary["trend_direction"] = result["trend_direction"]
        if "days_on_market" in result:
            summary["days_on_market"] = result["days_on_market"]
        if "price_per_sqft" in result:
            summary["price_per_sqft"] = result["price_per_sqft"]
            
        return summary
    
    async def _process_price_trend(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process price trend analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulated processing time
        await asyncio.sleep(2)
        
        # Sample data structure for price trend analysis
        return {
            "average_price": 850000,
            "median_price": 780000,
            "price_trend": [
                {"month": "2024-01", "avg_price": 780000},
                {"month": "2024-02", "avg_price": 795000},
                {"month": "2024-03", "avg_price": 810000},
                {"month": "2024-04", "avg_price": 835000},
                {"month": "2024-05", "avg_price": 850000},
            ],
            "trend_direction": "upward",
            "trend_percentage": 8.97,
            "sample_size": 187
        }
    
    async def _process_comparable_market(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process comparable market area analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulated processing time
        await asyncio.sleep(3)
        
        # Sample data structure for comparable market analysis
        return {
            "average_price": 920000,
            "median_price": 875000,
            "comparable_areas": [
                {"zip_code": "90211", "similarity": 0.92, "avg_price": 890000},
                {"zip_code": "90212", "similarity": 0.87, "avg_price": 950000},
                {"zip_code": "90024", "similarity": 0.81, "avg_price": 1050000}
            ],
            "price_index": 112.5,
            "sample_size": 143
        }
    
    async def _process_sales_velocity(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sales velocity analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulated processing time
        await asyncio.sleep(2.5)
        
        # Sample data structure for sales velocity analysis
        return {
            "days_on_market": 28,
            "sales_per_month": 42,
            "velocity_trend": [
                {"month": "2024-01", "days_on_market": 35, "sales": 38},
                {"month": "2024-02", "days_on_market": 32, "sales": 40},
                {"month": "2024-03", "days_on_market": 29, "sales": 41},
                {"month": "2024-04", "days_on_market": 28, "sales": 42}
            ],
            "seasonal_adjustment": 1.05,
            "sample_size": 165
        }
    
    async def _process_market_valuation(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market valuation for a specific property.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulated processing time
        await asyncio.sleep(4)
        
        # Get property attributes from parameters
        property_id = parameters.get("property_id", "unknown")
        sqft = parameters.get("sqft", 2000)
        bedrooms = parameters.get("bedrooms", 3)
        bathrooms = parameters.get("bathrooms", 2)
        year_built = parameters.get("year_built", 1990)
        
        # Sample data structure for market valuation
        return {
            "property_id": property_id,
            "estimated_value": 925000,
            "value_range": {
                "low": 875000,
                "high": 975000
            },
            "comparable_properties": [
                {"id": "prop-123", "price": 910000, "similarity": 0.94},
                {"id": "prop-456", "price": 945000, "similarity": 0.89},
                {"id": "prop-789", "price": 895000, "similarity": 0.86}
            ],
            "valuation_factors": {
                "location": 0.4,
                "size": 0.25,
                "condition": 0.2,
                "amenities": 0.15
            },
            "confidence_score": 0.87,
            "sample_size": 12
        }
    
    async def _process_price_per_sqft(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process price per square foot analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulated processing time
        await asyncio.sleep(1.5)
        
        # Get zip_code from parameters
        zip_code = parameters.get("zip_code", "90210")
        
        # Sample data structure for price per square foot analysis
        return {
            "zip_code": zip_code,
            "price_per_sqft": 425,
            "comparison": {
                "county_average": 380,
                "percentile": 68
            },
            "breakdown_by_property_type": {
                "single_family": 450,
                "condo": 380,
                "multi_family": 320
            },
            "historical_trend": [
                {"year": 2022, "price_per_sqft": 390},
                {"year": 2023, "price_per_sqft": 405},
                {"year": 2024, "price_per_sqft": 425}
            ],
            "sample_size": 95
        }