from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

class County(db.Model):
    __tablename__ = 'counties'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    county_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    county_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str] = mapped_column(String(2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ExportJob(db.Model):
    __tablename__ = 'export_jobs'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    county_id: Mapped[str] = mapped_column(String(50), nullable=False)
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    export_format: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    file_path: Mapped[str] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)

class SyncOperation(db.Model):
    __tablename__ = 'sync_operations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    county_id: Mapped[str] = mapped_column(String(50), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=True)