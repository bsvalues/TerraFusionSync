"""
TerraFusion SyncService - Market Analysis Plugin - Schemas

This module provides Pydantic schema models for the Market Analysis plugin.
These schemas define the structure of request and response objects for the API.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class AnalysisType(str, Enum):
    """Types of market analysis that can be performed."""
    PRICE_TREND_BY_ZIP = "price_trend_by_zip"
    COMPARABLE_MARKET_AREA = "comparable_market_area"
    SALES_VELOCITY = "sales_velocity"
    MARKET_VALUATION = "market_valuation"
    PRICE_PER_SQFT = "price_per_sqft"


class JobStatus(str, Enum):
    """Possible statuses for a market analysis job."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class MarketTrendDataPoint(BaseModel):
    """Data point for market trend data."""
    date: Optional[str] = None
    year_month: Optional[str] = None
    value: float


class PricingDataPoint(BaseModel):
    """Data point for pricing trends."""
    date: str
    value: float
    year_month: Optional[str] = None


class SalesVelocityDataPoint(BaseModel):
    """Data point for sales velocity trends."""
    year_month: str
    new_listings: int
    sales: int
    avg_days_on_market: int


class ComparableArea(BaseModel):
    """Comparable market area information."""
    zip_code: str
    similarity_score: float
    distance_miles: float
    median_price: float
    price_per_sqft: float


class PropertyDetails(BaseModel):
    """Details about a specific property."""
    beds: int
    baths: float
    sqft: int


class ComparableProperty(BaseModel):
    """Comparable property information."""
    property_id: str
    beds: int
    baths: float
    sqft: int
    sale_price: float
    price_per_sqft: float
    distance_miles: float
    sale_date: str


class PropertyValueRange(BaseModel):
    """Value range for a property."""
    low: float
    high: float


class SizeBracket(BaseModel):
    """Price per sqft data for a specific size bracket."""
    name: str
    min_sqft: int
    max_sqft: int
    avg_ppsf: float
    sample_count: int


class MarketAnalysisRunRequest(BaseModel):
    """Request to run a market analysis job."""
    county_id: str = Field(..., description="County ID for the analysis")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(
        ..., 
        description="Parameters for the analysis, varies by analysis type"
    )


class MarketAnalysisJobStatusResponse(BaseModel):
    """Response with job status information."""
    job_id: str
    county_id: str
    analysis_type: str
    status: str
    message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MarketAnalysisResultData(BaseModel):
    """Result data from a completed market analysis job."""
    result_summary: Optional[Dict[str, Any]] = None
    result_data_location: Optional[str] = None
    trends: Optional[List[Dict[str, Any]]] = None


class MarketAnalysisJobResultResponse(MarketAnalysisJobStatusResponse):
    """
    Response with job status and result data for a completed analysis job.
    Extends MarketAnalysisJobStatusResponse with result data.
    """
    result: Optional[MarketAnalysisResultData] = None


class PriceTrendResponse(BaseModel):
    """Response for price trend analysis."""
    zip_code: str
    property_type: str
    date_range: Dict[str, str]
    average_price: float
    median_price: float
    price_change: float
    price_change_percentage: float
    trends: List[PricingDataPoint]


class ComparableMarketAreaResponse(BaseModel):
    """Response for comparable market area analysis."""
    primary_zip: str
    search_radius_miles: float
    min_similar_listings: int
    comparable_areas: List[ComparableArea]
    total_comparable_areas_found: int


class SalesVelocityResponse(BaseModel):
    """Response for sales velocity analysis."""
    zip_code: str
    property_type: str
    date_range: Dict[str, str]
    average_days_on_market: int
    total_listings: int
    sold_listings: int
    sales_per_month: float
    absorption_rate_percentage: float
    months_of_inventory: float
    trends: List[SalesVelocityDataPoint]


class MarketValuationResponse(BaseModel):
    """Response for market valuation analysis."""
    zip_code: str
    property_id: Optional[str]
    property_details: PropertyDetails
    estimated_value: float
    value_range: PropertyValueRange
    price_per_sqft: float
    confidence_score: float
    comparable_properties: List[ComparableProperty]


class PricePerSqftResponse(BaseModel):
    """Response for price per square foot analysis."""
    zip_code: str
    property_type: str
    date_range: Dict[str, str]
    average_price_per_sqft: float
    median_price_per_sqft: float
    min_price_per_sqft: float
    max_price_per_sqft: float
    breakdown_by_size: List[SizeBracket]
    trends: List[PricingDataPoint]