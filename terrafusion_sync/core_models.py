"""
TerraFusion SyncService - Core Models

This module provides the core SQLAlchemy models for the property assessment and sync operations.
These models are designed to be compatible with an async setup.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any, Set
import uuid  # For generating UUIDs
import enum
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Table, Date, Enum
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ==========================================
# Property Assessment Models
# ==========================================

class PropertyType(enum.Enum):
    """Types of properties for assessment and valuation."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    VACANT_LAND = "vacant_land"
    SPECIAL_PURPOSE = "special_purpose"
    MIXED_USE = "mixed_use"


class PropertyOperational(Base):
    """
    Operational property assessment data model.
    This model stores the core property data that is synchronized 
    between the county systems and TerraFusion, with a focus on valuation
    and assessment operations.
    """
    
    __tablename__ = 'property_operational'
    
    # Primary identifiers
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic property information
    parcel_number: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    county_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    property_type: Mapped[str] = mapped_column(String(50), index=True)
    property_class: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    
    # Address information
    address_street: Mapped[Optional[str]] = mapped_column(String(255))
    address_city: Mapped[Optional[str]] = mapped_column(String(100))
    address_state: Mapped[Optional[str]] = mapped_column(String(50))
    address_zip: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Geographic information
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    legal_description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Physical characteristics
    lot_size_sqft: Mapped[Optional[float]] = mapped_column(Float)
    building_size_sqft: Mapped[Optional[float]] = mapped_column(Float)
    year_built: Mapped[Optional[int]] = mapped_column(Integer)
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[float]] = mapped_column(Float)
    stories: Mapped[Optional[float]] = mapped_column(Float)
    
    # Assessment and valuation data
    assessed_value: Mapped[Optional[float]] = mapped_column(Float, index=True)
    market_value: Mapped[Optional[float]] = mapped_column(Float, index=True)
    land_value: Mapped[Optional[float]] = mapped_column(Float)
    improvement_value: Mapped[Optional[float]] = mapped_column(Float)
    assessment_year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    last_sale_price: Mapped[Optional[float]] = mapped_column(Float)
    last_sale_date: Mapped[Optional[date]] = mapped_column(Date)
    
    # Tax information
    tax_district: Mapped[Optional[str]] = mapped_column(String(100))
    tax_year: Mapped[Optional[int]] = mapped_column(Integer)
    tax_amount: Mapped[Optional[float]] = mapped_column(Float)
    tax_status: Mapped[Optional[str]] = mapped_column(String(50))
    
    # Special statuses
    is_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    exemption_type: Mapped[Optional[str]] = mapped_column(String(100))
    is_historic: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Tracking fields
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_status: Mapped[str] = mapped_column(String(50), default="pending")
    sync_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime)
    last_modified_by: Mapped[Optional[str]] = mapped_column(String(100))
    
    # JSON fields for flexible data storage
    attributes: Mapped[Dict] = mapped_column(MutableDict.as_mutable(JSONB), default=dict)
    valuation_history: Mapped[Optional[List]] = mapped_column(JSON)
    
    # Relationships (can be uncommented when the referenced models are defined)
    # valuations: Mapped[List["PropertyValuation"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    # attachments: Mapped[List["PropertyAttachment"]] = relationship(back_populates="property", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for API responses."""
        # Handle date/datetime serialization
        def serialize_value(value):
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            return value
            
        result = {
            "id": self.id,
            "property_id": self.property_id,
            "parcel_number": self.parcel_number,
            "county_id": self.county_id,
            "property_type": self.property_type,
            "property_class": self.property_class,
            
            "address": {
                "street": self.address_street,
                "city": self.address_city,
                "state": self.address_state,
                "zip": self.address_zip
            },
            
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "legal_description": self.legal_description
            },
            
            "physical_details": {
                "lot_size_sqft": self.lot_size_sqft,
                "building_size_sqft": self.building_size_sqft,
                "year_built": self.year_built,
                "bedrooms": self.bedrooms,
                "bathrooms": self.bathrooms,
                "stories": self.stories
            },
            
            "valuation": {
                "assessed_value": self.assessed_value,
                "market_value": self.market_value,
                "land_value": self.land_value,
                "improvement_value": self.improvement_value,
                "assessment_year": self.assessment_year,
                "last_sale_price": self.last_sale_price,
                "last_sale_date": serialize_value(self.last_sale_date)
            },
            
            "tax_info": {
                "tax_district": self.tax_district,
                "tax_year": self.tax_year,
                "tax_amount": self.tax_amount,
                "tax_status": self.tax_status
            },
            
            "flags": {
                "is_exempt": self.is_exempt,
                "exemption_type": self.exemption_type,
                "is_historic": self.is_historic
            },
            
            "metadata": {
                "created_at": serialize_value(self.created_at),
                "updated_at": serialize_value(self.updated_at),
                "sync_status": self.sync_status,
                "sync_timestamp": serialize_value(self.sync_timestamp),
                "last_modified_by": self.last_modified_by
            },
            
            "attributes": self.attributes,
            "valuation_history": self.valuation_history
        }
        
        return result
    
    async def update_valuation(self, assessed_value: float, market_value: float, assessment_year: int) -> None:
        """
        Update the property valuation and track history.
        
        Args:
            assessed_value: New assessed value
            market_value: New market value
            assessment_year: Year of the assessment
        """
        # Store current values in history before updating
        if not self.valuation_history:
            self.valuation_history = []
            
        # Append current values to history
        if self.assessed_value is not None and self.market_value is not None:
            history_entry = {
                'assessed_value': self.assessed_value,
                'market_value': self.market_value,
                'assessment_year': self.assessment_year,
                'recorded_at': datetime.utcnow().isoformat()
            }
            self.valuation_history.append(history_entry)
        
        # Update to new values
        self.assessed_value = assessed_value
        self.market_value = market_value
        self.assessment_year = assessment_year
        self.updated_at = datetime.utcnow()


