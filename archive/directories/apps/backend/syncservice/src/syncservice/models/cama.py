"""
Models for the CAMA system.

This module defines the schema and data models for the target CAMA system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import relationship

from syncservice.models.base import BaseDBModel, BasePydanticModel


class CAMAProperty(BaseDBModel):
    """SQLAlchemy model for the CAMA Property table."""
    
    __tablename__ = "cama_property"
    
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    parcel_number = Column(String(50), nullable=False, index=True)
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(2), nullable=True)
    zip_code = Column(String(10), nullable=True)
    legal_description = Column(Text, nullable=True)
    acreage = Column(Float, nullable=True)
    year_built = Column(Integer, nullable=True)
    source_last_modified = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    geo_coordinates = Column(JSON, nullable=True)
    additional_data = Column(JSON, nullable=True)


class CAMAOwner(BaseDBModel):
    """SQLAlchemy model for the CAMA Owner table."""
    
    __tablename__ = "cama_owner"
    
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("cama_property.id"), nullable=False)
    owner_name = Column(String(255), nullable=False)
    owner_type = Column(String(50), nullable=True)
    ownership_percentage = Column(Float, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    source_last_modified = Column(DateTime, nullable=False)
    contact_information = Column(JSON, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    property = relationship("CAMAProperty", back_populates="owners")


class CAMAValue(BaseDBModel):
    """SQLAlchemy model for the CAMA property value table."""
    
    __tablename__ = "cama_value"
    
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("cama_property.id"), nullable=False)
    tax_year = Column(Integer, nullable=False)
    assessed_value = Column(Float, nullable=True)
    market_value = Column(Float, nullable=True)
    land_value = Column(Float, nullable=True)
    improvement_value = Column(Float, nullable=True)
    source_last_modified = Column(DateTime, nullable=False)
    valuation_method = Column(String(100), nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    property = relationship("CAMAProperty", back_populates="values")


class CAMAStructure(BaseDBModel):
    """SQLAlchemy model for the CAMA Structure table."""
    
    __tablename__ = "cama_structure"
    
    source_id = Column(String(100), nullable=False, unique=True, index=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("cama_property.id"), nullable=False)
    structure_type = Column(String(100), nullable=False)
    square_footage = Column(Float, nullable=True)
    condition = Column(String(50), nullable=True)
    year_built = Column(Integer, nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Float, nullable=True)
    source_last_modified = Column(DateTime, nullable=False)
    construction_details = Column(JSON, nullable=True)
    amenities = Column(JSON, nullable=True)
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    property = relationship("CAMAProperty", back_populates="structures")


# Add back-references
CAMAProperty.owners = relationship("CAMAOwner", back_populates="property")
CAMAProperty.values = relationship("CAMAValue", back_populates="property")
CAMAProperty.structures = relationship("CAMAStructure", back_populates="property")


# Pydantic models for data validation and API interactions
class CAMAPropertySchema(BasePydanticModel):
    """Pydantic model for CAMA Property data."""
    
    id: str
    source_id: str
    parcel_number: str
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    legal_description: Optional[str] = None
    acreage: Optional[float] = None
    year_built: Optional[int] = None
    source_last_modified: datetime
    is_active: bool
    geo_coordinates: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CAMAOwnerSchema(BasePydanticModel):
    """Pydantic model for CAMA Owner data."""
    
    id: str
    source_id: str
    property_id: str
    owner_name: str
    owner_type: Optional[str] = None
    ownership_percentage: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    source_last_modified: datetime
    contact_information: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CAMAValueSchema(BasePydanticModel):
    """Pydantic model for CAMA Value data."""
    
    id: str
    source_id: str
    property_id: str
    tax_year: int
    assessed_value: Optional[float] = None
    market_value: Optional[float] = None
    land_value: Optional[float] = None
    improvement_value: Optional[float] = None
    source_last_modified: datetime
    valuation_method: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CAMAStructureSchema(BasePydanticModel):
    """Pydantic model for CAMA Structure data."""
    
    id: str
    source_id: str
    property_id: str
    structure_type: str
    square_footage: Optional[float] = None
    condition: Optional[str] = None
    year_built: Optional[int] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    source_last_modified: datetime
    construction_details: Optional[Dict[str, Any]] = None
    amenities: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class CAMAPropertyComplete(CAMAPropertySchema):
    """Complete CAMA Property record with related data."""
    
    owners: List[CAMAOwnerSchema] = []
    values: List[CAMAValueSchema] = []
    structures: List[CAMAStructureSchema] = []
