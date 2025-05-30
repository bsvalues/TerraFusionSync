# TerraFusion SyncService Platform Documentation

**Version:** 1.0.0  
**Date:** April 28, 2025  
**Prepared by:** DevOps Team

## 1. System Architecture

### 1.1 Overview

The TerraFusion SyncService platform is designed as a robust, enterprise-grade data synchronization solution with a two-tier microservice architecture:

1. **API Gateway (Flask, port 5000)**
   - Main entry point for all client requests
   - Handles authentication and routing
   - Proxies API requests to the SyncService
   - Provides auto-recovery of the SyncService if it stops
   - Status monitoring and management endpoints

2. **SyncService (FastAPI, port 8080)**
   - Core business logic for synchronization
   - Implements change detection, transformation, validation
   - Provides detailed metrics and monitoring
   - Self-healing capabilities for failed syncs
   - Handles direct database interactions

### 1.2 Communication Flow

```
Client -> API Gateway (port 5000) -> SyncService (port 8080) -> External Systems
```

### 1.3 Database Schema

The system uses PostgreSQL database with the following primary tables:

- `system_metrics`: Stores performance metrics
- `audit_entries`: Tracks all system events and changes
- `sync_operations`: Records of sync operations
- `sync_pairs`: Configuration of synchronization pairs

## 2. Environment Configuration

### 2.1 Required Environment Variables

The system relies on the following environment variables:

```
DATABASE_URL=postgresql://<user>:<password>@<host>:<port>/<db_name>
PGHOST=<postgres_host>
PGPORT=<postgres_port>
PGUSER=<postgres_user>
PGPASSWORD=<postgres_password>
PGDATABASE=<postgres_database>
```

### 2.2 Port Configuration

- API Gateway: 5000
- SyncService: 8080

### 2.3 Workflows

1. **Start application**: `gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app`
2. **syncservice**: `python run_syncservice_workflow_8080.py`

Both workflows must be running for the system to operate correctly.

## 3. Operational Procedures

### 3.1 Starting the System

To start the system:

1. Start the SyncService workflow first:
   ```
   replit workflow start syncservice
   ```

2. Then start the API Gateway workflow:
   ```
   replit workflow start "Start application"
   ```

### 3.2 Stopping the System

To stop the system:

1. Stop the API Gateway workflow:
   ```
   replit workflow stop "Start application"
   ```

2. Then stop the SyncService workflow:
   ```
   replit workflow stop syncservice
   ```

### 3.3 Monitoring the System

Key monitoring endpoints:

- System Status: `http://localhost:5000/api/status`
- Health Check: `http://localhost:8080/health`
- System Metrics: `http://localhost:8080/metrics`
- Audit Summary: `http://localhost:5000/api/audit/summary`

### 3.4 Database Backup and Restore

Use the `backup_utilities.py` script:

```
python backup_utilities.py backup
python backup_utilities.py restore <backup_file>
python backup_utilities.py list
```

### 3.5 Service Recovery

Use the `service_recovery.py` script:

```
python service_recovery.py check
python service_recovery.py restart-api
python service_recovery.py restart-sync
python service_recovery.py restart-all
```

## 4. Maintenance Procedures

### 4.1 Regular Maintenance Tasks

Use the `maintenance_schedule.py` script:

```
python maintenance_schedule.py run --type weekly
python maintenance_schedule.py run --type monthly
python maintenance_schedule.py run --type quarterly
```

### 4.2 Maintenance Schedule

- **Weekly**: Sundays at 01:00
  - Update packages
  - Clean logs
  - Backup database

- **Monthly**: 1st day of each month at 02:00
  - Optimize database
  - Check disk space
  - Rotate logs

- **Quarterly**: 15th of Jan, Apr, Jul, Oct at 03:00
  - Performance review
  - Security audit
  - Update documentation

### 4.3 Performance Tuning

Use the `performance_tuning.py` script:

```
python performance_tuning.py optimize-all
python performance_tuning.py optimize-db
python performance_tuning.py optimize-api
python performance_tuning.py optimize-sync
python performance_tuning.py test --endpoint http://localhost:5000/api/status
```

## 5. Security Configuration

### 5.1 Authentication

The system uses a configurable authentication system defined in `security_config.py`.

In production, enable the authentication by setting:
```python
AUTH_CONFIG = {
    "auth_required": True,
    ...
}
```

### 5.2 API Security

