"""
TerraFusion SyncService - Market Analysis Plugin - Service

This module provides the core business logic for the Market Analysis plugin.
It handles job management, data processing, and result generation.
"""

import json
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, update, and_, or_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from terrafusion_sync.core_models import MarketAnalysisJob
from terrafusion_sync.plugins.market_analysis.metrics import (
    record_job_submission,
    record_job_completion,
    record_job_failure,
    update_running_jobs,
    record_job_processing_time,
    record_property_valuation,
    record_price_per_sqft,
    record_comparable_areas_count,
    record_sales_velocity,
    record_days_on_market,
    update_property_price_metrics,
    update_market_score
)

logger = logging.getLogger(__name__)

# Constants for job status
JOB_STATUS_PENDING = "PENDING"
JOB_STATUS_RUNNING = "RUNNING"
JOB_STATUS_COMPLETED = "COMPLETED"
JOB_STATUS_FAILED = "FAILED"
JOB_STATUS_CANCELLED = "CANCELLED"

# Constants for analysis types
ANALYSIS_TYPE_PRICE_TREND = "price_trend_by_zip"
ANALYSIS_TYPE_COMPARABLE_MARKET = "comparable_market_area"
ANALYSIS_TYPE_SALES_VELOCITY = "sales_velocity"
ANALYSIS_TYPE_MARKET_VALUATION = "market_valuation"
ANALYSIS_TYPE_PRICE_PER_SQFT = "price_per_sqft"

