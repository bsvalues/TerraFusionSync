# TerraFusion SyncService

A sophisticated microservice for synchronizing data between multiple enterprise systems including PACS, CAMA, GIS, and ERP platforms.

## Architecture Overview

TerraFusion SyncService uses a two-tier microservice architecture:

### 1. API Gateway (Flask, port 5000)
- Main entry point for all client requests
- Handles authentication and routing
- Proxies API requests to the SyncService
- Provides auto-recovery of the SyncService if it stops
- Status monitoring and management endpoints

### 2. SyncService (FastAPI, port 8000)
- Core business logic for synchronization
- Implements change detection, transformation, validation
- Provides detailed metrics and monitoring
- Self-healing capabilities for failed syncs
- Handles direct database interactions

### Communication Flow
Client → API Gateway (port 5000) → SyncService (port 8000) → External Systems

## Core Components

### Change Detector
- Identifies changes in source systems since last sync
- Supports both full and incremental sync modes
- Query optimization for large datasets
- Configurable change detection logic per system type

### Transformer
- Converts source data format to target system format
- Field mapping configuration through YAML files
- Supports complex transformations with custom scripts
- Handles data type conversion and validation

### Validator
- Schema-based validation for transformed data
- Business rule validation using configurable rules engine
- Historical data consistency checks
- Warning and error severity levels

### Self-Healing Orchestrator
- Retries failed operations with exponential backoff
- Dependency-aware ordering of sync operations
- Transaction management across systems
- Error isolation to prevent cascading failures

### Monitoring System
- Real-time metrics collection with time series support
- System resource monitoring (CPU, memory, disk)
- Sync operation tracking with detailed logs
- Health check endpoints for status verification

## Configuration

### Port Configuration
- The main Flask application MUST run on port 5000
- The SyncService MUST run on port 8000 to avoid conflicts

This separation allows independent scaling, updating, and management of each component while maintaining a unified API surface for clients.

## API Endpoints

### Gateway Endpoints (port 5000)
- `/` - Gateway information
- `/status` - System status information
- `/dashboard` - Redirects to dashboard UI
- `/api-docs` - Redirects to API documentation
- `/api/*` - Proxies all API requests to SyncService
- `/start-syncservice` - Manually starts SyncService if needed

### SyncService Endpoints (port 8000)
- `/` - SyncService information
- `/health/live` - Liveness probe
- `/health/ready` - Readiness probe
- `/health/status` - Detailed health status
- `/api/metrics` - System metrics
- `/api/system` - System information
- `/api/sync/operations` - Sync operations status
- `/api/sync/metrics` - Sync metrics
- `/api/sync/active` - Active sync operations
- `/api/config` - Service configuration

## Starting the Service

The system is designed to start automatically on initialization:

1. The API Gateway (Flask) starts first on port 5000
2. The Gateway automatically starts the SyncService on port 8000
3. The Gateway monitors the SyncService and restarts it if needed

### Important Note About Workflows

The system uses two different approaches to start and manage the SyncService:

1. **Primary Method (Recommended)**: The main application on port 5000 automatically starts, monitors, and manages the SyncService on port 8000. This happens through the `ensure_syncservice_running()` function in main.py.

2. **Secondary Method (Standalone)**: The "syncservice" workflow in .replit is configured to start the SyncService independently, but this method is currently facing port conflict issues and is not recommended.

For normal operation, you should only need to start the "Start application" workflow, as it will handle the SyncService automatically.

### Manual Control

You can manually restart or manage the SyncService:
- Using the API: `GET /start-syncservice`
- Using the command line: `python run_syncservice_direct.py`

The system will automatically handle port configurations to ensure the SyncService runs on port 8000.

## Additional Information

### Environment Variables
- `SYNC_SERVICE_API_KEY` - API key for protected endpoints (default: "dev-api-key")
- `SYNC_SERVICE_DB_URL` - Database URL for metrics and sync tracking
- `SYNC_SERVICE_PORT` - Always set to 8000

### System Requirements
- Python 3.7+
- PostgreSQL database
- FastAPI and Flask
- SQLAlchemy for database operations
- Required Python packages in pyproject.toml

### Logging
- Gateway logs to stdout
- SyncService logs with Python logging system
- Log level configurable via environment