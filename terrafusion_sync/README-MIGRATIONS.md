# TerraFusion SyncService Database Migrations

This document explains how to use Alembic for database migrations in the TerraFusion SyncService.

## Overview

Database migrations are managed using Alembic, an SQLAlchemy migration tool. Migrations allow us to evolve the database schema over time while maintaining data integrity and tracking changes.

## Directory Structure

The migration system is structured as follows:

- `terrafusion_sync/alembic.ini` - Alembic configuration file
- `terrafusion_sync/alembic_migrations/` - Directory containing migration scripts
  - `env.py` - Alembic environment configuration
  - `script.py.mako` - Template for migration scripts
  - `versions/` - Directory containing migration version scripts

## Creating Migrations

To create a new migration, use the provided helper script:

```bash
# Generate a migration based on model changes
python terrafusion_sync/create_initial_migration.py
```

This will create a new migration script in the `alembic_migrations/versions/` directory. The script will contain the changes needed to update the database schema based on the current SQLAlchemy models.

You can also create migrations manually using the Alembic CLI:

```bash
# Generate a new migration (must be run from terrafusion_sync directory)
cd terrafusion_sync
alembic revision -m "description_of_changes" --autogenerate
```

## Running Migrations

To apply migrations to the database, use the provided helper script:

```bash
# Apply all pending migrations
python terrafusion_sync/run_migrations.py
```

This will bring your database schema up to date with the latest migration version.

You can also run migrations using the Alembic CLI:

```bash
# Apply all pending migrations (must be run from terrafusion_sync directory)
cd terrafusion_sync
alembic upgrade head

# Apply migrations up to a specific version
alembic upgrade <revision_id>

# Revert migrations down to a specific version
alembic downgrade <revision_id>

# Revert one migration
alembic downgrade -1
```

## Database Configuration

Alembic uses the database connection URL from your environment variables:

```
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
```

## Development Workflow

1. Make changes to your SQLAlchemy models in `core_models.py`
2. Generate a migration: `python terrafusion_sync/create_initial_migration.py`
3. Review the generated migration script in `alembic_migrations/versions/`
4. Apply the migration: `python terrafusion_sync/run_migrations.py`
5. Verify the changes in the database

## Testing Migrations

For testing, a separate test database is used. The test infrastructure automatically applies migrations to the test database before running tests.

The test database URL is configured in the `.env` file:

```
TEST_DATABASE_URL=postgresql+asyncpg://user:password@host/dbname_test
```

## Troubleshooting

If you encounter issues with migrations:

1. Ensure the `DATABASE_URL` environment variable is set correctly
2. Check that your models are properly defined in `core_models.py`
3. If autogeneration isn't detecting changes, ensure your models inherit from the same `Base` class used by Alembic
4. For complex schema changes, consider writing manual migrations instead of using autogeneration

For more information, refer to the [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/).