"""
SystemMetrics model for TerraFusion SyncService platform.

This module defines the SQLAlchemy model for system metrics, which
store performance and health data for monitoring and analysis.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime

from . import db


class SystemMetrics(db.Model):
    """
    SQLAlchemy model for system metrics.
    
    System metrics store performance and health data about the system
    for monitoring, alerting, and analysis purposes.
    """
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Metric collection timestamp
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    # System resource metrics
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    
    # Service-specific metrics
    service_name = Column(String(64), nullable=False)
    service_status = Column(String(32), nullable=True)
    response_time = Column(Float, nullable=True)
    
    # Process metrics
    process_count = Column(Integer, nullable=True)
    thread_count = Column(Integer, nullable=True)
    
    # Additional metrics in JSON format
    additional_metrics = Column(JSON, nullable=True)
    
    # Create indexes for common queries
    __table_args__ = (
        Index('idx_metrics_timestamp', timestamp),
        Index('idx_metrics_service', service_name),
    )
    
    def __init__(
        self,
        service_name,
        **kwargs
    ):
        """Initialize a new system metrics record."""
        self.service_name = service_name
        
        # Set other fields from kwargs if provided
        self.timestamp = kwargs.get('timestamp', datetime.utcnow())
        self.cpu_usage = kwargs.get('cpu_usage')
        self.memory_usage = kwargs.get('memory_usage')
        self.disk_usage = kwargs.get('disk_usage')
        self.service_status = kwargs.get('service_status')
        self.response_time = kwargs.get('response_time')
        self.process_count = kwargs.get('process_count')
        self.thread_count = kwargs.get('thread_count')
        self.additional_metrics = kwargs.get('additional_metrics', {})
    
    def to_dict(self):
        """Convert the model to a dictionary representation."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage,
            'service_name': self.service_name,
            'service_status': self.service_status,
            'response_time': self.response_time,
            'process_count': self.process_count,
            'thread_count': self.thread_count,
            'additional_metrics': self.additional_metrics
        }