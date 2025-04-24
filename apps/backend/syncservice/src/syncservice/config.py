"""
Configuration settings for the SyncService plugin.

This module provides a Pydantic Settings class to manage environment variables
and configuration for the application.
"""

import os
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # General settings
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    
    # SQL Server (source) settings
    sqlserver_driver: str = Field(default="ODBC Driver 17 for SQL Server", env="SQLSERVER_DRIVER")
    sqlserver_host: str = Field(..., env="SQLSERVER_HOST")
    sqlserver_port: int = Field(default=1433, env="SQLSERVER_PORT")
    sqlserver_database: str = Field(..., env="SQLSERVER_DATABASE")
    sqlserver_user: str = Field(..., env="SQLSERVER_USER")
    sqlserver_password: str = Field(..., env="SQLSERVER_PASSWORD")
    
    # PostgreSQL (target) settings
    postgres_host: str = Field(default=os.getenv("PGHOST", "localhost"), env="POSTGRES_HOST")
    postgres_port: int = Field(default=int(os.getenv("PGPORT", "5432")), env="POSTGRES_PORT")
    postgres_database: str = Field(default=os.getenv("PGDATABASE", "postgres"), env="POSTGRES_DATABASE")
    postgres_user: str = Field(default=os.getenv("PGUSER", "postgres"), env="POSTGRES_USER")
    postgres_password: str = Field(default=os.getenv("PGPASSWORD", ""), env="POSTGRES_PASSWORD")
    
    # NATS settings
    nats_url: str = Field(default="nats://localhost:4222", env="NATS_URL")
    
    # OpenAI API for AI enrichment
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Field mapping configuration
    field_mapping_path: str = Field(
        default="src/syncservice/field_mapping.yaml", 
        env="FIELD_MAPPING_PATH"
    )
    
    class Config:
        """Pydantic config settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Create cached instance of application settings.
    
    Returns:
        Settings: Application configuration settings
    """
    return Settings()
