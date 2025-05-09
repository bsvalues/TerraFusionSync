"""
TerraFusion SyncService - Core Models

This module provides the core SQLAlchemy models for the property assessment and sync operations.
These models are designed to be compatible with an async setup.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid  # For generating UUIDs
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Table
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass

class PropertyOperational(Base):
    """
    PropertyOperational model for property assessment data.
    
    This core model represents property assessment data in the operational database.
    It contains essential property details for valuation, assessment, and sync operations.
    """
    __tablename__ = 'properties_operational'
    
    # Primary identification fields
    property_id = mapped_column(String(50), primary_key=True)
    county_id = mapped_column(String(20), nullable=False, index=True)
    parcel_number = mapped_column(String(50), nullable=False, index=True)
    
    # Address information
    address_street = mapped_column(String(100), nullable=False)
    address_city = mapped_column(String(50), nullable=False)
    address_state = mapped_column(String(2), nullable=False)
    address_zip = mapped_column(String(10), nullable=False)
    
    # Property characteristics
    property_type = mapped_column(String(30), nullable=False)  # residential, commercial, industrial, agricultural, etc.
    land_area_sqft = mapped_column(Float, nullable=True)
    building_area_sqft = mapped_column(Float, nullable=True)
    year_built = mapped_column(Integer, nullable=True)
    bedrooms = mapped_column(Integer, nullable=True)
    bathrooms = mapped_column(Float, nullable=True)
    
    # Valuation data
    last_sale_date = mapped_column(DateTime, nullable=True)
    last_sale_price = mapped_column(Float, nullable=True)
    current_market_value = mapped_column(Float, nullable=True)
    assessed_value = mapped_column(Float, nullable=True)
    assessment_year = mapped_column(Integer, nullable=True)
    
    # Tax information
    tax_district = mapped_column(String(50), nullable=True)
    millage_rate = mapped_column(Float, nullable=True)
    tax_amount = mapped_column(Float, nullable=True)
    
    # Ownership details
    owner_name = mapped_column(String(100), nullable=True)
    owner_type = mapped_column(String(30), nullable=True)  # individual, business, trust, etc.
    
    # Geospatial data
    latitude = mapped_column(Float, nullable=True)
    longitude = mapped_column(Float, nullable=True)
    
    # Legal description
    legal_description = mapped_column(Text, nullable=True)
    
    # Special attributes
    is_exempt = mapped_column(Boolean, default=False)
    exemption_type = mapped_column(String(50), nullable=True)
    is_historical = mapped_column(Boolean, default=False)
    
    # Metadata
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_sync_id = mapped_column(Integer, nullable=True)
    data_source = mapped_column(String(50), nullable=True)
    
    # Extended data storage (for flexible schema)
    extended_attributes = mapped_column(JSON, nullable=True)
    
    # Relationships
    valuations = relationship("PropertyValuation", back_populates="property", cascade="all, delete-orphan")
    improvements = relationship("PropertyImprovement", back_populates="property", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PropertyOperational {self.property_id} ({self.address_street}, {self.address_city})>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        result = {
            "property_id": self.property_id,
            "county_id": self.county_id,
            "parcel_number": self.parcel_number,
            "address": f"{self.address_street}, {self.address_city}, {self.address_state} {self.address_zip}",
            "property_type": self.property_type,
            "land_area_sqft": self.land_area_sqft,
            "building_area_sqft": self.building_area_sqft,
            "year_built": self.year_built,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "last_sale_date": self.last_sale_date.isoformat() if self.last_sale_date else None,
            "last_sale_price": self.last_sale_price,
            "current_market_value": self.current_market_value,
            "assessed_value": self.assessed_value,
            "assessment_year": self.assessment_year,
            "owner_name": self.owner_name,
            "is_exempt": self.is_exempt,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        # Add extended attributes if available
        if self.extended_attributes:
            for key, value in self.extended_attributes.items():
                if key not in result:  # Avoid overwriting standard attributes
                    result[key] = value
        
        return result


class PropertyValuation(Base):
    """
    PropertyValuation model for tracking valuations of properties over time.
    
    This model stores historical and current valuations of properties, including
    methods used, confidence levels, and other evaluation metrics.
    """
    __tablename__ = 'property_valuations'
    
    id = mapped_column(Integer, primary_key=True)
    property_id = mapped_column(String(50), ForeignKey('properties_operational.property_id'), nullable=False)
    
    # Valuation details
    valuation_date = mapped_column(DateTime, default=datetime.utcnow)
    valuation_amount = mapped_column(Float, nullable=False)
    valuation_method = mapped_column(String(50), nullable=False)  # comparable_sales, income_approach, cost_approach, etc.
    valuation_type = mapped_column(String(30), nullable=False)  # market, assessed, taxable, etc.
    valuation_year = mapped_column(Integer, nullable=False)
    
    # Valuation metrics
    confidence_score = mapped_column(Float, nullable=True)  # 0-100%
    margin_of_error = mapped_column(Float, nullable=True)  # percentage
    
    # Valuation supporting data
    comparables_used = mapped_column(JSON, nullable=True)  # List of comparable property IDs used
    adjustments = mapped_column(JSON, nullable=True)  # Adjustments made during valuation
    notes = mapped_column(Text, nullable=True)
    
    # Approval information
    is_final = mapped_column(Boolean, default=False)
    approved_by = mapped_column(String(100), nullable=True)
    approved_at = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    created_by = mapped_column(String(100), nullable=True)
    sync_operation_id = mapped_column(Integer, nullable=True)
    
    # Relationships
    property = relationship("PropertyOperational", back_populates="valuations")
    
    def __repr__(self):
        return f"<PropertyValuation {self.id} for {self.property_id} - {self.valuation_amount}>"


class PropertyImprovement(Base):
    """
    PropertyImprovement model for tracking improvements to properties.
    
    This model represents improvements made to properties, such as building
    additions, renovations, or other material changes that affect value.
    """
    __tablename__ = 'property_improvements'
    
    id = mapped_column(Integer, primary_key=True)
    property_id = mapped_column(String(50), ForeignKey('properties_operational.property_id'), nullable=False)
    
    # Improvement details
    improvement_type = mapped_column(String(50), nullable=False)  # addition, renovation, pool, outbuilding, etc.
    description = mapped_column(Text, nullable=False)
    year_completed = mapped_column(Integer, nullable=True)
    
    # Size and cost
    area_added_sqft = mapped_column(Float, nullable=True)
    cost = mapped_column(Float, nullable=True)
    value_added = mapped_column(Float, nullable=True)
    
    # Permit information
    permit_number = mapped_column(String(50), nullable=True)
    permit_date = mapped_column(DateTime, nullable=True)
    permit_status = mapped_column(String(30), nullable=True)  # approved, pending, complete
    
    # Metadata
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_source = mapped_column(String(50), nullable=True)
    
    # Relationships
    property = relationship("PropertyOperational", back_populates="improvements")
    
    def __repr__(self):
        return f"<PropertyImprovement {self.id} for {self.property_id} - {self.improvement_type}>"


class SyncSourceSystem(Base):
    """
    SyncSourceSystem model for managing external source systems.
    
    This model represents county systems or external data sources from which
    property data is synchronized.
    """
    __tablename__ = 'sync_source_systems'
    
    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String(100), nullable=False)
    system_type = mapped_column(String(50), nullable=False)  # pacs, gis, document_management, etc.
    county_id = mapped_column(String(20), nullable=False)
    
    # Connection details
    connection_type = mapped_column(String(30), nullable=False)  # database, api, file_import, etc.
    connection_config = mapped_column(Text, nullable=False)  # JSON encoded connection details
    
    # Authentication
    auth_type = mapped_column(String(30), nullable=True)  # basic, oauth, api_key, etc.
    auth_config = mapped_column(Text, nullable=True)  # JSON encoded auth details (encrypted)
    
    # Schema mapping
    schema_mapping = mapped_column(JSON, nullable=True)  # Mapping from source fields to TerraFusion fields
    
    # System status
    is_active = mapped_column(Boolean, default=True)
    last_successful_sync = mapped_column(DateTime, nullable=True)
    
    # Metadata
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = mapped_column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<SyncSourceSystem {self.name} ({self.system_type} - {self.county_id})>"


class ImportJob(Base):
    """
    ImportJob model for tracking data import jobs.
    
    This model represents batch import jobs from source systems, including
    their status, progress, and results.
    """
    __tablename__ = 'import_jobs'
    
    id = mapped_column(Integer, primary_key=True)
    source_system_id = mapped_column(Integer, ForeignKey('sync_source_systems.id'), nullable=False)
    
    # Job details
    job_type = mapped_column(String(50), nullable=False)  # full_import, delta_import, validation, etc.
    status = mapped_column(String(30), default='pending')  # pending, running, completed, failed, cancelled
    
    # Progress tracking
    total_records = mapped_column(Integer, default=0)
    processed_records = mapped_column(Integer, default=0)
    successful_records = mapped_column(Integer, default=0)
    failed_records = mapped_column(Integer, default=0)
    
    # Time tracking
    start_time = mapped_column(DateTime, nullable=True)
    end_time = mapped_column(DateTime, nullable=True)
    estimated_completion_time = mapped_column(DateTime, nullable=True)
    
    # Job configuration
    job_parameters = mapped_column(JSON, nullable=True)  # Parameters used for this import job
    
    # Results
    result_summary = mapped_column(Text, nullable=True)  # Summary of results
    error_log = mapped_column(Text, nullable=True)  # Log of errors
    
    # Metadata
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    created_by = mapped_column(String(100), nullable=True)
    
    # Relationships
    source_system = relationship("SyncSourceSystem")
    
    def __repr__(self):
        return f"<ImportJob {self.id} - {self.job_type} from {self.source_system_id} ({self.status})>"
    
    @property
    def progress_percentage(self) -> float:
        """Calculate the progress percentage of the import job."""
        if not self.total_records or self.total_records == 0:
            return 0.0
        return round((self.processed_records / self.total_records) * 100, 2)
    
    @property
    def success_rate(self) -> float:
        """Calculate the success rate of the import job."""
        if not self.processed_records or self.processed_records == 0:
            return 0.0
        return round((self.successful_records / self.processed_records) * 100, 2)
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Calculate the duration of the import job in seconds."""
        if not self.end_time or not self.start_time:
            return None
        return int((self.end_time - self.start_time).total_seconds())


