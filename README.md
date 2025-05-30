# TerraFusion Platform v2.0

Enterprise-grade geospatial data synchronization platform designed for county government operations. TerraFusion provides seamless integration of legacy assessment systems with modern AI-powered analytics and citizen-facing services.

## 🏛️ Built for County Government

TerraFusion addresses the unique challenges of county-level operations:
- **Property Assessment Integration**: Connect PACS, CAMA, and Tyler Technologies systems
- **GIS Data Management**: Multi-format export and spatial analysis capabilities
- **AI-Powered Insights**: Fraud detection and exemption analysis
- **Citizen Services**: Self-service district lookup and property information
- **Regulatory Compliance**: Built-in audit trails and security controls

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- 4GB RAM (8GB recommended)
- Modern web browser

### Installation

1. **Clone and Setup**
```bash
git clone https://github.com/your-org/terrafusion-platform.git
cd terrafusion-platform
```

2. **Environment Configuration**
```bash
# Create environment file
cp .env.example .env

# Required environment variables:
DATABASE_URL=postgresql://user:password@localhost/terrafusion
SESSION_SECRET=your-secure-session-key
```

3. **Database Setup**
```bash
# Initialize database tables
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

4. **Start Services**
```bash
# Main application (Port 5000)
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Sync service (Port 8080)
python run_syncservice_workflow_8080.py
```

5. **Access Dashboard**
Open http://localhost:5000/dashboard in your web browser

## 🎯 Core Features

### GIS Data Export
Export property and boundary data in multiple formats:
- **Shapefile**: Industry-standard GIS format
- **GeoJSON**: Web-friendly JSON format
- **KML**: Google Earth compatible
- **GeoPackage**: Modern SQLite-based format
- **CSV**: Tabular data with coordinates

```bash
# API Example
curl -X POST http://localhost:5000/api/v1/gis-export/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "county_id": "benton_wa",
    "username": "analyst@county.gov",
    "export_format": "shapefile",
    "area_of_interest": {"type": "Polygon", "coordinates": [...]},
    "layers": ["parcels", "zoning", "roads"]
  }'
```

### District Lookup Service
Find administrative boundaries by address or coordinates:

```bash
# Address lookup
curl "http://localhost:5000/api/v1/district-lookup/address?address=123 Main St, Kennewick, WA"

# Coordinate lookup
curl "http://localhost:5000/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090"
```

### AI-Powered Analysis
Leverage artificial intelligence for data insights:
- **Exemption Analysis**: Fraud detection and compliance checking
- **Data Quality Assessment**: Automated validation and recommendations
- **Narrative Generation**: Human-readable summaries of complex data

## 🏗️ Architecture

### Backend Services
- **Flask API Gateway** (Port 5000): Main application and web interface
- **FastAPI Sync Service** (Port 8080): Legacy system integration and data processing
- **PostgreSQL Database**: Spatial data storage with PostGIS extension
- **Ollama AI Engine**: Local AI processing for secure government environments

### Frontend Components
- **Bootstrap 5**: Responsive, accessible government UI
- **Leaflet Maps**: Interactive mapping with county data
- **Chart.js**: Data visualization and analytics
- **Progressive Enhancement**: Works without JavaScript for core functions

### Security Features
- **Role-Based Access Control**: County-level data isolation
- **JWT Authentication**: Secure API access with token rotation
- **Audit Logging**: Complete activity tracking for compliance
- **TLS Encryption**: All data encrypted in transit

## 📊 Database Schema

### Core Tables
```sql
-- User management
users: id, username, email, password_hash, created_at, active

-- County configuration
counties: id, county_code, county_name, state_code, created_at

-- Export job tracking
export_jobs: id, job_id, county_id, username, export_format, status, 
            created_at, completed_at, file_path, error_message

-- Sync operation audit
sync_operations: id, operation_id, county_id, operation_type, status,
                records_processed, created_at, completed_at, error_message
```

### Indexes and Performance
- Foreign key indexes on all relationship columns
- Spatial indexes on geographic data (PostGIS)
- Composite indexes on frequently queried combinations
- Connection pooling with automatic health checks

## 🔧 Configuration

### Application Settings
```python
# app.py configuration
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
SQLALCHEMY_ENGINE_OPTIONS = {
    "pool_recycle": 300,        # Connection recycling
    "pool_pre_ping": True,      # Health check queries
}
```

### County-Specific Configuration
Each county requires a configuration file in `county_configs/`:
```json
{
  "county_code": "benton_wa",
  "county_name": "Benton County",
  "state_code": "WA",
  "districts": {
    "voting_precincts": {...},
    "fire_districts": {...},
    "school_districts": {...}
  }
}
```

## 🔌 API Integration

### Authentication
All API requests require JWT authentication:
```bash
# Login to get token
curl -X POST http://localhost:5000/api/v1/rbac/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user@county.gov", "password": "secure_password"}'

