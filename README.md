# TerraFusion SyncService Platform

A sophisticated enterprise data synchronization platform that enables intelligent, scalable data migration across complex system landscapes.

## Overview

TerraFusion SyncService is a robust, enterprise-grade data synchronization platform built with a microservice architecture. It provides intelligent data migration capabilities between various systems with advanced monitoring, logging, and recovery features.

## Architecture

The system uses a two-tier microservice architecture:

1. **API Gateway (Flask, port 5000)**
   - Main entry point for all client requests
   - Handles authentication and routing
   - Provides auto-recovery and health monitoring

2. **SyncService (FastAPI, port 8080)**
   - Core business logic for synchronization
   - Implements change detection and validation
   - Exposes detailed metrics and health endpoints
   - Plugin-based architecture for extensibility

## Key Features

- **Intelligent Sync Workflows**: Customizable sync operations with incremental and full sync modes
- **Report Generation**: Comprehensive report generation and management through the Reporting Plugin
- **Advanced Monitoring**: Comprehensive metrics collection and visualization
- **Auto-recovery**: Self-healing capabilities that automatically restart failed components
- **Audit Logging**: Complete audit trail of all operations for compliance and debugging
- **CDC Reconciliation**: Change Data Capture with stale process detection and recovery
- **Performance Tuning**: Optimized database access and connection pooling
- **Disaster Recovery**: Built-in backup, restore, and recovery procedures
- **Scheduled Maintenance**: Automated maintenance tasks on regular schedules
- **Security**: Configurable authentication, rate limiting, and security controls

## Getting Started

### Prerequisites

- PostgreSQL database
- Python 3.8+
- Required Python packages (installed via the package manager)

### Starting the Application

The application uses two workflows:

1. Start the SyncService:
   ```
   replit workflow start syncservice
   ```

2. Start the API Gateway:
   ```
   replit workflow start "Start application"
   ```

### Verifying the Installation

After starting the application, you can verify it's working by:

1. Checking the status endpoint:
   ```
   curl http://localhost:5000/api/status
   ```

2. Checking the health endpoint:
   ```
   curl http://localhost:8080/health
   ```

## Key Utilities

The platform includes several utility scripts for operations, maintenance, and recovery:

- **service_recovery.py**: Service recovery procedures
- **backup_utilities.py**: Database backup and restore
- **performance_tuning.py**: Performance optimization utilities
- **disaster_recovery.py**: Disaster recovery procedures
- **maintenance_schedule.py**: Scheduled maintenance tasks
- **monitoring_service.py**: Monitoring and alerting

## Documentation

Detailed documentation is available in the `docs` directory:

- [System Documentation](docs/system_documentation.md): Comprehensive system documentation
- [CI Reporting Tests](docs/ci_reporting_tests.md): Guide for Reporting Plugin CI integration
- Recovery plans are automatically generated in the `recovery_scripts` directory
- Maintenance reports are created in the `maintenance_scripts` directory

## Monitoring

Key monitoring endpoints:

- System Status: `http://localhost:5000/api/status`
- Health Check: `http://localhost:8080/health`
- System Metrics: `http://localhost:8080/metrics`
- Audit Summary: `http://localhost:5000/api/audit/summary`

## Testing

The platform includes comprehensive test coverage:

- Unit tests: `pytest terrafusion_platform/tests/unit`
- Integration tests: `pytest terrafusion_platform/tests/integration`
- Reporting Plugin tests:
  - Integration tests: `pytest tests/plugins/test_reporting.py -m "integration"`
  - Stale reports test: `python test_stale_reports.py`
  - Metrics verification: `python test_reporting_metrics.py`

CI/CD automation is configured in `.github/workflows` to run all tests on every PR and merge.

## License

Copyright (c) 2025 TerraFusion. All rights reserved.