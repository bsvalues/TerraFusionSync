"""
TerraFusion SyncService - GIS Export Plugin - Schemas

This module defines the Pydantic models/schemas for the GIS Export plugin.
These schemas are used for request validation, response serialization, and API documentation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
import uuid
import datetime

class GisExportRunRequest(BaseModel):
    export_format: str = Field(..., example="GeoJSON", description="Desired output format (e.g., GeoJSON, Shapefile, KML).")
    county_id: str = Field(..., example="COUNTY01")
    area_of_interest: Optional[Dict[str, Any]] = Field(None, example={"type": "bbox", "coordinates": [-120.5, 46.0, -120.0, 46.5]}, description="Defines the spatial extent.")
    layers: List[str] = Field(..., example=["parcels", "zoning"], description="List of data layers to include.")
    parameters: Optional[Dict[str, Any]] = Field(None, example={"include_assessment_data": True}, description="Additional export parameters.")

class GisExportJobStatusResponse(BaseModel):
    job_id: str
    export_format: str
    county_id: str
    status: str
    message: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None # Includes AOI and layers for reference
    created_at: datetime.datetime
    updated_at: datetime.datetime
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None

class GisExportResultData(BaseModel):
    result_file_location: Optional[str] = None # URL or path to the exported file
    result_file_size_kb: Optional[int] = None
    result_record_count: Optional[int] = None
    # Add other relevant result metadata

class GisExportJobResultResponse(GisExportJobStatusResponse):
    result: Optional[GisExportResultData] = None