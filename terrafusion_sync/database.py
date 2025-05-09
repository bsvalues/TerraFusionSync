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
else:
    # Convert standard PostgreSQL URL to async version if needed
    if DATABASE_URL.startswith('postgresql://'):
        DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1)
        logger.info(f"Using async PostgreSQL connection: {DATABASE_URL.split('@')[0]}@...")
    elif not (DATABASE_URL.startswith('postgresql+asyncpg://') or DATABASE_URL.startswith('sqlite+aiosqlite://')):
        logger.warning(f"Database URL doesn't specify an async driver. Attempting to use: {DATABASE_URL}")
        # We'll let the engine creation attempt to handle any errors if the URL is invalid

# Engine configuration with connection pooling settings
engine_kwargs = {
    "echo": os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true",
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 300,
    "pool_pre_ping": True
}

# Remove SSL parameters if using asyncpg to avoid unsupported parameter issues
if DATABASE_URL.startswith('postgresql+asyncpg://'):
    # Create a modified URL without SSL parameters
    from urllib.parse import urlparse, parse_qs, urlunparse, urlencode
    
    parsed_url = urlparse(DATABASE_URL)
    query_params = parse_qs(parsed_url.query)
    
    # Remove SSL-related parameters that asyncpg doesn't support
    for param in ['sslmode', 'sslrootcert', 'sslcert', 'sslkey']:
        if param in query_params:
            del query_params[param]
    
    # Rebuild the URL
    new_query = urlencode(query_params, doseq=True)
    parsed_url = parsed_url._replace(query=new_query)
    DATABASE_URL = urlunparse(parsed_url)
    
    logger.info(f"Modified database URL for asyncpg compatibility")
    
    # Add custom SSL context configuration if needed
    # engine_kwargs["ssl"] = create_asyncpg_ssl_context()

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

# Configure engine with execution options to help with transaction handling
engine = engine.execution_options(
    isolation_level="READ COMMITTED",  # Less strict isolation level
    postgresql_readonly=False,
    postgresql_deferrable=False  # Non-deferrable transactions
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
    
    Enhanced for better transaction handling in asyncpg to help avoid 
    "cannot perform operation: another operation is in progress" errors.
    
    Yields:
        AsyncSession: An async SQLAlchemy session
    """
    session = AsyncSessionFactory()
    session_id = id(session)  # Get unique identifier for logging
    try:
        logger.debug(f"Database session {session_id} opened")
        yield session
        
        # Try to commit any pending changes
        try:
            # Only commit if there are actual changes
            if session.in_transaction():
                logger.debug(f"Committing database session {session_id}")
                await session.commit()
                logger.debug(f"Database session {session_id} committed")
            else:
                logger.debug(f"No active transaction in session {session_id} to commit")
        except SQLAlchemyError as commit_error:
            logger.error(f"Error committing database session {session_id}: {commit_error}")
            # Attempt to rollback on commit error
            try:
                await session.rollback()
                logger.debug(f"Database session {session_id} rolled back due to commit error")
            except Exception as rollback_error:
                logger.error(f"Error rolling back database session {session_id}: {rollback_error}")
            # We'll re-raise the original commit error
            raise commit_error
    
    except SQLAlchemyError as e:
        logger.error(f"Database transaction error in session {session_id}: {e}", exc_info=True)
        # Attempt rollback, but don't raise additional errors if rollback fails
        try:
            if session.in_transaction():
                await session.rollback()
                logger.debug(f"Database session {session_id} rolled back due to SQLAlchemyError")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback session {session_id}: {rollback_error}")
        raise
        
    except Exception as e:
        logger.error(f"Unexpected error during database transaction in session {session_id}: {e}", exc_info=True)
        # Attempt rollback, but don't raise additional errors if rollback fails
        try:
            if session.in_transaction():
                await session.rollback()
                logger.debug(f"Database session {session_id} rolled back due to unexpected error")
        except Exception as rollback_error:
            logger.error(f"Failed to rollback session {session_id}: {rollback_error}")
        raise
        
    finally:
        # Always close the session, but don't raise additional errors if close fails
        try:
            await session.close()
            logger.debug(f"Database session {session_id} closed")
        except Exception as close_error:
            logger.error(f"Error closing database session {session_id}: {close_error}")
            # We don't re-raise this error as it would mask the original exception


async def initialize_db():
    """
    Initialize the database by creating all tables if they don't exist.
    
    This function should be called during application startup.
    """
    from terrafusion_sync.core_models import Base
    
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
            # Simple query to test connection using text object
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            # Get scalar result without awaiting it (as it's not awaitable)
            scalar_result = result.scalar_one()
            
            # Get basic connection info
            pool_stats = {
                "pool_type": str(type(engine.pool)).split("'")[1],  # Extract just the class name
                "database_type": DATABASE_URL.split(":")[0] if ":" in DATABASE_URL else "unknown"
            }
            
            return {
                "status": "connected",
                **pool_stats,
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