class ReportJob(Base):
    """
    Represents a reporting job, its status, parameters, and results location.
    
    This model is used to track the lifecycle of report generation jobs, including
    their configuration, status, and where to find the generated reports.
    """
    __tablename__ = 'report_jobs'

    # Primary identification fields
    report_id = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_type = mapped_column(String(50), index=True, nullable=False, comment="Type of report being generated (e.g., sales_ratio_study, assessment_roll)")
    county_id = mapped_column(String(20), index=True, nullable=False, comment="County ID for which the report is generated")
    
    # Status tracking
    status = mapped_column(String(30), index=True, nullable=False, default="PENDING", 
                          comment="Report job status: PENDING, RUNNING, COMPLETED, FAILED")
    message = mapped_column(Text, nullable=True, comment="Status message or error details")
    
    # Configuration
    parameters_json = mapped_column(JSON, nullable=True, 
                                  comment="JSON object storing the parameters used for report generation")
    
    # Timestamps
    created_at = mapped_column(DateTime, default=datetime.utcnow, 
                             comment="Timestamp when the job was created")
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                             comment="Timestamp of the last status update")
    started_at = mapped_column(DateTime, nullable=True, 
                             comment="Timestamp when report generation started")
    completed_at = mapped_column(DateTime, nullable=True, 
                               comment="Timestamp when report generation completed or failed")

    # Result Information
    result_location = mapped_column(String(255), nullable=True, 
                                  comment="Location/identifier of the generated report (e.g., S3 path, URL)")
    result_metadata_json = mapped_column(JSON, nullable=True, 
                                       comment="Optional metadata about the report result (e.g., file size, page count)")

    def __repr__(self):
        return f"<ReportJob report_id='{self.report_id}' report_type='{self.report_type}' county_id='{self.county_id}' status='{self.status}'>"
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary representation."""
        result = {
            "report_id": self.report_id,
            "report_type": self.report_type,
            "county_id": self.county_id,
            "status": self.status,
            "message": self.message,
            "parameters": self.parameters_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result_location": self.result_location,
            "result_metadata": self.result_metadata_json
        }
        return result