# ==========================================
# Reporting Models
# ==========================================

class ReportType(enum.Enum):
    """Types of reports that can be generated."""
    PROPERTY_ASSESSMENT = "property_assessment"
    VALUATION_SUMMARY = "valuation_summary"
    COUNTY_COMPARISON = "county_comparison"
    SYNC_AUDIT = "sync_audit"
    TAX_PROJECTION = "tax_projection"
    CUSTOM = "custom"


class ReportFormat(enum.Enum):
    """Available formats for generated reports."""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    JSON = "json"
    HTML = "html"


class ReportStatus(enum.Enum):
    """Possible statuses for a report job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class ReportJob(Base):
    """
    Model for tracking report generation jobs.
    This model is used to track the status and details of report generation tasks,
    which may run asynchronously and take some time to complete.
    """
    
    __tablename__ = 'report_jobs'
    
    # Primary key and identifiers - matching database schema
    # The database uses report_id as the public identifier
    report_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    county_id: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # When the report job was created/updated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When processing started
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When processing completed
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), default=ReportStatus.PENDING.value)
    
    # Parameters JSON for the report
    parameters_json: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Result storage
    result_location: Mapped[Optional[str]] = mapped_column(String(255))  # URL to the generated report
    result_metadata_json: Mapped[Optional[Dict]] = mapped_column(JSON)  # Metadata about the result
    
    # Error tracking
    message: Mapped[Optional[str]] = mapped_column(Text)  # Error message or status details
    
    # Note: The started_at and completed_at fields replace these fields
    # We keep them for backward compatibility with existing code
    # Eventually these should be removed when all code is updated
    processing_started_at = property(lambda self: self.started_at)
    processing_completed_at = property(lambda self: self.completed_at)
    
    # Additional metadata for cross-service tracking
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100))  # For cross-service tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary for API responses."""
        # Helper function to handle date and datetime serialization
        def serialize_value(value):
            if isinstance(value, (datetime, date)):
                return value.isoformat()
            return value
            
        result = {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "county_id": self.county_id,
            
            "timestamps": {
                "created_at": serialize_value(self.created_at),
                "updated_at": serialize_value(self.updated_at),
                "started_at": serialize_value(self.started_at),
                "completed_at": serialize_value(self.completed_at)
            },
            
            "parameters": self.parameters_json,
            
            "status": {
                "current": self.status,
                "message": self.message
            },
            
            "result": {
                "location": self.result_location,
                "metadata": self.result_metadata_json
            }
        }
        
        return result
    
    async def get_processing_time(self) -> Optional[float]:
        """Calculate the processing time in seconds, if available."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    async def start_processing(self) -> None:
        """Mark the job as processing and record the start time."""
        self.status = ReportStatus.PROCESSING.value
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    async def complete_processing(self, result_location: str, result_metadata: Dict[str, Any]) -> None:
        """Mark the job as completed and record the results."""
        self.status = ReportStatus.COMPLETED.value
        self.result_location = result_location
        self.result_metadata_json = result_metadata
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    async def fail_processing(self, error_message: str) -> None:
        """Mark the job as failed with an error message."""
        self.status = ReportStatus.FAILED.value
        self.message = error_message
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

# All duplicate model definitions have been removed