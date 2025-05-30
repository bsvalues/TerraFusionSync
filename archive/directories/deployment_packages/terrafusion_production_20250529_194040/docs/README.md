# TerraFusion Platform

**Enterprise Geospatial Data Synchronization Platform**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)](https://fastapi.tiangolo.com/)

TerraFusion is a production-ready geospatial data synchronization platform designed for county-level property assessment and collection systems (PACS). It provides seamless integration with legacy systems while offering advanced AI-powered analytics, real-time data synchronization, and comprehensive district lookup capabilities.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Gateway   │    │   SyncService   │    │   PostgreSQL    │
│   (Flask:5000)  │◄──►│ (FastAPI:8080)  │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  District APIs  │    │ WebSocket APIs  │    │ Backup Service  │
│  AI Analytics   │    │ Real-time Sync  │    │ (Hourly Auto)   │
│  Vendor Access  │    │ Data Validation │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- PostgreSQL 16+ with PostGIS extension
- Node.js 20+ (for frontend development)
- Docker (optional, for containerized deployment)

### Environment Setup

1. **Clone and Navigate**
   ```bash
   git clone <repository-url>
   cd terrafusion-platform
   ```

2. **Install Dependencies**
   ```bash
   # Python dependencies
   pip install -r requirements.txt
   
   # Node.js dependencies (if using frontend)
   npm install
   ```

3. **Database Configuration**
   
   Set these environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost:5432/terrafusion"
   export PGHOST="localhost"
   export PGPORT="5432"
   export PGUSER="your_username"
   export PGPASSWORD="your_password"
   export PGDATABASE="terrafusion"
   export SESSION_SECRET="your-secret-key-here"
   ```

4. **Initialize Database**
   ```bash
   python -c "from app import db; db.create_all()"
   ```

### Running the Platform

#### Option 1: Using Replit (Recommended)
```bash
# Start API Gateway
python main.py

# In a separate terminal, start SyncService
python run_syncservice_workflow_8080.py
```

#### Option 2: Manual Startup
```bash
# Start API Gateway
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Start SyncService
cd syncservice && uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

#### Option 3: Docker Deployment
```bash
docker-compose up -d
```

### Verification

After startup, verify the services:

- **API Gateway**: http://localhost:5000/health
- **SyncService**: http://localhost:8080/health
- **Dashboard**: http://localhost:5000/dashboard

## 📡 API Reference

### Core Endpoints

#### Health and Status
```bash
GET /health                    # System health check
GET /api/status               # Detailed system status
GET /api/version              # Version information
```

#### District Lookup Service
```bash
# Lookup by coordinates
GET /api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090

# Lookup by address
GET /api/v1/district-lookup/address?address=123 Main St, Kennewick, WA

# List all districts
GET /api/v1/district-lookup/districts

# Get specific district info
GET /api/v1/district-lookup/districts/{type}/{id}
```

#### GIS Export Management
```bash
# List export jobs
GET /api/v1/gis-export/jobs

# Create new export job
POST /api/v1/gis-export/jobs
Content-Type: application/json
{
  "county_id": "benton_wa",
  "format": "shapefile",
  "filters": {...}
}

# Get job status
GET /api/v1/gis-export/jobs/{job_id}

# Download completed export
GET /api/v1/gis-export/jobs/{job_id}/download
```

#### AI Analytics
```bash
# Analyze GIS export
POST /api/v1/ai/analyze/gis-export
{
  "job_id": "export_123"
}

# Analyze property exemption
POST /api/v1/ai/analyze/exemption
{
  "parcel_id": "12345",
  "exemption_type": "homestead",
  "property_description": "Single family residence"
}

# AI service health
GET /api/v1/ai/health
```

### Public Vendor API

Secure API endpoints for authorized third-party vendors:

```bash
# Generate vendor access token
POST /api/public/v1/token
{
  "vendor_id": "certified_vendor_123",
  "county_id": "benton_wa"
}

# Access county data (requires token)
GET /api/public/v1/counties/{county_id}/parcels
Authorization: Bearer <jwt_token>

# Get district information
GET /api/public/v1/counties/{county_id}/districts
```

## 🗄️ Database Schema

### Core Tables

#### Users and Authentication
```sql
-- User management
users (id, username, email, password_hash, created_at, is_active)
roles (id, name, description, permissions)
user_roles (user_id, role_id, county_id)

-- Session management
user_sessions (id, user_id, token, expires_at, created_at)
```

#### Geographic Data
```sql
-- District boundaries
districts (id, type, name, boundary_geom, county_id, metadata)

-- Property records
parcels (id, parcel_number, owner_name, property_address, 
         assessment_value, coordinates, district_assignments)
```

#### Export and Processing
```sql
-- Export job tracking
export_jobs (id, user_id, status, parameters, created_at, 
             completed_at, file_path, error_message)

-- Sync operations
sync_operations (id, source_system, operation_type, status,
                record_count, started_at, completed_at)
```

## 🔧 Configuration

### County Configuration

Each county requires a configuration file in `county_configs/{county_name}/`:

```yaml
# benton_wa_config.yaml
county_id: benton_wa
county_name: "Benton County, WA"
legacy_system_type: "PACS_CAMA"
data_sources:
  - type: "property_records"
    connection: "postgresql://..."
    table_mapping: {...}
  - type: "district_boundaries"
    source: "geojson_files"
    path: "data/districts/"
```

### Environment Variables

#### Required Variables
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:port/db
PGHOST=localhost
PGPORT=5432
PGUSER=username
PGPASSWORD=password
PGDATABASE=terrafusion

# Security
SESSION_SECRET=your-secret-key
JWT_SECRET=your-jwt-secret

# Services
API_PORT=5000
SYNC_PORT=8080
WEBSOCKET_PORT=8081
```

#### Optional Variables
```bash
# AI Services
OPENAI_API_KEY=your-openai-key
NARRATOR_AI_ENDPOINT=http://localhost:8082
EXEMPTION_SEER_ENDPOINT=http://localhost:8083

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Backup
BACKUP_SCHEDULE=hourly
BACKUP_RETENTION_DAYS=30
```

## 🛡️ Security

### Authentication Methods

1. **JWT Tokens**: For API access and vendor authentication
2. **Session Cookies**: For web dashboard access
3. **API Keys**: For service-to-service communication

### Role-Based Access Control (RBAC)

```python
# User roles and permissions
ROLES = {
    'system_admin': ['*'],  # Full access
    'county_admin': ['county:*'],  # County-specific admin
    'assessor': ['property:read', 'property:write', 'export:create'],
    'analyst': ['property:read', 'export:read', 'report:create'],
    'vendor': ['api:public', 'data:read']  # Limited API access
}
```

### Data Protection

- **Encryption**: All data encrypted at rest and in transit
- **Access Logging**: Comprehensive audit trails
- **Input Validation**: Sanitization of all user inputs
- **Rate Limiting**: API throttling and abuse prevention

## 📊 Monitoring and Observability

### Health Checks

The platform provides comprehensive health monitoring:

```bash
# Basic health check
curl http://localhost:5000/health

# Detailed system status
curl http://localhost:5000/api/status

# Service-specific health
curl http://localhost:8080/health  # SyncService
curl http://localhost:5000/api/v1/ai/health  # AI Services
```

### Metrics and Logging

- **Application Logs**: Structured JSON logging with correlation IDs
- **Performance Metrics**: Response times, throughput, error rates
- **Business Metrics**: Export volumes, user activity, data sync status
- **Infrastructure Metrics**: CPU, memory, disk usage, database performance

### Backup System

Automated backup system with the following features:

- **Schedule**: Hourly automated backups
- **Compression**: Gzip compression for storage efficiency
- **Retention**: Configurable retention policies
- **Monitoring**: Backup success/failure tracking
- **Recovery**: Point-in-time recovery capabilities

```bash
# Manual backup operations
python backup_utilities.py backup
python backup_utilities.py restore <backup_file>
python backup_utilities.py list
```

## 🧪 Testing

### Running Tests

```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# API tests
python -m pytest tests/api/

# Performance tests
python -m pytest tests/performance/
```

### Test Coverage

The platform maintains comprehensive test coverage:

- **Unit Tests**: Core business logic and utilities
- **Integration Tests**: Database operations and external services
- **API Tests**: All endpoint functionality and security
- **Performance Tests**: Load testing and benchmarking

## 🚀 Deployment

### Production Deployment

#### Azure App Service (Recommended)
```bash
# Deploy using Azure CLI
az webapp up --name terrafusion-prod --resource-group terrafusion-rg

# Configure environment variables
az webapp config appsettings set --name terrafusion-prod \
  --settings DATABASE_URL="..." SESSION_SECRET="..."
```

#### Docker Deployment
```bash
# Build and deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose scale syncservice=3
```

#### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set up system service
sudo systemctl enable terrafusion-api
sudo systemctl enable terrafusion-sync

# Start services
sudo systemctl start terrafusion-api
sudo systemctl start terrafusion-sync
```

### Environment-Specific Configuration

#### Development
- Debug mode enabled
- Hot reloading
- Verbose logging
- Local database

#### Staging
- Production-like configuration
- Limited data sets
- Integration testing
- SSL certificates

#### Production
- Optimized performance
- High availability setup
- Comprehensive monitoring
- Automated backups

## 🔧 Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -c "from app import db; print(db.engine.execute('SELECT 1').scalar())"

# Verify environment variables
echo $DATABASE_URL
```

#### Service Startup Problems
```bash
# Check port availability
netstat -tulpn | grep :5000
netstat -tulpn | grep :8080

# Review logs
tail -f logs/api-gateway.log
tail -f logs/syncservice.log
```

#### Performance Issues
```bash
# Monitor resource usage
htop
iostat -x 1

# Check database performance
psql -c "SELECT * FROM pg_stat_activity;"
```

### Debug Mode

Enable debug mode for detailed error information:

```bash
export FLASK_DEBUG=1
export FLASK_ENV=development
python main.py
```

## 📚 Documentation

### Additional Resources

- **API Documentation**: Available at `/api/docs` when running
- **Architecture Guide**: See `docs/architecture.md`
- **Deployment Guide**: See `docs/deployment.md`
- **Security Guide**: See `docs/security.md`
- **County Integration Guide**: See `docs/county_integration.md`

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

For support and questions:

- **Documentation**: Check the `docs/` directory
- **Issues**: Create an issue in the repository
- **Discussions**: Use the repository discussions
- **Email**: Contact the development team

## 🏆 Acknowledgments

- **Benton County, WA**: Primary pilot implementation
- **Open Source Community**: Flask, FastAPI, and PostgreSQL communities
- **Contributors**: All developers who have contributed to this project

---

**Made with ❤️ for county governments worldwide**