"""
TerraFusion SyncService - GIS Export Plugin - Schemas

This module defines Pydantic models used for data validation and serialization
in the GIS Export plugin API.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json

class GisExportRunRequest(BaseModel):
    """Schema for running a GIS export job."""
    
    county_id: str = Field(..., description="ID of the county")
    format: str = Field(..., description="Export format (GeoJSON, Shapefile, KML, etc)")
    username: str = Field(..., description="Username of the person requesting the export")
    area_of_interest: Dict[str, Any] = Field(
        ..., 
        description="GeoJSON object defining the area of interest"
    )
    layers: List[str] = Field(..., description="List of layers to include in the export")
    parameters: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional parameters for the export (e.g., simplify_tolerance, coordinate_system)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "county_id": "benton_wa",
                "format": "GeoJSON",
                "username": "county_user",
                "area_of_interest": {
                    "type": "Polygon",
                    "coordinates": [[
                        [-122.48, 37.78],
                        [-122.48, 37.80],
                        [-122.46, 37.80],
                        [-122.46, 37.78],
                        [-122.48, 37.78]
                    ]]
                },
                "layers": ["parcels", "buildings", "zoning"],
                "parameters": {
                    "include_attributes": True,
                    "simplify_tolerance": 0.0001,
                    "coordinate_system": "EPSG:4326"
                }
            }
        }

class GisExportJobStatusResponse(BaseModel):
    """Schema for GIS export job status response."""
    
    job_id: str = Field(..., description="Unique ID of the export job")
    county_id: str = Field(..., description="ID of the county")
    export_format: str = Field(..., description="Export format")
    status: str = Field(..., description="Current status of the job")
    message: Optional[str] = Field(None, description="Status message or error details")
    parameters: Dict[str, Any] = Field({}, description="Export parameters")
    created_at: datetime = Field(..., description="When the job was created")
    updated_at: datetime = Field(..., description="When the job was last updated")
    started_at: Optional[datetime] = Field(None, description="When processing started")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")

class GisExportResultData(BaseModel):
    """Schema for GIS export result data."""
    
    file_location: Optional[str] = Field(None, description="URL or path to the export file")
    file_size_kb: Optional[int] = Field(None, description="Size of the export file in KB")
    record_count: Optional[int] = Field(None, description="Number of records in the export")
    data: Optional[Dict[str, Any]] = Field(None, description="Inline GeoJSON data if applicable")

class GisExportJobResultResponse(BaseModel):
    """Schema for GIS export job result response."""
    
    job_id: str = Field(..., description="Unique ID of the export job")
    county_id: str = Field(..., description="ID of the county")
    export_format: str = Field(..., description="Export format")
    status: str = Field(..., description="Current status of the job")
    message: Optional[str] = Field(None, description="Status message or error details")
    parameters: Dict[str, Any] = Field({}, description="Export parameters")
    created_at: datetime = Field(..., description="When the job was created")
    completed_at: Optional[datetime] = Field(None, description="When processing completed")
    result: Optional[GisExportResultData] = Field(None, description="Export result data")