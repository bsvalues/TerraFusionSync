"""
Fix Market Analysis Background Task

This script addresses the background task implementation in the
Market Analysis plugin to resolve any circular dependencies.
"""

import os
import importlib
import inspect
import sys

# Path to the tasks.py file
TASKS_PATH = "terrafusion_sync/plugins/market_analysis/tasks.py"

# Check if the file exists
if not os.path.exists(TASKS_PATH):
    print(f"Error: Could not find {TASKS_PATH}")
    sys.exit(1)

# Create a backup
backup_path = f"{TASKS_PATH}.bak"
with open(TASKS_PATH, "r") as f:
    original_content = f.read()

with open(backup_path, "w") as f:
    f.write(original_content)
    print(f"Created backup at {backup_path}")

# Define the new content with circular dependency fixes
tasks_content = """\"\"\"
TerraFusion SyncService - Market Analysis Plugin - Background Tasks

This module provides background task functions for asynchronous 
processing of market analysis jobs.
\"\"\"

import logging
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Awaitable
import uuid

# Core imports
from terrafusion_sync.database import get_db_session
from terrafusion_sync.core_models import MarketAnalysisJob

# Import metrics module directly
import terrafusion_sync.metrics as core_metrics

# Setup logging
logger = logging.getLogger(__name__)

async def run_analysis_job(
    get_session_factory: Callable[[], Awaitable],
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters: Dict[str, Any]
):
    \"\"\"
    Run a market analysis job asynchronously.
    
    Args:
        get_session_factory: Function that returns a database session
        job_id: ID of the job to process
        analysis_type: Type of analysis to perform (e.g., 'price_trend_by_zip')
        county_id: County identifier
        parameters: Parameters for the analysis
    \"\"\"
    # Get the session factory
    try:
        # Import service functions here to avoid circular imports
        from .service import update_job_status, get_analysis_job
        
        logger.info(f"Starting market analysis job {job_id} of type {analysis_type}")
        
        # Increment in-progress counter
        core_metrics.MARKET_ANALYSIS_JOBS_IN_PROGRESS.labels(
            county_id=county_id,
            analysis_type=analysis_type
        ).inc()
        
        # Get DB session
        async with get_session_factory() as session:
            # Update job status to IN_PROGRESS
            await update_job_status(
                db=session,
                job_id=job_id,
                status="IN_PROGRESS",
                message="Analysis job started",
                started_at=datetime.now()
            )
        
        # Record job start time for duration tracking
        start_time = time.time()
        
        # Process job based on analysis type
        try:
            # Get the result based on analysis type
            result = await process_analysis_by_type(
                job_id=job_id,
                analysis_type=analysis_type,
                county_id=county_id,
                parameters=parameters,
                get_session_factory=get_session_factory
            )
            
            # Calculate processing duration
            duration = time.time() - start_time
            
            # Record successful completion metrics
            core_metrics.MARKET_ANALYSIS_JOBS_COMPLETED.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).inc()
            
            core_metrics.MARKET_ANALYSIS_PROCESSING_DURATION.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).observe(duration)
            
            # Update job with results
            async with get_session_factory() as session:
                await update_job_status(
                    db=session,
                    job_id=job_id,
                    status="COMPLETED",
                    message="Analysis completed successfully",
                    completed_at=datetime.now(),
                    result_summary_json=result.get("summary"),
                    result_data_location=result.get("data_location")
                )
                
            logger.info(f"Market analysis job {job_id} completed successfully in {duration:.2f}s")
            
        except Exception as e:
            # Log the exception
            logger.error(f"Error processing market analysis job {job_id}: {str(e)}", exc_info=True)
            
            # Record failure metrics
            core_metrics.MARKET_ANALYSIS_JOBS_FAILED.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).inc()
            
            # Update job with error information
            try:
                async with get_session_factory() as session:
                    await update_job_status(
                        db=session,
                        job_id=job_id,
                        status="FAILED",
                        message=f"Analysis failed: {str(e)}",
                        completed_at=datetime.now()
                    )
            except Exception as update_error:
                logger.error(f"Failed to update job status for {job_id}: {str(update_error)}")
        
        finally:
            # Decrement in-progress counter
            core_metrics.MARKET_ANALYSIS_JOBS_IN_PROGRESS.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).dec()
            
    except Exception as e:
        logger.error(f"Unhandled exception in run_analysis_job for job {job_id}: {str(e)}", exc_info=True)
        # Ensure metrics are decremented even on unexpected errors
        try:
            core_metrics.MARKET_ANALYSIS_JOBS_IN_PROGRESS.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).dec()
            
            core_metrics.MARKET_ANALYSIS_JOBS_FAILED.labels(
                county_id=county_id,
                analysis_type=analysis_type
            ).inc()
        except Exception:
            pass

async def process_analysis_by_type(
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters: Dict[str, Any],
    get_session_factory: Callable[[], Awaitable]
) -> Dict[str, Any]:
    \"\"\"
    Process a market analysis job based on its type.
    
    Args:
        job_id: ID of the job to process
        analysis_type: Type of analysis to perform
        county_id: County identifier
        parameters: Parameters for the analysis
        get_session_factory: Function that returns a database session
        
    Returns:
        Dictionary with analysis results
    \"\"\"
    # Import analysis functions here to avoid circular imports
    from .service import get_metrics_data
    from .metrics import update_property_price_metrics, update_market_score
    
    # Default response structure
    result = {
        "summary": {
            "job_id": job_id,
            "analysis_type": analysis_type,
            "county_id": county_id,
            "processed_at": datetime.now().isoformat(),
            "trends": []
        },
        "data_location": None
    }
    
    # Different processing based on analysis type
    if analysis_type == "price_trend_by_zip":
        # Process price trends by ZIP code
        zip_code = parameters.get("zip_code")
        time_period = parameters.get("time_period", "1y")
        
        logger.info(f"Processing price trend analysis for ZIP {zip_code} over {time_period}")
        
        # Get metrics data for processing
        metrics_data = await get_metrics_data(county_id, "property_prices", time_period)
        
        # Process the data (simulated)
        await asyncio.sleep(2)  # Simulate processing time
        
        # Update metrics for future queries
        await update_property_price_metrics(zip_code, metrics_data)
        
        # Add trends to result
        result["summary"]["zip_code"] = zip_code
        result["summary"]["time_period"] = time_period
        result["summary"]["avg_price"] = 450000
        result["summary"]["price_change_pct"] = 5.2
        result["summary"]["n_properties"] = 120
        
        # Add trend points (simulated data)
        result["summary"]["trends"] = [
            {"date": "2024-01", "value": 430000},
            {"date": "2024-02", "value": 435000},
            {"date": "2024-03", "value": 442000},
            {"date": "2024-04", "value": 448000},
            {"date": "2024-05", "value": 450000}
        ]
        
    elif analysis_type == "comparable_market_area":
        # Process comparable market areas
        property_id = parameters.get("property_id")
        radius_miles = parameters.get("radius_miles", 5)
        
        logger.info(f"Processing comparable market area for property {property_id}")
        
        # Simulate processing
        await asyncio.sleep(3)
        
        # Add results
        result["summary"]["property_id"] = property_id
        result["summary"]["radius_miles"] = radius_miles
        result["summary"]["n_comparables"] = 15
        result["summary"]["avg_comparable_price"] = 425000
        result["summary"]["market_liquidity_score"] = 7.2
        
    elif analysis_type == "sales_velocity":
        # Process sales velocity metrics
        area_code = parameters.get("area_code")
        period_months = parameters.get("period_months", 6)
        
        logger.info(f"Processing sales velocity for area {area_code}")
        
        # Simulate processing
        await asyncio.sleep(2.5)
        
        # Update market score metrics
        await update_market_score(area_code, 8.3)
        
        # Add results
        result["summary"]["area_code"] = area_code
        result["summary"]["period_months"] = period_months
        result["summary"]["avg_days_on_market"] = 22
        result["summary"]["demand_supply_ratio"] = 1.3
        result["summary"]["market_score"] = 8.3
        
        # Add trend points
        result["summary"]["trends"] = [
            {"date": "2024-01", "value": 8.1},
            {"date": "2024-02", "value": 8.0},
            {"date": "2024-03", "value": 8.2},
            {"date": "2024-04", "value": 8.4},
            {"date": "2024-05", "value": 8.3}
        ]
        
    elif analysis_type == "market_valuation":
        # Process market valuation
        property_type = parameters.get("property_type", "residential")
        region_id = parameters.get("region_id")
        
        logger.info(f"Processing market valuation for {property_type} in region {region_id}")
        
        # Simulate processing
        await asyncio.sleep(4)
        
        # Add results
        result["summary"]["property_type"] = property_type
        result["summary"]["region_id"] = region_id
        result["summary"]["valuation_confidence"] = 0.89
        result["summary"]["market_trend"] = "appreciating"
        result["summary"]["forecast_change_6m"] = 3.1
        
    elif analysis_type == "price_per_sqft":
        # Process price per square foot analysis
        property_type = parameters.get("property_type", "all")
        area_ids = parameters.get("area_ids", [])
        
        logger.info(f"Processing price per sqft for {property_type} in {len(area_ids)} areas")
        
        # Simulate processing
        await asyncio.sleep(2)
        
        # Add results
        result["summary"]["property_type"] = property_type
        result["summary"]["area_count"] = len(area_ids)
        result["summary"]["avg_price_sqft"] = 275
        result["summary"]["min_price_sqft"] = 190
        result["summary"]["max_price_sqft"] = 350
        
    else:
        # Unknown analysis type
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    return result
"""

# Write the updated file
with open(TASKS_PATH, "w") as f:
    f.write(tasks_content)

print(f"Successfully updated {TASKS_PATH} to fix circular dependencies")
print("Restart the syncservice workflow to apply changes.")