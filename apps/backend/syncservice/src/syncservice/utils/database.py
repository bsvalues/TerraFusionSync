"""
Database utilities for the SyncService.

This module provides functions to connect to source and target databases
and execute queries.
"""

import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

import pyodbc
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from syncservice.config import get_settings

logger = logging.getLogger(__name__)

# Database engines
source_engine: Optional[AsyncEngine] = None
target_engine: Optional[AsyncEngine] = None

# Session factories
source_session_factory = None
target_session_factory = None


async def init_db_connections() -> None:
    """
    Initialize database connections for source and target systems.
    """
    global source_engine, target_engine, source_session_factory, target_session_factory
    
    settings = get_settings()
    
    # Initialize source database connection (SQL Server)
    try:
        # For SQL Server, we'll use pyodbc directly as asyncio support is limited
        source_conn_str = (
            f"DRIVER={{{settings.sqlserver_driver}}};"
            f"SERVER={settings.sqlserver_host},{settings.sqlserver_port};"
            f"DATABASE={settings.sqlserver_database};"
            f"UID={settings.sqlserver_user};"
            f"PWD={settings.sqlserver_password}"
        )
        
        logger.info(f"Connecting to source database: {settings.sqlserver_host}:{settings.sqlserver_port}/{settings.sqlserver_database}")
        # Using sqlalchemy for now, but we'll need to adapt for async operations
        source_engine = create_async_engine(
            f"mssql+pyodbc:///?odbc_connect={source_conn_str}",
            future=True,
            echo=settings.debug_mode
        )
        
        # Create session factory for source database
        source_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=source_engine,
            class_=sa.orm.Session
        )
        
        logger.info("Source database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize source database connection: {str(e)}")
        raise
    
    # Initialize target database connection (PostgreSQL)
    try:
        # PostgreSQL connection string
        postgres_conn_str = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}@"
            f"{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
        )
        
        logger.info(f"Connecting to target database: {settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}")
        target_engine = create_async_engine(
            postgres_conn_str,
            future=True,
            echo=settings.debug_mode
        )
        
        # Create session factory for target database
        target_session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=target_engine,
            class_=sa.orm.Session
        )
        
        logger.info("Target database connection initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize target database connection: {str(e)}")
        raise


async def close_db_connections() -> None:
    """
    Close database connections.
    """
    global source_engine, target_engine
    
    if source_engine:
        logger.info("Closing source database connection")
        await source_engine.dispose()
        source_engine = None
    
    if target_engine:
        logger.info("Closing target database connection")
        await target_engine.dispose()
        target_engine = None


@asynccontextmanager
async def get_source_session():
    """
    Get a session for the source database.
    
    Returns:
        Context manager that yields a database session.
    """
    if source_session_factory is None:
        await init_db_connections()
        
    session = source_session_factory()
    try:
        yield session
    finally:
        session.close()


@asynccontextmanager
async def get_target_session():
    """
    Get a session for the target database.
    
    Returns:
        Context manager that yields a database session.
    """
    if target_session_factory is None:
        await init_db_connections()
        
    session = target_session_factory()
    try:
        yield session
    finally:
        session.close()


async def execute_source_query(query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
    """
    Execute a query against the source database.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        List of dictionaries containing query results
    """
    try:
        async with get_source_session() as session:
            result = await session.execute(sa.text(query), params or {})
            if result.returns_rows:
                # Convert row proxies to dictionaries
                return [dict(row._mapping) for row in result]
            return []
    except Exception as e:
        logger.error(f"Error executing source query: {str(e)}")
        raise


async def execute_target_query(query: str, params: Optional[List] = None) -> List[Dict[str, Any]]:
    """
    Execute a query against the target database.
    
    Args:
        query: SQL query to execute
        params: Query parameters
        
    Returns:
        List of dictionaries containing query results
    """
    try:
        async with get_target_session() as session:
            result = await session.execute(sa.text(query), params or {})
            if result.returns_rows:
                # Convert row proxies to dictionaries
                return [dict(row._mapping) for row in result]
            return []
    except Exception as e:
        logger.error(f"Error executing target query: {str(e)}")
        raise


async def check_source_connection() -> bool:
    """
    Check if the source database connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    try:
        await execute_source_query("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Source database connection check failed: {str(e)}")
        return False


async def check_target_connection() -> bool:
    """
    Check if the target database connection is working.
    
    Returns:
        True if connection is working, False otherwise
    """
    try:
        await execute_target_query("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Target database connection check failed: {str(e)}")
        return False
