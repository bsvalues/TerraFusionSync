"""
TerraFusion SyncService - Reporting Schemas

This module defines the Pydantic schemas for the reporting plugin,
providing validation and serialization for API requests and responses.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str = Field(..., description="Error message details")


class ReportJobCreate(BaseModel):
    """Schema for creating a new report job."""
    report_type: str = Field(
        ...,
        description="Type of report to generate (e.g., 'sales_ratio_study', 'assessment_roll')"
    )
    county_id: str = Field(
        ...,
        description="County ID for which to generate the report"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional parameters for report generation"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "report_type": "assessment_roll",
                "county_id": "county-123",
                "parameters": {
                    "year": 2025,
                    "include_exemptions": True,
                    "output_format": "pdf"
                }
            }
        }


class ReportJobUpdate(BaseModel):
    """Schema for updating a report job."""
    status: str = Field(
        ...,
        description="New status (PENDING, RUNNING, COMPLETED, FAILED)"
    )
    message: Optional[str] = Field(
        None,
        description="Optional status message or error details"
    )
    result_location: Optional[str] = Field(
        None,
        description="Location/identifier of the generated report (e.g., S3 path, URL)"
    )
    result_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata about the report result (e.g., file size, page count)"
    )
    
    @validator('status')
    def validate_status(cls, v):
        """Validate that status is one of the allowed values."""
        allowed = ["PENDING", "RUNNING", "COMPLETED", "FAILED"]
        if v not in allowed:
            raise ValueError(f"Status must be one of: {', '.join(allowed)}")
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "status": "COMPLETED",
                "message": "Report generated successfully",
                "result_location": "reports/county-123/assessment_roll_2025.pdf",
                "result_metadata": {
                    "file_size_bytes": 2048576,
                    "page_count": 42,
                    "generated_timestamp": "2025-05-09T12:34:56Z"
                }
            }
        }


class ReportJobBase(BaseModel):
    """Base schema for report job responses."""
    report_id: str = Field(..., description="Unique identifier for the report job")
    report_type: str = Field(..., description="Type of report")
    county_id: str = Field(..., description="County ID for which the report is generated")
    status: str = Field(..., description="Current status of the report job")
    message: Optional[str] = Field(None, description="Status message or error details")
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters used for report generation"
    )
    created_at: datetime = Field(..., description="Timestamp when the job was created")
    updated_at: datetime = Field(..., description="Timestamp of the last status update")
    started_at: Optional[datetime] = Field(
        None,
        description="Timestamp when report generation started"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="Timestamp when report generation completed or failed"
    )
    result_location: Optional[str] = Field(
        None,
        description="Location/identifier of the generated report"
    )
    result_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata about the report result"
    )


class ReportJobResponse(ReportJobBase):
    """Schema for report job responses."""
    
    class Config:
        from_attributes = True
        
        # Map model attribute names to schema field names
        model_config = {
            "json_schema_extra": {
                "example": {
                    "report_id": "123e4567-e89b-12d3-a456-426614174000",
                    "report_type": "assessment_roll",
                    "county_id": "county-123",
                    "status": "COMPLETED",
                    "message": "Report generated successfully",
                    "parameters": {
                        "year": 2025,
                        "include_exemptions": True
                    },
                    "created_at": "2025-05-09T12:00:00Z",
                    "updated_at": "2025-05-09T12:30:00Z",
                    "started_at": "2025-05-09T12:05:00Z",
                    "completed_at": "2025-05-09T12:30:00Z",
                    "result_location": "reports/county-123/assessment_roll_2025.pdf",
                    "result_metadata": {
                        "file_size_bytes": 2048576,
                        "page_count": 42
                    }
                }
            }
        }
        
    # Map DB field names to schema field names
    @classmethod
    def from_orm(cls, obj):
        # Create a dictionary of the model's attributes
        obj_dict = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
        
        # Map specific JSON fields
        if "parameters_json" in obj_dict:
            obj_dict["parameters"] = obj_dict.pop("parameters_json")
        if "result_metadata_json" in obj_dict:
            obj_dict["result_metadata"] = obj_dict.pop("result_metadata_json")
            
        # Create instance
        return cls(**obj_dict)


class ReportJobListResponse(BaseModel):
    """Schema for a list of report jobs."""
    items: List[ReportJobResponse] = Field(..., description="List of report jobs")
    count: int = Field(..., description="Number of jobs in the response")