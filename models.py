"""
Models for TerraFusion SyncService database.

This module defines the base database models for the SyncService application.
Note: The core sync models have been moved to apps/backend/models/
"""
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from flask_sqlalchemy import SQLAlchemy
import enum
import json
import uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

# Create a single SQLAlchemy instance to be used throughout the application
db = SQLAlchemy()


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


class PropertyType(enum.Enum):
    """Types of properties for assessment and valuation."""
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    AGRICULTURAL = "agricultural"
    VACANT_LAND = "vacant_land"
    SPECIAL_PURPOSE = "special_purpose"
    MIXED_USE = "mixed_use"


class PropertyOperational(db.Model):
    """
    Operational property assessment data model.
    This model is used to store the core property data that is synchronized 
    between the county systems and TerraFusion, with a focus on valuation
    and assessment operations.
    """
    
    __tablename__ = 'property_operational'
    
    # Primary identifiers
    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.String(36), unique=True, index=True, nullable=False)
    
    # Basic property information
    parcel_number = db.Column(db.String(50), index=True, nullable=False)
    county_id = db.Column(db.String(50), index=True, nullable=False)
    property_type = db.Column(db.String(50), index=True, nullable=False)
    property_class = db.Column(db.String(50), index=True)
    
    # Address information
    address_street = db.Column(db.String(255))
    address_city = db.Column(db.String(100))
    address_state = db.Column(db.String(50))
    address_zip = db.Column(db.String(20))
    
    # Geographic information
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    legal_description = db.Column(db.Text)
    
    # Physical characteristics
    lot_size_sqft = db.Column(db.Float)
    building_size_sqft = db.Column(db.Float)
    year_built = db.Column(db.Integer)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Float)
    stories = db.Column(db.Float)
    
    # Assessment and valuation data
    assessed_value = db.Column(db.Float, index=True)
    market_value = db.Column(db.Float, index=True)
    land_value = db.Column(db.Float)
    improvement_value = db.Column(db.Float)
    assessment_year = db.Column(db.Integer, index=True)
    last_sale_price = db.Column(db.Float)
    last_sale_date = db.Column(db.Date)
    
    # Tax information
    tax_district = db.Column(db.String(100))
    tax_year = db.Column(db.Integer)
    tax_amount = db.Column(db.Float)
    tax_status = db.Column(db.String(50))
    
    # Special statuses
    is_exempt = db.Column(db.Boolean, default=False)
    exemption_type = db.Column(db.String(100))
    is_historic = db.Column(db.Boolean, default=False)
    
    # Tracking fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sync_status = db.Column(db.String(50), default="pending")
    sync_timestamp = db.Column(db.DateTime)
    last_modified_by = db.Column(db.String(100))
    
    # JSON fields for flexible data storage
    attributes = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    valuation_history = db.Column(db.JSON)
    
    # Relationships (can be uncommented when the referenced models are defined)
    # valuations = db.relationship('PropertyValuation', back_populates='property', cascade='all, delete-orphan')
    # attachments = db.relationship('PropertyAttachment', back_populates='property', cascade='all, delete-orphan')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'property_id': self.property_id,
            'parcel_number': self.parcel_number,
            'county_id': self.county_id,
            'property_type': self.property_type,
            'property_class': self.property_class,
            'address_street': self.address_street,
            'address_city': self.address_city,
            'address_state': self.address_state,
            'address_zip': self.address_zip,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'legal_description': self.legal_description,
            'lot_size_sqft': self.lot_size_sqft,
            'building_size_sqft': self.building_size_sqft,
            'year_built': self.year_built,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'stories': self.stories,
            'assessed_value': self.assessed_value,
            'market_value': self.market_value,
            'land_value': self.land_value,
            'improvement_value': self.improvement_value,
            'assessment_year': self.assessment_year,
            'last_sale_price': self.last_sale_price,
            'last_sale_date': self.last_sale_date.isoformat() if self.last_sale_date else None,
            'tax_district': self.tax_district,
            'tax_year': self.tax_year,
            'tax_amount': self.tax_amount,
            'tax_status': self.tax_status,
            'is_exempt': self.is_exempt,
            'exemption_type': self.exemption_type,
            'is_historic': self.is_historic,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'sync_status': self.sync_status,
            'sync_timestamp': self.sync_timestamp.isoformat() if self.sync_timestamp else None,
            'last_modified_by': self.last_modified_by,
            'attributes': self.attributes,
            'valuation_history': self.valuation_history
        }
    
    def update_valuation(self, assessed_value: float, market_value: float, assessment_year: int) -> None:
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


