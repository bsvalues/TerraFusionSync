"""
Database utilities for SyncService.

This module provides database utilities for connecting to and interacting with
both source and target databases.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from syncservice.config.system_config import get_sync_config

logger = logging.getLogger(__name__)

# Global database engines and session factories
source_engine: Optional[AsyncEngine] = None
target_engine: Optional[AsyncEngine] = None
source_session_factory: Optional[sessionmaker] = None
target_session_factory: Optional[sessionmaker] = None


async def init_db_connections() -> None:
    """
    Initialize database connections for source and target systems.
    """
    global source_engine, target_engine, source_session_factory, target_session_factory
    
    config = get_sync_config()
    
    # Find the first enabled source system with PACS type
    pacs_configs = [
        system for system in config.source_systems.values()
        if system.is_enabled and system.system_type == 'pacs'
    ]
    
    # Find the first enabled target system with CAMA type
    cama_configs = [
        system for system in config.target_systems.values()
        if system.is_enabled and system.system_type == 'cama'
    ]
    
    if pacs_configs:
        # Initialize source database connection (SQL Server)
        try:
            source_params = pacs_configs[0].connection_params
            
            # For SQL Server, we'll use pyodbc directly as asyncio support is limited
            source_conn_str = (
                f"DRIVER={{{source_params.get('driver', 'ODBC Driver 17 for SQL Server')}}};"
                f"SERVER={source_params.get('host', 'localhost')},"
                f"{source_params.get('port', 1433)};"
                f"DATABASE={source_params.get('database', 'PACS')};"
                f"UID={source_params.get('user', 'sa')};"
                f"PWD={source_params.get('password', '')}"
            )
            
            logger.info(f"Connecting to source database: {source_params.get('host')}:{source_params.get('port')}/{source_params.get('database')}")
            
            # Using sqlalchemy for now, but we'll need to adapt for async operations
            source_engine = create_async_engine(
                f"mssql+pyodbc:///?odbc_connect={source_conn_str}",
                future=True,
                echo=source_params.get('debug_mode', False)
            )
            
            # Create session factory for source database
            source_session_factory = sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                bind=source_engine
            )
            
            logger.info("Source database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize source database connection: {str(e)}")
    
    if cama_configs:
        # Initialize target database connection (PostgreSQL)
        try:
            target_params = cama_configs[0].connection_params
            
            target_url = (
                f"postgresql+asyncpg://"
                f"{target_params.get('user', os.getenv('PGUSER', 'postgres'))}:"
                f"{target_params.get('password', os.getenv('PGPASSWORD', ''))}@"
                f"{target_params.get('host', os.getenv('PGHOST', 'localhost'))}:"
                f"{target_params.get('port', int(os.getenv('PGPORT', '5432')))}/"
                f"{target_params.get('database', os.getenv('PGDATABASE', 'postgres'))}"
            )
            
            logger.info(f"Connecting to target database: {target_params.get('host')}:{target_params.get('port')}/{target_params.get('database')}")
            
            # Create engine for PostgreSQL
            target_engine = create_async_engine(
                target_url,
                future=True,
                echo=target_params.get('debug_mode', False)
            )
            
            # Create session factory for target database
            target_session_factory = sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                bind=target_engine
            )
            
            logger.info("Target database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize target database connection: {str(e)}")


async def get_source_session() -> AsyncSession:
    """
    Get a session for the source database.
    
    Returns:
        AsyncSession: Session for the source database
    """
    if source_session_factory is None:
        await init_db_connections()
        
    if source_session_factory is None:
        raise RuntimeError("Source database connection not initialized")
        
    return source_session_factory()


async def get_target_session() -> AsyncSession:
    """
    Get a session for the target database.
    
    Returns:
        AsyncSession: Session for the target database
    """
    if target_session_factory is None:
        await init_db_connections()
        
    if target_session_factory is None:
        raise RuntimeError("Target database connection not initialized")
        
    return target_session_factory()


async def execute_source_query(query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a query on the source database.
    
    Args:
        query: SQL query to execute
        params: Parameters for the query
        
    Returns:
        List of dictionaries containing query results
    """
    if params is None:
        params = []
        
    try:
        async with await get_source_session() as session:
            result = await session.execute(text(query), params)
            # Convert to list of dictionaries
            keys = result.keys()
            return [dict(zip(keys, row)) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error executing source query: {str(e)}")
        return []


async def execute_target_query(query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Execute a query on the target database.
    
    Args:
        query: SQL query to execute
        params: Parameters for the query
        
    Returns:
        List of dictionaries containing query results
    """
    if params is None:
        params = []
        
    try:
        async with await get_target_session() as session:
            result = await session.execute(text(query), params)
            # Convert to list of dictionaries
            keys = result.keys()
            return [dict(zip(keys, row)) for row in result.fetchall()]
    except Exception as e:
        logger.error(f"Error executing target query: {str(e)}")
        return []


async def check_source_connection() -> bool:
    """
    Check if the connection to the source database is active.
    
    Returns:
        bool: True if connection is active, False otherwise
    """
    try:
        if source_engine is None:
            await init_db_connections()
            
        if source_engine is None:
            return False
            
        async with await get_source_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Error checking source connection: {str(e)}")
        return False


async def check_target_connection() -> bool:
    """
    Check if the connection to the target database is active.
    
    Returns:
        bool: True if connection is active, False otherwise
    """
    try:
        if target_engine is None:
            await init_db_connections()
            
        if target_engine is None:
            return False
            
        async with await get_target_session() as session:
            result = await session.execute(text("SELECT 1"))
            return result.scalar() == 1
    except Exception as e:
        logger.error(f"Error checking target connection: {str(e)}")
        return False