- Enable HTTPS for all communications
- Implement API rate limiting
- Restrict CORS configuration to specific origins
- Use proper role definitions

### 5.3 Audit Logging

All system events are logged in the audit trail. You can view the audit summary at:
```
http://localhost:5000/api/audit/summary
```

## 6. Disaster Recovery

### 6.1 Recovery Procedures

Use the `disaster_recovery.py` script:

```
python disaster_recovery.py recover [--backup <backup_file>]
python disaster_recovery.py fix-corruption <entity_type> [--validation <script>]
python disaster_recovery.py create-plan <issue_type> [--components <component_list>]
```

### 6.2 Recovery Plans

The system includes pre-defined recovery plans for:

- Service outages
- Data corruption
- Complete system failure

Recovery plans are generated in the `recovery_scripts` directory.

## 7. Monitoring Configuration

### 7.1 Monitored Metrics

- CPU Usage (alert threshold: >80%)
- Memory Usage (alert threshold: >80%)
- Disk Usage (alert threshold: >85%)
- Service Response Time (alert threshold: >500ms)
- Failed Sync Operations (alert threshold: >5 in 1 hour)
- Service Restarts (alert threshold: >3 in 24 hours)

### 7.2 Log Management

- Log files are stored in the `logs` directory
- Log rotation is configured for 7-day retention
- Centralized logging is implemented for both services

## 8. Troubleshooting Guide

### 8.1 Common Issues

#### API Gateway not responding
1. Check if the workflow is running
2. Verify port 5000 is available
3. Check logs for errors
4. Restart using `python service_recovery.py restart-api`

#### SyncService not responding
1. Check if the workflow is running
2. Verify port 8080 is available
3. Check logs for errors
4. Restart using `python service_recovery.py restart-sync`

#### Database connectivity issues
1. Verify PostgreSQL service is running
2. Check environment variables
3. Test connection using PostgreSQL client
4. Review database logs

### 8.2 Log Analysis

Key log patterns to look for:
- "Error starting SyncService" - Indicates startup failure
- "Failed to get metrics from SyncService" - Communication issues
- "Failed to restart SyncService after X attempts" - Recovery system failure
- "CPU/Memory/Disk usage above threshold" - Resource constraints

## 9. Change Management

All changes to the system should follow this process:

1. Document the proposed change
2. Create a backup before making changes
3. Test the change in isolation if possible
4. Implement the change
5. Verify system health and functionality
6. Document the change in the maintenance log

## 10. Support Information

For issues with the TerraFusion SyncService platform, contact:

- **DevOps Team**: devops@example.com
- **System Administrator**: sysadmin@example.com
- **Database Administrator**: dba@example.com

## 11. Appendix

### 11.1 Key Files and Their Purposes

| File | Purpose |
|------|---------|
| `main.py` | Main entry point for the Flask API Gateway |
| `app.py` | Core implementation of the API Gateway |
| `syncservice.py` | Implementation of the FastAPI SyncService |
| `run_syncservice_workflow_8080.py` | Script to run the SyncService on port 8080 for workflow |
| `models.py` | Database models for metrics and audit logs |
| `manual_fix_system_monitoring.py` | Robust system monitoring implementation |
| `backup_utilities.py` | Database backup and recovery utilities |
| `service_recovery.py` | Service recovery procedures |
| `performance_tuning.py` | Performance optimization utilities |
| `disaster_recovery.py` | Disaster recovery procedures |
| `maintenance_schedule.py` | Maintenance scheduling and execution |
| `security_config.py` | Security configuration |
| `logging_config.py` | Logging configuration |
| `monitoring_config.py` | Monitoring configuration |

### 11.2 API Endpoints

#### API Gateway Endpoints

- `GET /api/status` - System status
- `GET /api/sync-pairs` - List sync pairs
- `GET /api/sync-pairs/<id>` - Get sync pair details
- `GET /api/sync-operations` - List sync operations
- `POST /api/sync-operations` - Start a new sync operation
- `GET /api/metrics` - Get system metrics
- `GET /api/audit` - Get audit entries
- `GET /api/audit/summary` - Get audit summary

#### SyncService Endpoints

- `GET /health` - Health check
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /metrics` - System metrics
- `GET /systems` - Available systems for synchronization
- `GET /sync-pairs` - Configured sync pairs
- `POST /sync/<pair_id>/start` - Start a sync operation