class ReportJob(db.Model):
    """
    Model for tracking report generation jobs.
    This model is used to track the status and details of report generation tasks,
    which may run asynchronously and take some time to complete.
    """
    
    __tablename__ = 'report_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    report_type = db.Column(db.String(50), nullable=False)
    report_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Who requested the report
    user_id = db.Column(db.String(100))
    username = db.Column(db.String(100))
    
    # When the report job was created/updated
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Parameters and filters for the report
    parameters = db.Column(db.JSON, nullable=True)
    
    # Report output options
    format = db.Column(db.String(20), default=ReportFormat.PDF.value)
    
    # Processing status
    status = db.Column(db.String(20), default=ReportStatus.PENDING.value)
    progress = db.Column(db.Float, default=0.0)  # Percentage complete (0-100)
    
    # Result storage
    result_url = db.Column(db.String(255), nullable=True)  # URL to the generated report
    result_size = db.Column(db.Integer, nullable=True)  # Size in bytes
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Performance tracking
    processing_started_at = db.Column(db.DateTime, nullable=True)
    processing_completed_at = db.Column(db.DateTime, nullable=True)
    
    # Additional metadata
    county_id = db.Column(db.String(50), nullable=True)  # County for the report
    correlation_id = db.Column(db.String(100), nullable=True)  # For cross-service tracking
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'report_type': self.report_type,
            'report_name': self.report_name,
            'description': self.description,
            'user_id': self.user_id,
            'username': self.username,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'parameters': self.parameters,
            'format': self.format,
            'status': self.status,
            'progress': self.progress,
            'result_url': self.result_url,
            'result_size': self.result_size,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'processing_started_at': self.processing_started_at.isoformat() if self.processing_started_at else None,
            'processing_completed_at': self.processing_completed_at.isoformat() if self.processing_completed_at else None,
            'county_id': self.county_id,
            'correlation_id': self.correlation_id,
            'processing_time': self.get_processing_time()
        }
    
    def get_processing_time(self) -> Optional[float]:
        """Calculate the processing time in seconds, if available."""
        if self.processing_started_at and self.processing_completed_at:
            return (self.processing_completed_at - self.processing_started_at).total_seconds()
        return None
    
    def start_processing(self) -> None:
        """Mark the job as processing and record the start time."""
        self.status = ReportStatus.PROCESSING.value
        self.processing_started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_processing(self, result_url: str, result_size: int) -> None:
        """Mark the job as completed and record the results."""
        self.status = ReportStatus.COMPLETED.value
        self.progress = 100.0
        self.result_url = result_url
        self.result_size = result_size
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_processing(self, error_message: str) -> None:
        """Mark the job as failed with an error message."""
        self.status = ReportStatus.FAILED.value
        self.error_message = error_message
        self.processing_completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def update_progress(self, progress: float) -> None:
        """Update the progress percentage of the report generation."""
        self.progress = min(max(progress, 0.0), 99.9)  # Keep between 0 and 99.9%
        self.updated_at = datetime.utcnow()


class SystemMetrics(db.Model):
    """System performance metrics tracked over time."""
    
    __tablename__ = 'system_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    cpu_usage = db.Column(db.Float)
    memory_usage = db.Column(db.Float)
    disk_usage = db.Column(db.Float)
    active_connections = db.Column(db.Integer)
    response_time = db.Column(db.Float)
    error_count = db.Column(db.Integer)
    sync_operations_count = db.Column(db.Integer)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'active_connections': self.active_connections,
            'response_time': self.response_time,
            'error_count': self.error_count,
            'sync_operations_count': self.sync_operations_count
        }


class AuditEntry(db.Model):
    """
    Audit trail entry for tracking all system events and changes.
    This model is used for compliance, security, and debugging purposes.
    """
    
    __tablename__ = 'audit_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Who performed the action
    user_id = db.Column(db.String(100))  # Usually from authentication system
    username = db.Column(db.String(100))
    
    # What action was performed
    event_type = db.Column(db.String(50), nullable=False)  # 'sync_started', 'sync_completed', 'config_changed', etc.
    resource_type = db.Column(db.String(50), nullable=False)  # 'sync_pair', 'operation', 'system_config', etc.
    resource_id = db.Column(db.String(100))  # ID of the resource if applicable
    
    # Linked to a sync operation (if applicable)
    operation_id = db.Column(db.Integer, db.ForeignKey('sync_operations.id'), nullable=True)
    
    # Details of the action
    description = db.Column(db.Text, nullable=False)
    previous_state = db.Column(db.JSON, nullable=True)  # For tracking changes
    new_state = db.Column(db.JSON, nullable=True)  # For tracking changes
    
    # Additional metadata
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(250))
    correlation_id = db.Column(db.String(100))  # For tracing across services
    
    # Severity of the event
    severity = db.Column(db.String(20), default='info')  # 'info', 'warning', 'error', 'critical'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the model to a dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'user_id': self.user_id,
            'username': self.username,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'operation_id': self.operation_id,
            'description': self.description,
            'previous_state': self.previous_state,
            'new_state': self.new_state,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'correlation_id': self.correlation_id,
            'severity': self.severity
        }