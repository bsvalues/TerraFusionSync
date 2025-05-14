# GIS Export Plugin Implementation

This document provides implementation details for the GIS Export plugin in the TerraFusion Platform.

## Overview

The GIS Export plugin allows county users to export geospatial data in various formats. The plugin supports county-specific configurations, health monitoring via Prometheus metrics, and asynchronous background processing.

## Key Components

The GIS Export plugin consists of the following components:

1. **County Configuration** (`county_config.py`) - Manages county-specific settings such as available export formats, default coordinate systems, and maximum export area size
2. **Service Layer** (`service.py`) - Core business logic for creating, retrieving, and managing export jobs
3. **API Router** (`router.py`) - FastAPI router for the plugin's REST API endpoints
4. **Schemas** (`schemas.py`) - Pydantic models for request/response validation and serialization
5. **Metrics** (`metrics.py`) - Prometheus metrics for monitoring the plugin's performance and usage

## Database Models

The plugin uses the `GisExportJob` SQLAlchemy model defined in `terrafusion_sync.core_models`:

```python
class GisExportJob(Base):
    __tablename__ = "gis_export_jobs"
    
    job_id = Column(String, primary_key=True)
    county_id = Column(String, nullable=False)
    export_format = Column(String, nullable=False)
    status = Column(String, nullable=False)
    message = Column(String, nullable=True)
    area_of_interest_json = Column(JSON, nullable=False)
    layers_json = Column(JSON, nullable=False)
    parameters_json = Column(JSON, nullable=True)
    result_file_location = Column(String, nullable=True)
    result_file_size_kb = Column(Integer, nullable=True)
    result_record_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

## API Endpoints

The plugin exposes the following API endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/plugins/v1/gis-export/run` | Submit a new GIS export job |
| `GET` | `/plugins/v1/gis-export/status/{job_id}` | Check job status |
| `GET` | `/plugins/v1/gis-export/results/{job_id}` | Get job results |
| `POST` | `/plugins/v1/gis-export/cancel/{job_id}` | Cancel a job |
| `GET` | `/plugins/v1/gis-export/list` | List jobs with optional filtering |
| `GET` | `/plugins/v1/gis-export/formats/{county_id}` | Get supported formats for a county |
| `GET` | `/plugins/v1/gis-export/defaults/{county_id}` | Get default parameters for a county |
| `GET` | `/plugins/v1/gis-export/health` | Health check endpoint |

## County Configuration

The county configuration system allows each county to have its own set of:

1. Allowed export formats
2. Default coordinate system
3. Maximum export area size
4. Default simplification tolerance
5. Other export parameters

This configuration is loaded from county-specific JSON files at:
```
county_configs/{county_id}/{county_id}_config.json
```

If a county doesn't have a specific configuration, default values are used.

## Metrics

The plugin reports the following Prometheus metrics:

1. `gis_export_jobs_submitted_total` - Total number of submitted jobs
2. `gis_export_jobs_completed_total` - Total number of successfully completed jobs
3. `gis_export_jobs_failed_total` - Total number of failed jobs
4. `gis_export_processing_duration_seconds` - Processing time histogram
5. `gis_export_file_size_kb` - Result file size histogram
6. `gis_export_record_count` - Result record count histogram

These metrics are labeled with `county_id` and `export_format` for detailed analysis.

## Background Processing

The plugin uses FastAPI's `BackgroundTasks` to process export jobs asynchronously:

1. When a job is submitted, it's created with status `PENDING`
2. A background task is added to the request to process the job
3. The job status is updated to `RUNNING` when processing starts
4. After processing, the status is updated to `COMPLETED` or `FAILED`
5. Results (file location, size, record count) are stored in the job record

This allows the API to respond quickly while processing potentially large exports in the background.

## Error Handling

The plugin implements robust error handling:

1. Request validation through Pydantic models
2. Export format validation against county-specific allowed formats
3. Job status checks to prevent invalid operations
4. Detailed error messages in API responses
5. Error logging with appropriate severity levels
6. Error metrics for monitoring and alerting

## Testing

The plugin includes several test files:

1. `test_gis_export_county_config_standalone.py` - Tests county configuration functionality
2. `test_county_config_gis_export.py` - Integration tests between config and service
3. `tests/plugins/fixed_test_gis_export_end_to_end.py` - End-to-end API tests

## Documentation

The plugin's documentation includes:

1. `GIS_EXPORT_IMPLEMENTATION.md` (this file) - Implementation details
2. `docs/gis_export_county_configuration.md` - County configuration guide
3. `GIS_EXPORT_TEST_README.md` - Testing instructions
4. API documentation via FastAPI's automatic OpenAPI generation

## Future Enhancements

Planned enhancements include:

1. Support for more export formats (CSV, FileGDB, etc.)
2. Advanced area filtering options
3. Integration with county security and access controls
4. Caching of frequently requested exports
5. Rate limiting for resource-intensive exports

## Deployment Considerations

When deploying the plugin:

1. Ensure county configuration files are properly set up
2. Configure appropriate database access and permissions
3. Set up Prometheus scraping for the metrics endpoints
4. Ensure adequate storage for export files
5. Configure backup and retention policies for exports