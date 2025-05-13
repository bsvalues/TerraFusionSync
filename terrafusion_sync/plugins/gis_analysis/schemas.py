"""
TerraFusion SyncService - GIS Analysis Plugin - Schemas

This module defines the Pydantic models/schemas for the GIS Analysis plugin.
These schemas are used for request validation, response serialization, and API documentation.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class GISAnalysisType(str, Enum):
    """Types of GIS analyses supported by the plugin."""
    PROPERTY_BOUNDARY = "property_boundary"
    FLOOD_ZONE = "flood_zone"
    ZONING_ANALYSIS = "zoning_analysis"
    PROXIMITY_ANALYSIS = "proximity_analysis"
    HEATMAP_GENERATION = "heatmap_generation"
    SPATIAL_QUERY = "spatial_query"
    BUFFER_ANALYSIS = "buffer_analysis"
    INTERSECTION_ANALYSIS = "intersection_analysis"


class GISAnalysisRunRequest(BaseModel):
    """
    Schema for submitting a GIS analysis job.
    """
    county_id: str = Field(..., description="County ID for which to run the analysis")
    analysis_type: GISAnalysisType = Field(..., description="Type of GIS analysis to perform")
    parameters: Dict[str, Any] = Field(
        ..., 
        description="Parameters specific to the analysis type"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "county_id": "county-123",
                "analysis_type": "property_boundary",
                "parameters": {
                    "property_id": "P12345",
                    "include_adjacent": True,
                    "buffer_distance_meters": 100
                }
            }
        }


class SpatialPoint(BaseModel):
    """Representation of a point in geographic coordinates."""
    longitude: float = Field(..., description="Longitude in decimal degrees")
    latitude: float = Field(..., description="Latitude in decimal degrees")
    
    class Config:
        schema_extra = {
            "example": {
                "longitude": -122.4194,
                "latitude": 37.7749
            }
        }


class SpatialBoundingBox(BaseModel):
    """Representation of a geographic bounding box."""
    min_longitude: float = Field(..., description="Minimum longitude")
    min_latitude: float = Field(..., description="Minimum latitude")
    max_longitude: float = Field(..., description="Maximum longitude")
    max_latitude: float = Field(..., description="Maximum latitude")
    
    class Config:
        schema_extra = {
            "example": {
                "min_longitude": -122.5,
                "min_latitude": 37.7,
                "max_longitude": -122.4,
                "max_latitude": 37.8
            }
        }


class GISQueryParameters(BaseModel):
    """
    Schema for GIS spatial query parameters.
    """
    property_ids: Optional[List[str]] = Field(None, description="List of property IDs to include")
    layer_ids: Optional[List[str]] = Field(None, description="List of spatial layer IDs to include")
    bounding_box: Optional[SpatialBoundingBox] = Field(None, description="Geographic bounding box to limit results")
    center_point: Optional[SpatialPoint] = Field(None, description="Center point for radius-based queries")
    radius_meters: Optional[float] = Field(None, description="Search radius in meters from center point")
    
    @validator('radius_meters')
    def validate_radius(cls, v, values):
        """Validate that radius is provided if center_point is provided."""
        if values.get('center_point') is not None and v is None:
            raise ValueError("radius_meters must be provided when center_point is provided")
        return v


class GISAnalysisJobResponse(BaseModel):
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
                "analysis_type": "property_boundary",
                "status": "RUNNING",
                "message": "Job is being processed",
                "created_at": "2025-05-12T10:00:00",
                "updated_at": "2025-05-12T10:01:00",
                "started_at": "2025-05-12T10:00:30",
                "completed_at": None
            }
        }


class GISFeatureProperties(BaseModel):
    """
    Schema for GIS feature properties.
    """
    property_id: Optional[str] = None
    name: Optional[str] = None
    value: Optional[Union[str, int, float]] = None
    attributes: Optional[Dict[str, Any]] = None


class GISGeometryType(str, Enum):
    """Types of GIS geometries."""
    POINT = "Point"
    LINE_STRING = "LineString"
    POLYGON = "Polygon"
    MULTI_POINT = "MultiPoint"
    MULTI_LINE_STRING = "MultiLineString"
    MULTI_POLYGON = "MultiPolygon"
    GEOMETRY_COLLECTION = "GeometryCollection"


class GISGeometry(BaseModel):
    """
    Schema for GIS geometry (GeoJSON compatible).
    """
    type: GISGeometryType
    coordinates: Any  # Can be point, line, polygon coordinates
    
    class Config:
        schema_extra = {
            "example": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-122.4194, 37.7749],
                        [-122.4195, 37.7750],
                        [-122.4193, 37.7751],
                        [-122.4192, 37.7750],
                        [-122.4194, 37.7749]
                    ]
                ]
            }
        }


class GISFeature(BaseModel):
    """
    Schema for GIS feature (GeoJSON compatible).
    """
    type: str = "Feature"
    geometry: GISGeometry
    properties: GISFeatureProperties
    id: Optional[str] = None


class GISFeatureCollection(BaseModel):
    """
    Schema for GIS feature collection (GeoJSON compatible).
    """
    type: str = "FeatureCollection"
    features: List[GISFeature]
    properties: Optional[Dict[str, Any]] = None


class GISAnalysisResultResponse(BaseModel):
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
    geojson_result: Optional[GISFeatureCollection] = None
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job-123456",
                "county_id": "county-123",
                "analysis_type": "property_boundary",
                "status": "COMPLETED",
                "message": "Job completed successfully",
                "created_at": "2025-05-12T10:00:00",
                "updated_at": "2025-05-12T10:02:00",
                "started_at": "2025-05-12T10:00:30",
                "completed_at": "2025-05-12T10:02:00",
                "parameters": {
                    "property_id": "P12345",
                    "include_adjacent": True,
                    "buffer_distance_meters": 100
                },
                "results": {
                    "area_sq_meters": 5000,
                    "perimeter_meters": 300,
                    "centroid": {
                        "longitude": -122.4194,
                        "latitude": 37.7749
                    }
                },
                "geojson_result": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [
                                    [
                                        [-122.4194, 37.7749],
                                        [-122.4195, 37.7750],
                                        [-122.4193, 37.7751],
                                        [-122.4192, 37.7750],
                                        [-122.4194, 37.7749]
                                    ]
                                ]
                            },
                            "properties": {
                                "property_id": "P12345",
                                "name": "Main Property",
                                "attributes": {
                                    "zoning": "Residential",
                                    "parcel_id": "12345"
                                }
                            }
                        }
                    ]
                }
            }
        }


class SpatialLayerResponse(BaseModel):
    """
    Schema for spatial layer metadata response.
    """
    layer_id: str
    county_id: str
    layer_name: str
    layer_type: str
    description: Optional[str] = None
    source: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    feature_count: Optional[int] = None
    bounds: Optional[SpatialBoundingBox] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "layer_id": "flood-zones-2025",
                "county_id": "county-123",
                "layer_name": "Flood Zones 2025",
                "layer_type": "polygon",
                "description": "Updated flood zone boundaries for 2025",
                "source": "FEMA",
                "attributes": {
                    "zone_code": "string",
                    "flood_risk": "string",
                    "last_updated": "date"
                },
                "feature_count": 1250,
                "bounds": {
                    "min_longitude": -123.0,
                    "min_latitude": 37.0,
                    "max_longitude": -122.0,
                    "max_latitude": 38.0
                },
                "created_at": "2025-01-01T00:00:00",
                "updated_at": "2025-05-01T00:00:00"
            }
        }