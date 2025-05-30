"""
TerraFusion Platform - Database Models

This module defines the SQLAlchemy models for the TerraFusion Platform.
"""

import os
import json
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()
Base = declarative_base()

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256))
    first_name = Column(String(64))
    last_name = Column(String(64))
    county = Column(String(64))  # Fixed column name to avoid conflict
    role = Column(String(32), default='user')
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    gis_export_jobs = relationship("GisExportJob", back_populates="user")
    sync_jobs = relationship("SyncJob", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.username}>"
        
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'county': self.county,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': self.is_active
        }

class County(Base):
    """County model for storing county information."""
    __tablename__ = 'counties'
    
    id = Column(Integer, primary_key=True)
    county_id = Column(String(64), unique=True, nullable=False)
    name = Column(String(128), nullable=False)
    state = Column(String(32))
    config_path = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    gis_export_jobs = relationship("GisExportJob", back_populates="county")
    sync_jobs = relationship("SyncJob", back_populates="county")
    
    def __repr__(self):
        return f"<County {self.name}, {self.state}>"

class GisExportJob(Base):
    """GIS Export Job model for tracking export tasks."""
    __tablename__ = 'gis_export_jobs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    county_id = Column(String(64), ForeignKey('counties.county_id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(64))
    export_format = Column(String(32), nullable=False)
    area_of_interest = Column(JSON)
    layers = Column(JSON)
    parameters = Column(JSON)
    status = Column(String(32), default='PENDING')
    message = Column(Text)
    file_path = Column(String(256))
    file_size = Column(Integer)
    download_url = Column(String(256))
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    county = relationship("County", back_populates="gis_export_jobs")
    user = relationship("User", back_populates="gis_export_jobs")
    
    def __repr__(self):
        return f"<GisExportJob {self.job_id}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'job_id': self.job_id,
            'county_id': self.county_id,
            'username': self.username,
            'export_format': self.export_format,
            'area_of_interest': self.area_of_interest,
            'layers': self.layers,
            'parameters': self.parameters,
            'status': self.status,
            'message': self.message,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'download_url': self.download_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class SyncJob(Base):
    """Sync Job model for tracking data synchronization tasks."""
    __tablename__ = 'sync_jobs'
    
    id = Column(Integer, primary_key=True)
    job_id = Column(String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    county_id = Column(String(64), ForeignKey('counties.county_id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    username = Column(String(64))
    data_types = Column(JSON)
    source_system = Column(String(64))
    target_system = Column(String(64))
    parameters = Column(JSON)
    status = Column(String(32), default='PENDING')
    message = Column(Text)
    stats = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Relationships
    county = relationship("County", back_populates="sync_jobs")
    user = relationship("User", back_populates="sync_jobs")
    
    def __repr__(self):
        return f"<SyncJob {self.job_id}>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'job_id': self.job_id,
            'county_id': self.county_id,
            'username': self.username,
            'data_types': self.data_types,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'parameters': self.parameters,
            'status': self.status,
            'message': self.message,
            'stats': self.stats,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def generate_report(self):
        """Generate a detailed report for this sync job."""
        if self.status != 'COMPLETED':
            raise ValueError(f"Cannot generate report for job with status {self.status}")
        
        # Calculate duration if not already set
        if not self.duration_seconds and self.started_at and self.completed_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        # Generate summary
        summary = []
        summary.append(f"Synchronized data from {self.source_system} to {self.target_system}")
        summary.append(f"Data types: {', '.join(self.data_types)}")
        
        if self.stats:
            summary.append(f"Read {self.stats.get('records_read', 0)} records from source system")
            summary.append(f"Successfully wrote {self.stats.get('records_written', 0)} records to target system")
            
            if self.stats.get('warnings', 0) > 0:
                summary.append(f"Encountered {self.stats.get('warnings')} warnings during processing")
            if self.stats.get('errors', 0) > 0:
                summary.append(f"Encountered {self.stats.get('errors')} errors during processing")
            
            # Calculate success rate
            records_read = self.stats.get('records_read', 0)
            records_written = self.stats.get('records_written', 0)
            if records_read > 0:
                success_rate = (records_written / records_read) * 100
                summary.append(f"Success rate: {success_rate:.2f}%")
        
        # Create report dictionary
        report = {
            'job_id': self.job_id,
            'county_id': self.county_id,
            'username': self.username,
            'source_system': self.source_system,
            'target_system': self.target_system,
            'data_types': self.data_types,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'stats': self.stats,
            'summary': summary
        }
        
        return report

def init_db(app=None):
    """Initialize the database connection and create tables."""
    if app:
        # Use Flask-SQLAlchemy with Flask app
        db.init_app(app)
        with app.app_context():
            Base.metadata.create_all(db.engine)
    else:
        # Standalone SQLAlchemy initialization
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            engine = create_engine(db_url)
            Base.metadata.create_all(engine)
            Session = sessionmaker(bind=engine)
            return Session()
        else:
            raise ValueError("DATABASE_URL environment variable not set")

# Helper function to convert SQLAlchemy model instance to dict
def model_to_dict(model_instance):
    """Convert any SQLAlchemy model instance to a dictionary."""
    if hasattr(model_instance, 'to_dict') and callable(getattr(model_instance, 'to_dict')):
        return model_instance.to_dict()
    
    result = {}
    for column in model_instance.__table__.columns:
        value = getattr(model_instance, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        result[column.name] = value
    return result