# GIS Export Plugin

This plugin provides GIS (Geographic Information System) export functionality for the TerraFusion SyncService platform. It allows users to export geographic data in various formats with customizable parameters.

## Features

- Export geographic data in multiple formats (GeoJSON, Shapefile, etc.)
- Define area of interest by coordinates, boundaries, or features
- Select specific layers for export
- Customize export parameters
- Asynchronous job processing
- Comprehensive job status tracking
- Job management (list, cancel, results)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/plugins/v1/gis-export/run` | POST | Submit a new export job |
| `/plugins/v1/gis-export/status/{job_id}` | GET | Get the status of a specific job |
| `/plugins/v1/gis-export/list` | GET | List all export jobs |
| `/plugins/v1/gis-export/cancel/{job_id}` | POST | Cancel a running job |
| `/plugins/v1/gis-export/health` | GET | Health check endpoint |
| `/plugins/v1/gis-export/metrics` | GET | Prometheus metrics endpoint |

## Usage

### Submit an Export Job

```python
import requests
import json

export_job = {
    "export_format": "GeoJSON",
    "county_id": "EXAMPLE_COUNTY",
    "area_of_interest": {
        "type": "bbox",
        "coordinates": [-120.5, 46.0, -120.0, 46.5]
    },
    "layers": ["parcels", "zoning"],
    "parameters": {
        "include_assessment_data": True,
        "simplify_geometries": True
    }
}

response = requests.post(
    "http://localhost:8080/plugins/v1/gis-export/run",
    json=export_job
)

job_id = response.json()["job_id"]
print(f"Job submitted with ID: {job_id}")
```

### Check Job Status

```python
import requests

job_id = "your-job-id"
response = requests.get(
    f"http://localhost:8080/plugins/v1/gis-export/status/{job_id}"
)

status = response.json()
print(f"Job status: {status['status']}")
print(f"Message: {status['message']}")
```

### List Jobs

```python
import requests

response = requests.get(
    "http://localhost:8080/plugins/v1/gis-export/list",
    params={
        "county_id": "EXAMPLE_COUNTY",
        "status": "COMPLETED",
        "limit": 10
    }
)

jobs = response.json()
print(f"Found {len(jobs)} jobs")
for job in jobs:
    print(f"Job {job['job_id']}: {job['status']}")
```

### Cancel a Job

```python
import requests

job_id = "your-job-id"
response = requests.post(
    f"http://localhost:8080/plugins/v1/gis-export/cancel/{job_id}"
)

result = response.json()
print(f"Job cancelled: {result['status']}")
```

## Job Statuses

- `PENDING`: Job is queued and waiting to be processed
- `RUNNING`: Job is currently being processed
- `COMPLETED`: Job has completed successfully
- `FAILED`: Job has failed
- `CANCELLED`: Job was cancelled by the user

## Metrics

The plugin provides the following Prometheus metrics:

- `gis_export_jobs_submitted_total`: Counter for submitted jobs
- `gis_export_jobs_completed_total`: Counter for completed jobs
- `gis_export_jobs_failed_total`: Counter for failed jobs
- `gis_export_processing_duration_seconds`: Histogram for job processing time
- `gis_export_file_size_kb`: Histogram for exported file sizes
- `gis_export_record_count`: Histogram for number of records in exports

All metrics include labels for `county_id` and `export_format` to enable filtering and aggregation.

## Custom Metrics Registry

To avoid conflicts with other plugins, this plugin uses a custom Prometheus registry when the `GIS_EXPORT_USE_CUSTOM_REGISTRY` environment variable is set to `1`. This prevents duplicate metric errors when multiple plugins define metrics with similar names.

### Example:

```python
from terrafusion_sync.plugins.gis_export.metrics import GisExportMetrics

# Initialize with custom registry
GisExportMetrics.initialize(use_default_registry=False)

# Track job submission
GisExportMetrics.jobs_submitted.labels(
    county_id="EXAMPLE_COUNTY",
    export_format="GeoJSON",
    status_on_submit="PENDING"
).inc()
```

## Architecture

The plugin follows the standard architecture pattern:

- **Model**: Defines the database schema for GIS export jobs
- **Schema**: Defines the API request/response models
- **Router**: Handles HTTP requests and routes them to services
- **Service**: Contains business logic for processing exports
- **Tasks**: Background processing of export jobs
- **Metrics**: Prometheus metrics for monitoring