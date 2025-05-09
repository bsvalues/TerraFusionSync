"""
TerraFusion SyncService - Async Database Connection

This module provides the async SQLAlchemy database connection setup and session management
for the TerraFusion SyncService platform.
"""

import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())

# Database connection string from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("DATABASE_URL environment variable not set. Using SQLite in-memory database for development.")
    DATABASE_URL = "sqlite+aiosqlite:///terrafusion.db"

# Engine configuration with connection pooling settings
engine_kwargs = {
    "echo": os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true",
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 300,
    "pool_pre_ping": True
}

# Create the async engine
engine = create_async_engine(DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_session() -> AsyncSession:
    """
    Get a new async session.
    
    Note: This is a basic session provider. Use get_db_session() as a dependency
    in FastAPI endpoints for proper context management.
    
    Returns:
        AsyncSession: A new async SQLAlchemy session
    """
    return AsyncSessionFactory()


@asynccontextmanager
async def get_db_session():
    """
    Context manager for database sessions.
    
    This async context manager handles session lifecycle, including
    commit, rollback, and cleanup on exceptions.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
    """
    session = AsyncSessionFactory()
    try:
        logger.debug("Database session opened")
        yield session
        await session.commit()
        logger.debug("Database session committed")
    except SQLAlchemyError as e:
        logger.error(f"Database transaction error: {e}", exc_info=True)
        await session.rollback()
        logger.debug("Database session rolled back due to SQLAlchemyError")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database transaction: {e}", exc_info=True)
        await session.rollback()
        logger.debug("Database session rolled back due to unexpected error")
        raise
    finally:
        await session.close()
        logger.debug("Database session closed")


async def initialize_db():
    """
    Initialize the database by creating all tables if they don't exist.
    
    This function should be called during application startup.
    """
    from .core_models import Base
    
    logger.info("Initializing database and creating tables...")
    try:
        async with engine.begin() as conn:
            # Create tables if they don't exist
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise


async def get_db_status():
    """
    Check database connection status.
    
    Returns:
        dict: Status information about the database connection
    """
    try:
        session = await get_session()
        try:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            await result.scalar()
            
            # Get connection pool stats
            pool_size = engine.pool.size()
            checkedin = engine.pool.checkedin()
            checkedout = engine.pool.checkedout()
            
            return {
                "status": "connected",
                "pool_size": pool_size,
                "connections_checked_in": checkedin,
                "connections_checked_out": checkedout,
                "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else "sqlite",
                "message": "Database connection successful"
            }
        except Exception as e:
            logger.error(f"Database status check failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e)
            }
        finally:
            await session.close()
    except Exception as e:
        logger.error(f"Failed to create database session: {e}", exc_info=True)
        return {
            "status": "disconnected",
            "message": f"Could not establish database connection: {str(e)}"
        }