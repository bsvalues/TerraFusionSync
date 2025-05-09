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
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()))
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    report_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Who requested the report
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    username: Mapped[Optional[str]] = mapped_column(String(100))
    
    # When the report job was created/updated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Parameters and filters for the report
    parameters: Mapped[Optional[Dict]] = mapped_column(JSON)
    
    # Report output options
    format: Mapped[str] = mapped_column(String(20), default=ReportFormat.PDF.value)
    
    # Processing status
    status: Mapped[str] = mapped_column(String(20), default=ReportStatus.PENDING.value)
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # Percentage complete (0-100)
    
    # Result storage
    result_url: Mapped[Optional[str]] = mapped_column(String(255))  # URL to the generated report
    result_size: Mapped[Optional[int]] = mapped_column(Integer)  # Size in bytes
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Performance tracking
    processing_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    processing_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Additional metadata
    county_id: Mapped[Optional[str]] = mapped_column(String(50))  # County for the report
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100))  # For cross-service tracking
    
    async def get_processing_time(self) -> Optional[float]:
        """Calculate the processing time in seconds, if available."""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None
    
    async def start_processing(self) -> None:
        """Mark the job as processing and record the start time."""
        self.status = ReportStatus.PROCESSING.value
        self.processing_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    async def complete_processing(self, result_url: str, result_size: int) -> None:
        """Mark the job as completed and record the results."""
        self.status = ReportStatus.COMPLETED.value
        self.progress = 100.0
        self.result_url = result_url
        self.result_size = result_size
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    async def fail_processing(self, error_message: str) -> None:
        """Mark the job as failed with an error message."""
        self.status = ReportStatus.FAILED.value
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    async def update_progress(self, progress: float) -> None:
        """Update the progress percentage of the report generation."""
        self.progress = min(max(progress, 0.0), 99.9)  # Keep between 0 and 99.9%
        self.updated_at = datetime.utcnow()

# All duplicate model definitions have been removed