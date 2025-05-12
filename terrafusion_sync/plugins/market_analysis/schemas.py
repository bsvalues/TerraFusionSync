"""
TerraFusion SyncService - Market Analysis Plugin - Schemas

This module defines the Pydantic schemas for the Market Analysis plugin.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
import uuid
import datetime

class MarketAnalysisRunRequest(BaseModel):
    """Request schema for running a market analysis job."""
    analysis_type: str = Field(description="Type of market analysis to run.")
    county_id: str = Field(description="County identifier for the analysis.")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the market analysis."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "analysis_type": "price_trend_by_zip",
                    "county_id": "COUNTY01",
                    "parameters": {
                        "start_date": "2024-01-01", 
                        "end_date": "2024-12-31", 
                        "zip_codes": ["90210", "90211"],
                        "property_types": ["residential"]
                    }
                }
            ]
        }
    }

class MarketAnalysisJobStatusResponse(BaseModel):
    """Response schema for market analysis job status."""
    job_id: str = Field(description="Unique identifier for the market analysis job.")
    analysis_type: str = Field(description="Type of market analysis.")
    county_id: str = Field(description="County identifier.")
    status: str = Field(description="Current status of the job (PENDING, RUNNING, COMPLETED, FAILED).")
    message: Optional[str] = Field(default=None, description="Status message or error details.")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Original parameters for the analysis.")
    created_at: datetime.datetime = Field(description="When the job was created.")
    updated_at: datetime.datetime = Field(description="When the job was last updated.")
    started_at: Optional[datetime.datetime] = Field(default=None, description="When the job started processing.")
    completed_at: Optional[datetime.datetime] = Field(default=None, description="When the job completed processing.")

    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v

class MarketTrendDataPoint(BaseModel):
    """A data point for market trend analysis."""
    period: str = Field(description="Time period for the data point (e.g., 2024-Q1).")
    average_price: Optional[float] = Field(default=None, description="Average property price for the period.")
    median_price: Optional[float] = Field(default=None, description="Median property price for the period.")
    sales_volume: Optional[int] = Field(default=None, description="Number of sales during the period.")
    price_per_sqft: Optional[float] = Field(default=None, description="Average price per square foot.")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "period": "2024-Q1",
                    "average_price": 450000.0,
                    "median_price": 425000.0,
                    "sales_volume": 125,
                    "price_per_sqft": 350.75
                }
            ]
        }
    }

class MarketAnalysisResultData(BaseModel):
    """Schema for market analysis results."""
    result_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Summary of key findings from the analysis."
    )
    trends: Optional[List[MarketTrendDataPoint]] = Field(
        default=None,
        description="Time series data points for trend analysis."
    )
    result_data_location: Optional[str] = Field(
        default=None,
        description="Location of the detailed result data (e.g., S3 path)."
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result_summary": {
                        "key_finding": "Market prices increased by 5% year-over-year.",
                        "data_points_analyzed": 1500,
                        "recommendation": "Market conditions favorable for revaluation."
                    },
                    "result_data_location": "/data/analysis_results/COUNTY01/price_trend_by_zip/abc123.parquet"
                }
            ]
        }
    }

class MarketAnalysisJobResultResponse(MarketAnalysisJobStatusResponse):
    """Response schema for market analysis job results."""
    result: Optional[MarketAnalysisResultData] = Field(
        default=None,
        description="The analysis results, if job is completed."
    )