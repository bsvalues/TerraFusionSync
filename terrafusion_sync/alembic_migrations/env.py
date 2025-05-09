"""
Alembic environment script for database migrations in the TerraFusion SyncService.

This script configures the Alembic environment for SQLAlchemy's
async engine, enabling schema version control for the application's models.
"""

import os
import sys
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

# Add the parent directory to sys.path to allow importing application modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the SQLAlchemy declarative Base
from terrafusion_sync.core_models import Base
# Import all models here to ensure they are known to SQLAlchemy
# When the metadata is reflected, these models will be included
# For example:
# from terrafusion_sync.core_models import PropertyOperational, ReportJob, ValuationJob

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

def get_url():
    """Get the SQLAlchemy database URL from environment variables."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set.")
    
    # Convert standard URL to async URL if needed
    if "postgresql://" in db_url and "asyncpg" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    return db_url

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations in the standard SQLAlchemy way."""
    context.configure(
        connection=connection, 
        target_metadata=target_metadata,
        compare_type=True, # Detect column type changes
        compare_server_default=True, # Detect default value changes
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    url = get_url()
    
    # Create an async engine
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        # This await is necessary for the async engine
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # Handle running this code inside or outside an event loop
    try:
        # Get the current event loop, or create a new one
        loop = asyncio.get_event_loop()
        
        # Check if the loop is already running
        if loop.is_running():
            # If we're inside a running event loop, we can just create a task
            # The caller is expected to run the event loop
            print("Running migrations inside an existing event loop.")
            loop.create_task(run_migrations_online())
        else:
            # If no event loop is running, run a new one
            print("Running migrations with a new event loop.")
            asyncio.run(run_migrations_online())
    except RuntimeError as e:
        if "There is no current event loop in thread" in str(e):
            # No event loop in this thread, create a new one
            print("Creating a new event loop for migrations.")
            asyncio.run(run_migrations_online())
        else:
            raise