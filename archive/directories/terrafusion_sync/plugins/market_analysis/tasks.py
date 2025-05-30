"""
TerraFusion SyncService - Market Analysis Plugin - Background Tasks

This module provides background task workers for the Market Analysis plugin.
It processes analysis jobs asynchronously to avoid blocking API requests.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union

# Prevent circular imports via lazy loading
from sqlalchemy.ext.asyncio import AsyncSession

# Configure logging
logger = logging.getLogger(__name__)

# --- Analysis Functions ---

async def analyze_price_trend_by_zip(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze price trends by ZIP code.
    
    Args:
        parameters: Dictionary containing analysis parameters
            - zip_code: ZIP code to analyze
            - date_from: Start date for analysis (ISO format)
            - date_to: End date for analysis (ISO format)
            - property_type: Type of property to analyze (optional)
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Running price trend analysis for ZIP: {parameters.get('zip_code')}")
    
    # Simulate processing time
    processing_time = random.uniform(1.5, 3.0)
    await asyncio.sleep(processing_time)
    
    # Get parameters with defaults
    zip_code = parameters.get('zip_code', '12345')
    date_from = parameters.get('date_from', (datetime.now() - timedelta(days=365)).isoformat())
    date_to = parameters.get('date_to', datetime.now().isoformat())
    property_type = parameters.get('property_type', 'residential')
    
    # Generate sample trend data - in production this would use actual data
    num_points = random.randint(8, 12)
    
    # Generate trend data
    start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00') if date_from.endswith('Z') else date_from)
    end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00') if date_to.endswith('Z') else date_to)
    date_range = (end_date - start_date).days
    
    # Value ranges based on property type
    if property_type == 'residential':
        base_price = random.uniform(200000, 350000)
        trend_slope = random.uniform(0.05, 0.15)  # 5-15% annual growth
    elif property_type == 'commercial':
        base_price = random.uniform(500000, 1500000)
        trend_slope = random.uniform(0.03, 0.08)  # 3-8% annual growth
    else:
        base_price = random.uniform(150000, 250000)
        trend_slope = random.uniform(0.04, 0.12)  # 4-12% annual growth
    
    # Generate trend points
    trend_points = []
    for i in range(num_points):
        point_date = start_date + timedelta(days=(date_range / (num_points - 1)) * i)
        progress_factor = i / (num_points - 1)  # 0 to 1
        
        # Apply trend with some randomness
        price = base_price * (1 + trend_slope * progress_factor + random.uniform(-0.02, 0.02))
        
        trend_points.append({
            "date": point_date.isoformat(),
            "value": round(price, 2),
            "year_month": point_date.strftime("%Y-%m")
        })
    
    # Calculate summary metrics
    prices = [point["value"] for point in trend_points]
    avg_price = sum(prices) / len(prices)
    median_price = sorted(prices)[len(prices) // 2]
    price_change = prices[-1] - prices[0]
    price_change_pct = (price_change / prices[0]) * 100 if prices[0] > 0 else 0
    
    return {
        "zip_code": zip_code,
        "property_type": property_type,
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "average_price": round(avg_price, 2),
        "median_price": round(median_price, 2),
        "price_change": round(price_change, 2),
        "price_change_percentage": round(price_change_pct, 2),
        "trends": trend_points
    }

async def analyze_comparable_market_area(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find and analyze comparable market areas.
    
    Args:
        parameters: Dictionary containing analysis parameters
            - zip_code: Primary ZIP code for comparison
            - radius_miles: Search radius in miles (default: 25)
            - min_similar_listings: Minimum similar listings required (default: 10)
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Running comparable market area analysis for: {parameters.get('zip_code')}")
    
    # Simulate processing time
    processing_time = random.uniform(2.0, 5.0)
    await asyncio.sleep(processing_time)
    
    # Get parameters with defaults
    zip_code = parameters.get('zip_code', '12345')
    radius_miles = parameters.get('radius_miles', 25)
    min_similar = parameters.get('min_similar_listings', 10)
    
    # Generate sample comparable zip codes
    num_comps = random.randint(3, 6)
    base_zip = int(zip_code)
    
    comparable_areas = []
    for i in range(num_comps):
        # Generate similar but different ZIP
        new_zip = str(base_zip + random.randint(-100, 100)).zfill(5)
        
        # Skip if we accidentally generated the same ZIP
        if new_zip == zip_code:
            continue
            
        # Generate comparable stats
        similarity_score = random.uniform(0.65, 0.95)
        distance_miles = random.uniform(5, radius_miles)
        median_price = random.uniform(180000, 450000)
        price_per_sqft = random.uniform(100, 350)
        
        comparable_areas.append({
            "zip_code": new_zip,
            "similarity_score": round(similarity_score, 2),
            "distance_miles": round(distance_miles, 1),
            "median_price": round(median_price, 2),
            "price_per_sqft": round(price_per_sqft, 2)
        })
    
    # Sort by similarity score (descending)
    comparable_areas.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return {
        "primary_zip": zip_code,
        "search_radius_miles": radius_miles,
        "min_similar_listings": min_similar,
        "comparable_areas": comparable_areas,
        "total_comparable_areas_found": len(comparable_areas)
    }

async def analyze_sales_velocity(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze sales velocity metrics.
    
    Args:
        parameters: Dictionary containing analysis parameters
            - zip_code: ZIP code to analyze
            - property_type: Type of property
            - date_from: Start date for analysis
            - date_to: End date for analysis
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Running sales velocity analysis for: {parameters.get('zip_code')}")
    
    # Simulate processing time
    processing_time = random.uniform(1.0, 3.5)
    await asyncio.sleep(processing_time)
    
    # Get parameters with defaults
    zip_code = parameters.get('zip_code', '12345')
    property_type = parameters.get('property_type', 'residential')
    date_from = parameters.get('date_from', (datetime.now() - timedelta(days=180)).isoformat())
    date_to = parameters.get('date_to', datetime.now().isoformat())
    
    # Generate sample metrics
    avg_days_on_market = random.randint(20, 120)
    total_listings = random.randint(50, 300)
    new_listings_per_month = random.randint(5, 30)
    sold_listings = random.randint(int(total_listings * 0.3), int(total_listings * 0.8))
    
    # Calculate sales rate
    start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00') if date_from.endswith('Z') else date_from)
    end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00') if date_to.endswith('Z') else date_to)
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    months_diff = max(1, months_diff)  # Ensure at least 1 month
    
    sales_per_month = sold_listings / months_diff
    absorption_rate = (sold_listings / total_listings) * 100 if total_listings > 0 else 0
    months_of_inventory = total_listings / sales_per_month if sales_per_month > 0 else 0
    
    # Generate monthly trends
    monthly_trends = []
    current_date = start_date
    while current_date <= end_date:
        month_sales = int(sales_per_month * random.uniform(0.7, 1.3))  # Add variability
        month_dom = avg_days_on_market + random.randint(-10, 10)
        
        monthly_trends.append({
            "year_month": current_date.strftime("%Y-%m"),
            "new_listings": int(new_listings_per_month * random.uniform(0.8, 1.2)),
            "sales": month_sales,
            "avg_days_on_market": max(7, month_dom)  # Ensure positive value
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return {
        "zip_code": zip_code,
        "property_type": property_type,
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "average_days_on_market": avg_days_on_market,
        "total_listings": total_listings,
        "sold_listings": sold_listings,
        "sales_per_month": round(sales_per_month, 1),
        "absorption_rate_percentage": round(absorption_rate, 1),
        "months_of_inventory": round(months_of_inventory, 1),
        "trends": monthly_trends
    }

async def analyze_market_valuation(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform market valuation analysis.
    
    Args:
        parameters: Dictionary containing analysis parameters
            - zip_code: ZIP code area
            - property_id: Specific property to analyze (optional)
            - beds: Number of bedrooms (optional)
            - baths: Number of bathrooms (optional)
            - sqft: Square footage (optional)
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Running market valuation analysis for: {parameters.get('zip_code')}")
    
    # Simulate processing time
    processing_time = random.uniform(2.5, 6.0)
    await asyncio.sleep(processing_time)
    
    # Get parameters with defaults
    zip_code = parameters.get('zip_code', '12345')
    property_id = parameters.get('property_id')
    beds = parameters.get('beds', 3)
    baths = parameters.get('baths', 2)
    sqft = parameters.get('sqft', 1800)
    
    # Generate sample valuation data
    estimated_value = sqft * random.uniform(150, 350)
    confidence_score = random.uniform(0.70, 0.95)
    
    # Value range
    low_range = estimated_value * random.uniform(0.85, 0.95)
    high_range = estimated_value * random.uniform(1.05, 1.15)
    
    # Comparables
    num_comps = random.randint(3, 8)
    comps = []
    
    # Generate comparable properties
    for i in range(num_comps):
        comp_id = f"PROP-{random.randint(1000, 9999)}"
        comp_beds = beds + random.randint(-1, 1)
        comp_baths = baths + random.randint(-1, 1) * 0.5
        comp_sqft = sqft * random.uniform(0.8, 1.2)
        
        # Ensure minimum sensible values
        comp_beds = max(1, comp_beds)
        comp_baths = max(1, comp_baths)
        comp_sqft = max(500, comp_sqft)
        
        comp_price = comp_sqft * random.uniform(140, 360)
        comp_price_per_sqft = comp_price / comp_sqft
        comp_distance_miles = random.uniform(0.1, 3.0)
        
        comps.append({
            "property_id": comp_id,
            "beds": comp_beds,
            "baths": comp_baths,
            "sqft": int(comp_sqft),
            "sale_price": round(comp_price, 2),
            "price_per_sqft": round(comp_price_per_sqft, 2),
            "distance_miles": round(comp_distance_miles, 2),
            "sale_date": (datetime.now() - timedelta(days=random.randint(5, 120))).isoformat()
        })
    
    # Sort comps by distance
    comps.sort(key=lambda x: x["distance_miles"])
    
    return {
        "zip_code": zip_code,
        "property_id": property_id,
        "property_details": {
            "beds": beds,
            "baths": baths,
            "sqft": sqft
        },
        "estimated_value": round(estimated_value, 2),
        "value_range": {
            "low": round(low_range, 2),
            "high": round(high_range, 2)
        },
        "price_per_sqft": round(estimated_value / sqft, 2),
        "confidence_score": round(confidence_score, 2),
        "comparable_properties": comps
    }

async def analyze_price_per_sqft(parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze price per square foot metrics.
    
    Args:
        parameters: Dictionary containing analysis parameters
            - zip_code: ZIP code to analyze
            - property_type: Type of property
            - date_from: Start date for analysis
            - date_to: End date for analysis
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Running price per sqft analysis for: {parameters.get('zip_code')}")
    
    # Simulate processing time
    processing_time = random.uniform(1.5, 3.0)
    await asyncio.sleep(processing_time)
    
    # Get parameters with defaults
    zip_code = parameters.get('zip_code', '12345')
    property_type = parameters.get('property_type', 'residential')
    date_from = parameters.get('date_from', (datetime.now() - timedelta(days=365)).isoformat())
    date_to = parameters.get('date_to', datetime.now().isoformat())
    
    # Base price per sqft by property type
    if property_type == 'residential':
        base_ppsf = random.uniform(150, 300)
    elif property_type == 'commercial':
        base_ppsf = random.uniform(200, 500)
    else:
        base_ppsf = random.uniform(100, 200)
    
    # Overall stats
    avg_ppsf = base_ppsf
    median_ppsf = base_ppsf * random.uniform(0.95, 1.05)
    min_ppsf = base_ppsf * random.uniform(0.7, 0.9)
    max_ppsf = base_ppsf * random.uniform(1.1, 1.3)
    
    # Generate breakdown by property size
    size_brackets = [
        {"name": "Small (< 1000 sqft)", "min_sqft": 0, "max_sqft": 1000},
        {"name": "Medium (1000-2000 sqft)", "min_sqft": 1000, "max_sqft": 2000},
        {"name": "Large (2000-3000 sqft)", "min_sqft": 2000, "max_sqft": 3000},
        {"name": "Extra Large (> 3000 sqft)", "min_sqft": 3000, "max_sqft": 10000}
    ]
    
    # Generate ppsf for each bracket
    for bracket in size_brackets:
        # Smaller properties typically have higher ppsf
        if bracket["max_sqft"] <= 1000:
            factor = random.uniform(1.1, 1.25)
        elif bracket["max_sqft"] <= 2000:
            factor = random.uniform(0.95, 1.1)
        elif bracket["max_sqft"] <= 3000:
            factor = random.uniform(0.85, 1.0)
        else:
            factor = random.uniform(0.75, 0.9)
            
        bracket["avg_ppsf"] = round(base_ppsf * factor, 2)
        bracket["sample_count"] = random.randint(10, 50)
    
    # Generate monthly trend
    start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00') if date_from.endswith('Z') else date_from)
    end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00') if date_to.endswith('Z') else date_to)
    
    # Determine number of months
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    months_diff = max(1, months_diff)
    
    # Annual growth rate - randomize between 2-8%
    annual_growth_rate = random.uniform(0.02, 0.08)
    monthly_growth_rate = annual_growth_rate / 12
    
    # Generate trend data
    trend_points = []
    current_date = start_date
    current_ppsf = base_ppsf * random.uniform(0.9, 0.95)  # Start a bit lower
    
    while current_date <= end_date:
        # Add some randomness to the growth
        month_growth = monthly_growth_rate * random.uniform(0.5, 1.5)
        current_ppsf *= (1 + month_growth)
        
        trend_points.append({
            "year_month": current_date.strftime("%Y-%m"),
            "value": round(current_ppsf, 2)
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return {
        "zip_code": zip_code,
        "property_type": property_type,
        "date_range": {
            "from": date_from,
            "to": date_to
        },
        "average_price_per_sqft": round(avg_ppsf, 2),
        "median_price_per_sqft": round(median_ppsf, 2),
        "min_price_per_sqft": round(min_ppsf, 2),
        "max_price_per_sqft": round(max_ppsf, 2),
        "breakdown_by_size": size_brackets,
        "trends": trend_points
    }

# Map of analysis type to function
ANALYSIS_FUNCTIONS = {
    "price_trend_by_zip": analyze_price_trend_by_zip,
    "comparable_market_area": analyze_comparable_market_area,
    "sales_velocity": analyze_sales_velocity,
    "market_valuation": analyze_market_valuation,
    "price_per_sqft": analyze_price_per_sqft
}

# --- Task Runner ---

async def run_analysis_job(
    get_session_factory: Callable[[], AsyncSession],
    job_id: str,
    analysis_type: str,
    county_id: str,
    parameters_json: Union[str, Dict[str, Any]]
):
    """
    Run a market analysis job asynchronously.
    
    Args:
        get_session_factory: Factory function to get a database session
        job_id: ID of the job to run
        analysis_type: Type of analysis to perform
        county_id: County ID
        parameters_json: Analysis parameters as JSON string or dict
    """
    # Load service functions at runtime to avoid circular imports
    from .service import get_analysis_job, update_job_status
    import terrafusion_sync.metrics as metrics
    
    # Convert parameters if needed
    if isinstance(parameters_json, str):
        try:
            parameters = json.loads(parameters_json)
        except Exception as e:
            parameters = {"error": f"Failed to parse parameters JSON: {str(e)}"}
    else:
        parameters = parameters_json or {}
    
    logger.info(f"Starting analysis job {job_id} of type {analysis_type} for county {county_id}")
    
    # Start metrics timer
    start_time = time.time()
    
    # Start measuring task execution
    metrics.MARKET_ANALYSIS_TASK_DURATION.labels(
        analysis_type=analysis_type,
        county_id=county_id
    ).observe(0)  # Initial observation
    
    try:
        async with get_session_factory() as db:
            # Mark job as RUNNING
            logger.info(f"Marking job {job_id} as RUNNING")
            await update_job_status(
                db=db,
                job_id=job_id,
                status="RUNNING",
                message="Analysis in progress",
                started_at=datetime.now()
            )
        
        # Increment running tasks counter
        metrics.MARKET_ANALYSIS_TASKS_RUNNING.labels(
            analysis_type=analysis_type, 
            county_id=county_id
        ).inc()
        
        # Get the appropriate analysis function
        analysis_fn = ANALYSIS_FUNCTIONS.get(analysis_type)
        
        if not analysis_fn:
            logger.error(f"Unknown analysis type: {analysis_type}")
            async with get_session_factory() as db:
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status="FAILED",
                    message=f"Unknown analysis type: {analysis_type}"
                )
                
            # Update failure metric
            metrics.MARKET_ANALYSIS_TASKS_FAILED.labels(
                analysis_type=analysis_type,
                county_id=county_id,
                reason="unknown_type"
            ).inc()
            return
        
        try:
            # Execute the analysis
            logger.info(f"Executing {analysis_type} analysis with parameters: {parameters}")
            result = await analysis_fn(parameters)
            
            # Update job with result
            async with get_session_factory() as db:
                logger.info(f"Marking job {job_id} as COMPLETED")
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status="COMPLETED",
                    message="Analysis completed successfully",
                    completed_at=datetime.now(),
                    result_summary_json=result
                )
            
            # Update success metric
            metrics.MARKET_ANALYSIS_TASKS_COMPLETED.labels(
                analysis_type=analysis_type,
                county_id=county_id
            ).inc()
            
        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {str(e)}", exc_info=True)
            
            # Update job with error
            async with get_session_factory() as db:
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status="FAILED",
                    message=f"Analysis failed: {str(e)}",
                    completed_at=datetime.now()
                )
            
            # Update failure metric
            metrics.MARKET_ANALYSIS_TASKS_FAILED.labels(
                analysis_type=analysis_type,
                county_id=county_id,
                reason="execution_error"
            ).inc()
    
    except Exception as e:
        logger.error(f"Task execution error for job {job_id}: {str(e)}", exc_info=True)
        
        # Try to update job status
        try:
            async with get_session_factory() as db:
                await update_job_status(
                    db=db,
                    job_id=job_id,
                    status="FAILED",
                    message=f"Task execution error: {str(e)}",
                    completed_at=datetime.now()
                )
        except Exception as inner_e:
            logger.error(f"Failed to update job status for {job_id}: {str(inner_e)}")
        
        # Update failure metric
        metrics.MARKET_ANALYSIS_TASKS_FAILED.labels(
            analysis_type=analysis_type,
            county_id=county_id,
            reason="system_error"
        ).inc()
    
    finally:
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Decrement running tasks counter
        metrics.MARKET_ANALYSIS_TASKS_RUNNING.labels(
            analysis_type=analysis_type,
            county_id=county_id
        ).dec()
        
        # Record final task duration
        metrics.MARKET_ANALYSIS_TASK_DURATION.labels(
            analysis_type=analysis_type,
            county_id=county_id
        ).observe(execution_time)
        
        logger.info(f"Analysis job {job_id} completed in {execution_time:.2f} seconds")
