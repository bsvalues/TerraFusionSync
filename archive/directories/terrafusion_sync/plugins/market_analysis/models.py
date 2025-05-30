"""
TerraFusion SyncService - Market Analysis Plugin - Models

This module defines the SQLAlchemy models for the Market Analysis plugin.
"""

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base

# Create a base class for declarative models
Base = declarative_base()

class MarketAnalysisJob(Base):
    """
    Market Analysis Job model.
    
    This model represents a job for processing market analysis requests.
    """
    __tablename__ = 'market_analysis_jobs'
    
    # Primary key and identifiers
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    job_id = sa.Column(sa.String(36), unique=True, nullable=False, index=True)
    county_id = sa.Column(sa.String(50), nullable=False, index=True)
    
    # Job type and parameters
    analysis_type = sa.Column(sa.String(50), nullable=False, index=True)
    parameters_json = sa.Column(sa.Text, nullable=True)
    
    # Status and results
    status = sa.Column(sa.String(20), nullable=False, index=True, default="PENDING")
    message = sa.Column(sa.String(255), nullable=True)
    result_json = sa.Column(sa.Text, nullable=True)
    result_summary_json = sa.Column(sa.Text, nullable=True)
    
    # Timestamps
    created_at = sa.Column(sa.DateTime, nullable=False, index=True)
    updated_at = sa.Column(sa.DateTime, nullable=False)
    started_at = sa.Column(sa.DateTime, nullable=True)
    completed_at = sa.Column(sa.DateTime, nullable=True)
    
    def __repr__(self):
        """String representation of a job."""
        return f"<MarketAnalysisJob(job_id='{self.job_id}', status='{self.status}')>"