# Use token in requests
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:5000/api/v1/gis-export/jobs
```

### Rate Limiting
- **Public endpoints**: 100 requests/minute
- **Authenticated endpoints**: 1000 requests/minute
- **Export operations**: 10 concurrent jobs per user

### Error Handling
Standard HTTP status codes with JSON error responses:
```json
{
  "error": "Validation failed",
  "message": "Missing required field: county_id",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🚀 Deployment

### Production Environment
```dockerfile
# Dockerfile
FROM python:3.11-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "main:app"]
```

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/terrafusion
SESSION_SECRET=cryptographically-secure-key

# Optional
OLLAMA_BASE_URL=http://localhost:11434
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

### Health Checks
```bash
# Application health
curl http://localhost:5000/health

# Sync service health
curl http://localhost:8080/health

# Database connectivity
curl http://localhost:5000/api/v1/gis-export/jobs?limit=1
```

## 🧪 Testing

### Unit Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Test specific module
python -m pytest tests/test_gis_export.py -v

# Coverage report
python -m pytest --cov=app tests/
```

### API Testing
```bash
# Test GIS export functionality
curl -X POST http://localhost:5000/api/v1/gis-export/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @tests/fixtures/sample_export_request.json

# Test district lookup
curl "http://localhost:5000/api/v1/district-lookup/coordinates?lat=46.230&lon=-119.090"
```

### Load Testing
```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:5000
```

## 📝 Development

### Code Style
- **Python**: PEP 8 with Black formatter
- **HTML/CSS**: Bootstrap conventions
- **JavaScript**: ES6+ with Prettier
- **SQL**: Consistent naming and formatting

### Git Workflow
```bash
# Feature development
git checkout -b feature/new-export-format
git commit -m "feat: add GeoPackage export support"
git push origin feature/new-export-format

# Create pull request for review
```

### Database Migrations
```bash
# Create migration
python manage.py db init
python manage.py db migrate -m "Add new table"
python manage.py db upgrade
```

## 🛡️ Security

### Data Protection
- **Encryption**: TLS 1.3 for data in transit, AES-256 for data at rest
- **Access Control**: Role-based permissions with county isolation
- **Audit Trail**: Complete logging of all data access and modifications
- **Session Security**: Secure cookies with CSRF protection

### Compliance Features
- **FISMA**: Federal Information Security Management Act
- **SOC 2**: Service Organization Control 2 compliance
- **WCAG 2.1**: Web Content Accessibility Guidelines
- **Open Records**: Public information access capabilities

## 📞 Support

### Documentation
- **API Reference**: See `api_documentation.json` for complete OpenAPI spec
- **Component Library**: See `bootstrap_components.json` for UI components
- **Architecture Guide**: See `terrafusion_architecture_analysis.md`

### Troubleshooting

**Database Connection Issues**
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT version();"

# Verify PostGIS extension
psql $DATABASE_URL -c "SELECT PostGIS_version();"
```

**Performance Issues**
```bash
# Check database query performance
psql $DATABASE_URL -c "SELECT query, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Monitor application metrics
curl http://localhost:5000/health
```

**Export Failures**
```bash
# Check export job status
curl http://localhost:5000/api/v1/gis-export/jobs/JOB_ID

# Review application logs
tail -f logs/terrafusion.log
```

### Getting Help
- **Technical Issues**: Check application logs and database connectivity
- **Feature Requests**: Submit detailed requirements with use cases
- **Security Concerns**: Follow responsible disclosure procedures
- **Integration Support**: Provide system specifications and connection details

## 📄 License

Government Open Source License - designed for public sector use with transparency requirements and citizen access provisions.

## 🚀 What's Next

### Planned Features
- **Mobile Applications**: Native iOS/Android apps for field operations
- **Real-time Notifications**: WebSocket-based live updates
- **Advanced Analytics**: Machine learning for predictive insights
- **Multi-language Support**: Spanish and other local languages

### Integration Roadmap
- **Cloud Deployment**: AWS/Azure/GCP deployment guides
- **Enterprise SSO**: SAML/OAuth integration with government identity providers
- **API Ecosystem**: Third-party developer platform and SDK
- **Monitoring Suite**: Comprehensive observability and alerting

---

**TerraFusion Platform v2.0** - Empowering counties with modern geospatial technology while maintaining the security and reliability required for government operations.