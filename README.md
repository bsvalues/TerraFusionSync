# TerraFusion SyncService

A sophisticated SyncService platform for enterprise data migration, designed to enable seamless integration across diverse system architectures with advanced monitoring and adaptive synchronization capabilities.

## Architecture Overview

The TerraFusion SyncService uses a two-tier microservice architecture:

1. **API Gateway (Flask, port 5000):**
   - Main entry point for all client requests
   - Handles authentication and routing
   - Proxies API requests to the SyncService
   - Provides auto-recovery of the SyncService if it stops
   - Status monitoring and management endpoints

2. **SyncService (FastAPI, port 8080):**
   - Core business logic for synchronization
   - Implements change detection, transformation, validation
   - Provides detailed metrics and monitoring
   - Self-healing capabilities for failed syncs
   - Handles direct database interactions

## Communication Flow

```
Client -> API Gateway (port 5000) -> SyncService (port 8080) -> External Systems
```

## Key Features

- **Multi-system Integration**: Connect and synchronize data between PACS, CAMA, GIS, ERP, and CRM systems
- **Incremental and Full Sync**: Support for both full data transfers and efficient incremental updates
- **Real-time Monitoring**: Comprehensive metrics and health monitoring for all components
- **Self-healing Capabilities**: Automatic recovery from failures and connection issues
- **Defensive Programming**: Robust error handling with fallbacks at every level

## Component Details

### API Gateway

Built using Flask, provides a unified API surface for all clients. Features include:

- Status monitoring and health checks
- Service discovery and routing
- Authentication and API key management
- Database access for configuration and operations history
- Dashboard UI for monitoring sync operations

### SyncService

Built using FastAPI, implements the core business logic for data synchronization:

- Incremental and full sync operations
- Change detection and differential updates
- Data transformation and mapping
- System resource monitoring
- Error recovery and retry mechanisms

## Setup and Configuration

### Requirements

- Python 3.11+
- PostgreSQL database
- Dependencies as listed in `pyproject.toml`

### Environment Variables

The following environment variables are required:

- `DATABASE_URL`: PostgreSQL connection string
- `SYNCSERVICE_API_KEY`: API key for SyncService authentication

### Installation

1. Clone the repository
2. Install dependencies: `pip install -e .`
3. Set up the database: `flask db upgrade`
4. Start the services:
   - API Gateway: `gunicorn --bind 0.0.0.0:5000 main:app`
   - SyncService: `cd apps/backend/syncservice && uvicorn syncservice.main:app --host 0.0.0.0 --port 8080`

## API Documentation

### API Gateway Endpoints

- `GET /`: Root endpoint providing API information
- `GET /dashboard`: Dashboard UI for monitoring
- `GET /api/status`: API status and component health
- `GET /api/sync-pairs`: List of configured sync pairs
- `GET /api/sync-operations`: History of sync operations

### SyncService Endpoints

- `GET /health`: Health check endpoint
- `POST /api/sync/full`: Start a full sync operation
- `POST /api/sync/incremental`: Start an incremental sync operation
- `GET /api/sync/operations`: List active and completed operations
- `GET /api/metrics/system`: System metrics and performance data

## Development

### Project Structure

```
terrafusion/
├── apps/
│   ├── backend/
│   │   ├── api/         # API Gateway code
│   │   └── syncservice/ # SyncService code
│   └── frontend/        # Dashboard UI
├── libs/
│   └── shared/          # Shared utilities
├── docs/                # Documentation
└── tests/               # Test cases
```

### Testing

Run tests with: `pytest tests/`

## Troubleshooting

- **API Gateway can't connect to SyncService**: Ensure SyncService is running on port 8080
- **Database errors**: Check the DATABASE_URL environment variable
- **SyncService crashes**: Check system monitoring logs for resource issues

## License

MIT License