"""
Models for the legacy PACS system.

This module defines the schema and data models for the source PACS system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        String, Text)
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from syncservice.models.base import BasePydanticModel

# Create a separate base for SQL Server models
SQLServerBase = declarative_base()


class PACSProperty(SQLServerBase):
    """SQLAlchemy model for the PACS Property table."""
    
    __tablename__ = "Property"
    
    PropertyID = Column(UNIQUEIDENTIFIER, primary_key=True)
    ParcelNumber = Column(String(50), nullable=False, index=True)
    Address = Column(String(255), nullable=True)
    City = Column(String(100), nullable=True)
    State = Column(String(2), nullable=True)
    ZipCode = Column(String(10), nullable=True)
    LegalDescription = Column(Text, nullable=True)
    Acreage = Column(Float, nullable=True)
    YearBuilt = Column(Integer, nullable=True)
    LastModified = Column(DateTime, nullable=False, index=True)
    IsActive = Column(Boolean, default=True, nullable=False)


class PACSOwner(SQLServerBase):
    """SQLAlchemy model for the PACS Owner table."""
    
    __tablename__ = "Owner"
    
    OwnerID = Column(UNIQUEIDENTIFIER, primary_key=True)
    PropertyID = Column(UNIQUEIDENTIFIER, ForeignKey("Property.PropertyID"), nullable=False)
    OwnerName = Column(String(255), nullable=False)
    OwnerType = Column(String(50), nullable=True)
    OwnershipPercentage = Column(Float, nullable=True)
    StartDate = Column(DateTime, nullable=True)
    EndDate = Column(DateTime, nullable=True)
    LastModified = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    property = relationship("PACSProperty", back_populates="owners")


class PACSValueHistory(SQLServerBase):
    """SQLAlchemy model for the PACS property value history."""
    
    __tablename__ = "ValueHistory"
    
    ValueID = Column(UNIQUEIDENTIFIER, primary_key=True)
    PropertyID = Column(UNIQUEIDENTIFIER, ForeignKey("Property.PropertyID"), nullable=False)
    TaxYear = Column(Integer, nullable=False)
    AssessedValue = Column(Float, nullable=True)
    MarketValue = Column(Float, nullable=True)
    LandValue = Column(Float, nullable=True)
    ImprovementValue = Column(Float, nullable=True)
    LastModified = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    property = relationship("PACSProperty", back_populates="value_history")


class PACSStructure(SQLServerBase):
    """SQLAlchemy model for the PACS Structure table."""
    
    __tablename__ = "Structure"
    
    StructureID = Column(UNIQUEIDENTIFIER, primary_key=True)
    PropertyID = Column(UNIQUEIDENTIFIER, ForeignKey("Property.PropertyID"), nullable=False)
    StructureType = Column(String(100), nullable=False)
    SquareFootage = Column(Float, nullable=True)
    Condition = Column(String(50), nullable=True)
    YearBuilt = Column(Integer, nullable=True)
    Bedrooms = Column(Integer, nullable=True)
    Bathrooms = Column(Float, nullable=True)
    LastModified = Column(DateTime, nullable=False, index=True)
    
    # Relationships
    property = relationship("PACSProperty", back_populates="structures")


# Add back-references
PACSProperty.owners = relationship("PACSOwner", back_populates="property")
PACSProperty.value_history = relationship("PACSValueHistory", back_populates="property")
PACSProperty.structures = relationship("PACSStructure", back_populates="property")


# Pydantic models for data validation and API interactions
class PACSPropertySchema(BasePydanticModel):
    """Pydantic model for PACS Property data."""
    
    PropertyID: str
    ParcelNumber: str
    Address: Optional[str] = None
    City: Optional[str] = None
    State: Optional[str] = None
    ZipCode: Optional[str] = None
    LegalDescription: Optional[str] = None
    Acreage: Optional[float] = None
    YearBuilt: Optional[int] = None
    LastModified: datetime
    IsActive: bool


class PACSOwnerSchema(BasePydanticModel):
    """Pydantic model for PACS Owner data."""
    
    OwnerID: str
    PropertyID: str
    OwnerName: str
    OwnerType: Optional[str] = None
    OwnershipPercentage: Optional[float] = None
    StartDate: Optional[datetime] = None
    EndDate: Optional[datetime] = None
    LastModified: datetime


class PACSValueHistorySchema(BasePydanticModel):
    """Pydantic model for PACS Value History data."""
    
    ValueID: str
    PropertyID: str
    TaxYear: int
    AssessedValue: Optional[float] = None
    MarketValue: Optional[float] = None
    LandValue: Optional[float] = None
    ImprovementValue: Optional[float] = None
    LastModified: datetime


class PACSStructureSchema(BasePydanticModel):
    """Pydantic model for PACS Structure data."""
    
    StructureID: str
    PropertyID: str
    StructureType: str
    SquareFootage: Optional[float] = None
    Condition: Optional[str] = None
    YearBuilt: Optional[int] = None
    Bedrooms: Optional[int] = None
    Bathrooms: Optional[float] = None
    LastModified: datetime


class PACSPropertyComplete(PACSPropertySchema):
    """Complete PACS Property record with related data."""
    
    owners: List[PACSOwnerSchema] = []
    value_history: List[PACSValueHistorySchema] = []
    structures: List[PACSStructureSchema] = []
