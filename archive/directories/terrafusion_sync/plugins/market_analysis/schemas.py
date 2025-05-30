"""
TerraFusion SyncService - Market Analysis Plugin - Schemas

This module defines the Pydantic models/schemas for the Market Analysis plugin.
These schemas are used for request validation, response serialization, and API documentation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class MarketAnalysisRunRequest(BaseModel):
    """
    Schema for submitting a market analysis job.
    """
    county_id: str = Field(..., description="County ID for which to run the analysis")
    analysis_type: str = Field(..., description="Type of analysis to perform")
    parameters: Dict[str, Any] = Field(
        ..., 
        description="Parameters specific to the analysis type"
    )
    
    @validator('analysis_type')
    def validate_analysis_type(cls, v):
        valid_types = [
            'price_trend_by_zip', 
            'comparable_market_area', 
            'sales_velocity', 
            'market_valuation',
            'price_per_sqft'
        ]
        if v not in valid_types:
            raise ValueError(f"Analysis type must be one of: {', '.join(valid_types)}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "county_id": "county-123",
                "analysis_type": "price_trend_by_zip",
                "parameters": {
                    "zip_code": "90210",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                }
            }
        }


class MarketAnalysisJobStatusResponse(BaseModel):
    """
    Schema for job status response.
    """
    job_id: str
    county_id: str
    analysis_type: str
    status: str 
    message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-123456",
                "county_id": "county-123",
                "analysis_type": "price_trend_by_zip",
                "status": "RUNNING",
                "message": "Job is being processed",
                "created_at": "2025-05-12T10:00:00",
                "updated_at": "2025-05-12T10:01:00",
                "started_at": "2025-05-12T10:00:30",
                "completed_at": None
            }
        }


class MarketAnalysisJobResultResponse(BaseModel):
    """
    Schema for job result response.
    """
    job_id: str
    county_id: str
    analysis_type: str
    status: str
    message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parameters: Dict[str, Any]
    results: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-123456",
                "county_id": "county-123",
                "analysis_type": "price_trend_by_zip",
                "status": "COMPLETED",
                "message": "Job completed successfully",
                "created_at": "2025-05-12T10:00:00",
                "updated_at": "2025-05-12T10:02:00",
                "started_at": "2025-05-12T10:00:30",
                "completed_at": "2025-05-12T10:02:00",
                "parameters": {
                    "zip_code": "90210",
                    "start_date": "2024-01-01",
                    "end_date": "2024-12-31"
                },
                "results": {
                    "average_price": 1250000,
                    "median_price": 1100000,
                    "price_trend": [
                        {"month": "2024-01", "avg_price": 1100000},
                        {"month": "2024-02", "avg_price": 1150000},
                        {"month": "2024-03", "avg_price": 1200000}
                    ],
                    "sample_size": 245
                }
            }
        }