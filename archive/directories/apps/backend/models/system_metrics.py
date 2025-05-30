"""
TerraFusion SyncService model for System Metrics.

This module defines the SystemMetrics model, representing collected
system metrics for monitoring and analytics.
"""

import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from .base import Base


class SystemMetrics(Base):
    """
    SystemMetrics model representing collected system metrics.
    
    This model tracks system metrics such as CPU/memory usage, operation
    counts, error rates, and other performance indicators.
    """
    __tablename__ = 'system_metrics'
    
    id = Column(Integer, primary_key=True)
    
    # Measurement identifiers
    service = Column(String(255), nullable=False)  # "api_gateway", "sync_service", etc.
    instance_id = Column(String(255), nullable=True)  # Optional instance identifier
    
    # System resource metrics
    cpu_usage = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    disk_usage = Column(Float, nullable=True)
    
    # Application-specific metrics
    active_connections = Column(Integer, nullable=True)
    response_time = Column(Float, nullable=True)
    error_count = Column(Integer, nullable=True)
    error_rate = Column(Float, nullable=True)
    
    # Business metrics
    sync_operations_count = Column(Integer, nullable=True)
    sync_operations_success_rate = Column(Float, nullable=True)
    
    # Additional metrics in JSON format
    additional_metrics = Column(JSON, nullable=True)
    
    # Status information
    status = Column(String(50), nullable=False)  # "healthy", "degraded", "unhealthy"
    
    # Timestamps
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    timestamp = Column(DateTime, nullable=True)  # For compatibility with existing code
    
    def __repr__(self):
        return f"<SystemMetrics {self.id}: {self.service} at {self.collected_at} ({self.status})>"
    
    def to_dict(self):
        """
        Convert the SystemMetrics to a dictionary representation.
        
        Returns:
            Dictionary representation of the SystemMetrics
        """
        result = {
            "id": self.id,
            "service": self.service,
            "status": self.status,
            "collected_at": self.collected_at.isoformat(),
            "metrics": {
                "cpu_usage": self.cpu_usage,
                "memory_usage": self.memory_usage,
                "disk_usage": self.disk_usage,
                "active_connections": self.active_connections,
                "response_time": self.response_time,
                "error_count": self.error_count,
                "error_rate": self.error_rate,
                "sync_operations_count": self.sync_operations_count,
                "sync_operations_success_rate": self.sync_operations_success_rate
            }
        }
        
        # Include instance_id if available
        if self.instance_id:
            result["instance_id"] = self.instance_id
        
        # Include additional metrics if available
        if self.additional_metrics:
            if isinstance(self.additional_metrics, str):
                additional = json.loads(self.additional_metrics)
            else:
                additional = self.additional_metrics
            
            # Merge additional metrics into the metrics dictionary
            result["metrics"].update(additional)
        
        return result
    
    @classmethod
    def create_from_dict(cls, data, service, status="healthy"):
        """
        Create a new SystemMetrics instance from a dictionary.
        
        Args:
            data: Dictionary containing metrics data
            service: Service name (e.g., "api_gateway", "sync_service")
            status: System status (default: "healthy")
            
        Returns:
            New SystemMetrics instance
        """
        instance = cls(
            service=service,
            status=status,
            collected_at=datetime.utcnow()
        )
        
        # Map standard metrics fields
        standard_fields = {
            "cpu_usage": Float,
            "memory_usage": Float,
            "disk_usage": Float,
            "active_connections": Integer,
            "response_time": Float,
            "error_count": Integer,
            "error_rate": Float,
            "sync_operations_count": Integer,
            "sync_operations_success_rate": Float
        }
        
        # Set standard fields if they exist in the data
        for field, field_type in standard_fields.items():
            if field in data:
                setattr(instance, field, data[field])
        
        # If instance_id exists in data, set it
        if "instance_id" in data:
            instance.instance_id = data["instance_id"]
        
        # Store any additional metrics
        additional_metrics = {}
        for key, value in data.items():
            if key not in standard_fields and key != "instance_id":
                additional_metrics[key] = value
        
        if additional_metrics:
            instance.additional_metrics = additional_metrics
        
        return instance