"""
TerraFusion SyncService - GIS Analysis Plugin - Models

This module defines the SQLAlchemy models for the GIS Analysis plugin.
"""

import sqlalchemy as sa
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from terrafusion_sync.database import Base


class GISAnalysisJob(Base):
    """
    GIS Analysis Job model.
    
    This model represents a job for processing GIS analysis requests.
    """
    __tablename__ = 'gis_analysis_jobs'
    
    # Primary keys and identifiers
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    job_id = sa.Column(sa.String(36), unique=True, nullable=False, index=True)
    county_id = sa.Column(sa.String(50), nullable=False, index=True)
    
    # Analysis details
    analysis_type = sa.Column(sa.String(50), nullable=False, index=True)
    parameters_json = sa.Column(sa.Text, nullable=True)
    
    # Status and results
    status = sa.Column(sa.String(20), nullable=False, index=True, default="PENDING")
    message = sa.Column(sa.String(255), nullable=True)
    result_json = sa.Column(sa.Text, nullable=True)
    result_summary_json = sa.Column(sa.Text, nullable=True)
    geojson_result = sa.Column(sa.Text, nullable=True)  # For storing GeoJSON output
    
    # Timestamps
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = sa.Column(sa.DateTime, nullable=True)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    
    def __repr__(self) -> str:
        """String representation of a job."""
        return f"<GISAnalysisJob(job_id={self.job_id}, status={self.status})>"


class SpatialLayerMetadata(Base):
    """
    Spatial Layer Metadata model.
    
    This model stores metadata about available spatial layers for GIS analysis.
    """
    __tablename__ = 'spatial_layer_metadata'
    
    # Primary keys and identifiers
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    layer_id = sa.Column(sa.String(50), unique=True, nullable=False, index=True)
    county_id = sa.Column(sa.String(50), nullable=False, index=True)
    
    # Layer details
    layer_name = sa.Column(sa.String(100), nullable=False)
    layer_type = sa.Column(sa.String(50), nullable=False)  # polygon, point, line, raster
    description = sa.Column(sa.String(255), nullable=True)
    source = sa.Column(sa.String(100), nullable=True)
    
    # Layer attributes
    attributes_json = sa.Column(sa.Text, nullable=True)  # Available fields/attributes
    style_json = sa.Column(sa.Text, nullable=True)  # Default styling options
    
    # Metadata
    feature_count = sa.Column(sa.Integer, nullable=True)  # Number of features in the layer
    bounds_json = sa.Column(sa.Text, nullable=True)  # Geographic bounds as JSON
    created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        """String representation of a spatial layer."""
        return f"<SpatialLayerMetadata(layer_id={self.layer_id}, name={self.layer_name})>"