# Storage for background tasks
_running_tasks = {}


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
        self.get_session_factory = get_session_factory
        logger.info("Market Analysis Service initialized")

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
        
        # Record metric
        record_job_submission(county_id, analysis_type)
        
        # Create job record
        job = MarketAnalysisJob(
            job_id=job_id,
            county_id=county_id,
            analysis_type=analysis_type,
            status=JOB_STATUS_PENDING,
            parameters_json=json.dumps(parameters),
            created_at=now,
            updated_at=now,
            message="Job created and pending execution"
        )
        
        # Save to database
        async with self.get_session_factory() as session:
            session.add(job)
            await session.commit()
            
        logger.info(f"Created market analysis job {job_id} for county {county_id}, type: {analysis_type}")
        
        # Start background processing after job is saved
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
        async with self.get_session_factory() as session:
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
        async with self.get_session_factory() as session:
            job = await self._get_job(session, job_id)
            
            if not job:
                return None
                
            # Convert to dict with enhanced result handling
            result = self._job_to_dict(job)
            
            # Add result data if available
            if job.status == JOB_STATUS_COMPLETED:
                try:
                    result_summary = json.loads(job.result_summary_json) if job.result_summary_json else None
                    
                    result["result"] = {
                        "result_summary": result_summary,
                        "result_data_location": job.result_data_location
                    }
                    
                    # Check if we have trend data
                    if result_summary and "trends" in result_summary:
                        result["result"]["trends"] = result_summary["trends"]
                        
                except Exception as e:
                    logger.error(f"Error processing result data for job {job_id}: {str(e)}")
                    result["result"] = {
                        "result_summary": None,
                        "result_data_location": job.result_data_location
                    }
            
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
        async with self.get_session_factory() as session:
            query = select(MarketAnalysisJob).order_by(desc(MarketAnalysisJob.created_at)).limit(limit)
            
            if county_id:
                query = query.where(MarketAnalysisJob.county_id == county_id)
                
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
        async with self.get_session_factory() as session:
            job = await self._get_job(session, job_id)
            
            if not job:
                return False
                
            if job.status in [JOB_STATUS_PENDING, JOB_STATUS_RUNNING]:
                # Update job status
                job.status = JOB_STATUS_CANCELLED
                job.message = "Job cancelled by user"
                job.updated_at = datetime.utcnow()
                
                # Commit changes
                await session.commit()
                
                # Stop background task if running
                task = _running_tasks.get(job_id)
                if task and not task.done():
                    task.cancel()
                    
                logger.info(f"Cancelled job {job_id}")
                return True
                
            return False
    
    async def cleanup_stale_jobs(self, max_age_hours: int = 24) -> int:
        """
        Update status of jobs that have been stuck in RUNNING state.
        
        Args:
            max_age_hours: Maximum age in hours for a running job before it's considered stale
            
        Returns:
            int: Number of jobs updated
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        async with self.get_session_factory() as session:
            # Find running jobs that haven't been updated recently
            query = (
                update(MarketAnalysisJob)
                .where(
                    and_(
                        MarketAnalysisJob.status == JOB_STATUS_RUNNING,
                        MarketAnalysisJob.updated_at < cutoff_time
                    )
                )
                .values(
                    status=JOB_STATUS_FAILED,
                    message=f"Job timed out after {max_age_hours} hours",
                    updated_at=datetime.utcnow()
                )
            )
            
            result = await session.execute(query)
            await session.commit()
            
            updated_count = result.rowcount
            if updated_count > 0:
                logger.info(f"Cleaned up {updated_count} stale jobs")
                
            return updated_count

    async def _process_job_async(self, job_id: str) -> None:
        """
        Process a job asynchronously in the background.
        
        This method is designed to be run as a background task.
        
        Args:
            job_id: ID of the job to process
        """
        start_time = datetime.utcnow()
        
        async with self.get_session_factory() as session:
            # Get the job
            job = await self._get_job(session, job_id)
            
            if not job:
                logger.error(f"Job {job_id} not found for processing")
                return
                
            # Update job status to RUNNING
            job.status = JOB_STATUS_RUNNING
            job.message = "Job is being processed"
            job.started_at = start_time
            job.updated_at = start_time
            await session.commit()
            
            # Store task reference
            _running_tasks[job_id] = asyncio.current_task()
            
            # Get parameters
            try:
                parameters = json.loads(job.parameters_json) if job.parameters_json else {}
            except json.JSONDecodeError:
                parameters = {}

            # Update running job count for metrics
            update_running_jobs(job.county_id, job.analysis_type, 1)
            
            try:
                # Process based on analysis type
                if job.analysis_type == ANALYSIS_TYPE_PRICE_TREND:
                    result = await self._process_price_trend(job.county_id, parameters)
                elif job.analysis_type == ANALYSIS_TYPE_COMPARABLE_MARKET:
                    result = await self._process_comparable_market(job.county_id, parameters)
                elif job.analysis_type == ANALYSIS_TYPE_SALES_VELOCITY:
                    result = await self._process_sales_velocity(job.county_id, parameters)
                elif job.analysis_type == ANALYSIS_TYPE_MARKET_VALUATION:
                    result = await self._process_market_valuation(job.county_id, parameters)
                elif job.analysis_type == ANALYSIS_TYPE_PRICE_PER_SQFT:
                    result = await self._process_price_per_sqft(job.county_id, parameters)
                else:
                    raise ValueError(f"Unknown analysis type: {job.analysis_type}")
                
                # Update job with results
                job.status = JOB_STATUS_COMPLETED
                job.message = "Job completed successfully"
                job.result_summary_json = json.dumps(result["summary"])
                job.result_data_location = result.get("data_location", "")
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                
                # Record success metric
                record_job_completion(job.county_id, job.analysis_type)
                
            except Exception as e:
                # Log the error
                error_message = f"Error processing job: {str(e)}"
                logger.exception(error_message)
                
                # Update job with error
                job.status = JOB_STATUS_FAILED
                job.message = error_message
                job.completed_at = datetime.utcnow()
                job.updated_at = datetime.utcnow()
                
                # Record failure metric
                record_job_failure(job.county_id, job.analysis_type, "processing_error")
            
            finally:
                # Update metrics for running jobs
                update_running_jobs(job.county_id, job.analysis_type, 0)
                
                # Calculate and record processing time
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                record_job_processing_time(job.county_id, job.analysis_type, processing_time)
                
                # Commit changes and remove task reference
                await session.commit()
                _running_tasks.pop(job_id, None)
                
                logger.info(f"Completed processing job {job_id} with status {job.status}")

    async def _get_job(self, session: AsyncSession, job_id: str) -> Optional[MarketAnalysisJob]:
        """
        Get a job by ID.
        
        Args:
            session: Database session
            job_id: ID of the job to get
            
        Returns:
            MarketAnalysisJob or None: Job if found, None otherwise
        """
        result = await session.execute(
            select(MarketAnalysisJob).where(MarketAnalysisJob.job_id == job_id)
        )
        return result.scalars().first()
    
    def _job_to_dict(self, job: MarketAnalysisJob) -> Dict[str, Any]:
        """
        Convert a job model to a dictionary representation.
        
        Args:
            job: Job model to convert
            
        Returns:
            dict: Dictionary representation of the job
        """
        # Helper function to serialize datetime
        def serialize_datetime(dt):
            return dt.isoformat() if dt else None
            
        # Try to parse parameters from JSON
        try:
            parameters = json.loads(job.parameters_json) if job.parameters_json else None
        except json.JSONDecodeError:
            parameters = None
            
        return {
            "job_id": job.job_id,
            "county_id": job.county_id,
            "analysis_type": job.analysis_type,
            "status": job.status,
            "message": job.message,
            "parameters": parameters,
            "created_at": serialize_datetime(job.created_at),
            "updated_at": serialize_datetime(job.updated_at),
            "started_at": serialize_datetime(job.started_at),
            "completed_at": serialize_datetime(job.completed_at)
        }
        
    # === Analysis Processing Methods ===
    
    async def _process_price_trend(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process price trend analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Extract parameters
        zip_code = parameters.get("zip_code", "00000")
        property_type = parameters.get("property_type", "residential")
        
        # Generate sample data (in production this would query the database)
        trends = []
        base_price = 450000  # Base price in dollars
        
        # Generate 12 months of trend data
        for i in range(12):
            month = datetime.now() - timedelta(days=30 * (11 - i))
            # Add some random variation to create a trend
            price = base_price * (1 + (i * 0.01)) 
            
            trends.append({
                "date": month.strftime("%Y-%m-%d"),
                "year_month": month.strftime("%Y-%m"),
                "value": price
            })
            
        # Calculate summary metrics
        avg_price = sum(t["value"] for t in trends) / len(trends)
        start_price = trends[0]["value"]
        end_price = trends[-1]["value"]
        price_change = end_price - start_price
        price_change_pct = (price_change / start_price) * 100
        
        # Record metrics
        record_property_valuation(county_id, property_type, avg_price)
        
        # Prepare result
        result = {
            "summary": {
                "zip_code": zip_code,
                "property_type": property_type,
                "date_range": {
                    "from": trends[0]["date"],
                    "to": trends[-1]["date"]
                },
                "average_price": avg_price,
                "median_price": trends[len(trends) // 2]["value"],
                "price_change": price_change,
                "price_change_percentage": price_change_pct,
                "trends": trends
            }
        }
        
        return result
        
    async def _process_comparable_market(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process comparable market area analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Extract parameters
        zip_code = parameters.get("zip_code", "00000")
        radius_miles = parameters.get("radius_miles", 25)
        min_similar = parameters.get("min_similar_listings", 5)
        
        # Generate sample comparable areas
        comparable_areas = []
        
        # Sample zip codes near the given one
        sample_zips = [
            f"{int(zip_code) + i}" for i in range(1, 6)
        ]
        
        for i, sample_zip in enumerate(sample_zips):
            # Create a comparable area with sample data
            comparable_areas.append({
                "zip_code": sample_zip,
                "similarity_score": 0.95 - (i * 0.05),
                "distance_miles": (i + 1) * 5,
                "median_price": 450000 - (i * 15000),
                "price_per_sqft": 275 - (i * 10)
            })
            
        # Record metrics
        record_comparable_areas_count(county_id, zip_code, len(comparable_areas))
        
        # Prepare result
        result = {
            "summary": {
                "primary_zip": zip_code,
                "search_radius_miles": radius_miles,
                "min_similar_listings": min_similar,
                "comparable_areas": comparable_areas,
                "total_comparable_areas_found": len(comparable_areas)
            }
        }
        
        return result
        
    async def _process_sales_velocity(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sales velocity analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Extract parameters
        zip_code = parameters.get("zip_code", "00000")
        property_type = parameters.get("property_type", "residential")
        
        # Generate sample data
        trends = []
        
        # Generate 12 months of trend data
        for i in range(12):
            month = datetime.now() - timedelta(days=30 * (11 - i))
            
            # Seasonal variation with random component
            month_factor = 1.0 + 0.2 * ((month.month % 12) / 12.0)
            
            new_listings = int(50 * month_factor)
            sales = int(40 * month_factor)
            days_on_market = int(45 - (i * 0.5))
            
            trends.append({
                "year_month": month.strftime("%Y-%m"),
                "new_listings": new_listings,
                "sales": sales,
                "avg_days_on_market": days_on_market
            })
            
        # Calculate summary metrics
        total_listings = sum(t["new_listings"] for t in trends)
        total_sales = sum(t["sales"] for t in trends)
        avg_days = sum(t["avg_days_on_market"] for t in trends) / len(trends)
        sales_per_month = total_sales / len(trends)
        absorption_rate = (sales_per_month / total_listings) * 100 if total_listings > 0 else 0
        months_inventory = (total_listings / sales_per_month) if sales_per_month > 0 else 0
        
        # Record metrics
        update_market_score(county_id, zip_code, sales_per_month, avg_days)
        
        # Prepare result
        result = {
            "summary": {
                "zip_code": zip_code,
                "property_type": property_type,
                "date_range": {
                    "from": datetime.now() - timedelta(days=30 * 11),
                    "to": datetime.now()
                },
                "average_days_on_market": avg_days,
                "total_listings": total_listings,
                "sold_listings": total_sales,
                "sales_per_month": sales_per_month,
                "absorption_rate_percentage": absorption_rate,
                "months_of_inventory": months_inventory,
                "trends": trends
            }
        }
        
        return result
        
    async def _process_market_valuation(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process market valuation for a specific property.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulate processing time
        await asyncio.sleep(3)
        
        # Extract parameters
        zip_code = parameters.get("zip_code", "00000")
        property_id = parameters.get("property_id")
        beds = parameters.get("beds", 3)
        baths = parameters.get("baths", 2)
        sqft = parameters.get("sqft", 2000)
        
        # Calculate baseline price and price per square foot
        base_price = 450000
        # Adjust for property attributes
        price_per_sqft = 225
        estimated_value = sqft * price_per_sqft
        
        # Generate comparable properties
        comps = []
        for i in range(5):
            # Create a comparable property with slight variations
            comp_sqft = sqft + ((i - 2) * 200)
            comp_price = comp_sqft * price_per_sqft * (1 + ((i - 2) * 0.03))
            comp_ppsf = comp_price / comp_sqft
            
            comp_date = datetime.now() - timedelta(days=i * 15)
            
            comps.append({
                "property_id": f"PROP-{i+1000}",
                "beds": beds + ((i % 3) - 1),
                "baths": baths + ((i % 3) - 1) * 0.5,
                "sqft": comp_sqft,
                "sale_price": comp_price,
                "price_per_sqft": comp_ppsf,
                "distance_miles": i * 0.5,
                "sale_date": comp_date.strftime("%Y-%m-%d")
            })
            
        # Record metrics
        record_property_valuation(county_id, "residential", estimated_value)
        record_price_per_sqft(county_id, "residential", price_per_sqft)
        
        # Prepare result
        result = {
            "summary": {
                "zip_code": zip_code,
                "property_id": property_id,
                "property_details": {
                    "beds": beds,
                    "baths": baths,
                    "sqft": sqft
                },
                "estimated_value": estimated_value,
                "value_range": {
                    "low": estimated_value * 0.95,
                    "high": estimated_value * 1.05
                },
                "price_per_sqft": price_per_sqft,
                "confidence_score": 0.85,
                "comparable_properties": comps
            }
        }
        
        return result
        
    async def _process_price_per_sqft(self, county_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process price per square foot analysis.
        
        Args:
            county_id: County ID
            parameters: Analysis parameters
            
        Returns:
            dict: Analysis results
        """
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Extract parameters
        zip_code = parameters.get("zip_code", "00000")
        property_type = parameters.get("property_type", "residential")
        
        # Generate sample data
        trends = []
        
        # Base price per square foot
        base_ppsf = 225
        
        # Generate 12 months of trend data
        for i in range(12):
            month = datetime.now() - timedelta(days=30 * (11 - i))
            
            # Add increasing trend
            ppsf = base_ppsf * (1 + (i * 0.015))
            
            trends.append({
                "date": month.strftime("%Y-%m-%d"),
                "year_month": month.strftime("%Y-%m"),
                "value": ppsf
            })
            
        # Generate size brackets
        size_brackets = [
            {
                "name": "Small",
                "min_sqft": 500,
                "max_sqft": 1200,
                "avg_ppsf": base_ppsf * 1.1,
                "sample_count": 25
            },
            {
                "name": "Medium",
                "min_sqft": 1201,
                "max_sqft": 2000,
                "avg_ppsf": base_ppsf,
                "sample_count": 40
            },
            {
                "name": "Large",
                "min_sqft": 2001,
                "max_sqft": 3000,
                "avg_ppsf": base_ppsf * 0.95,
                "sample_count": 30
            },
            {
                "name": "Extra Large",
                "min_sqft": 3001,
                "max_sqft": 5000,
                "avg_ppsf": base_ppsf * 0.9,
                "sample_count": 15
            }
        ]
        
        # Calculate metrics
        avg_ppsf = sum(t["value"] for t in trends) / len(trends)
        ppsfes = [t["value"] for t in trends]
        ppsfes.sort()
        median_ppsf = ppsfes[len(ppsfes) // 2]
        min_ppsf = min(ppsfes)
        max_ppsf = max(ppsfes)
        
        # Record metrics
        record_price_per_sqft(county_id, property_type, avg_ppsf)
        
        # Prepare result
        result = {
            "summary": {
                "zip_code": zip_code,
                "property_type": property_type,
                "date_range": {
                    "from": trends[0]["date"],
                    "to": trends[-1]["date"]
                },
                "average_price_per_sqft": avg_ppsf,
                "median_price_per_sqft": median_ppsf,
                "min_price_per_sqft": min_ppsf,
                "max_price_per_sqft": max_ppsf,
                "breakdown_by_size": size_brackets,
                "trends": trends
            }
        }
        
        return result