# GIS Export Plugin

The GIS Export plugin provides functionality for exporting geographic data from the TerraFusion platform in various formats suitable for use in GIS applications. This plugin is part of the TerraFusion SyncService and follows the same architectural patterns as other plugins.

## Features

- Export property data in multiple GIS formats (GeoJSON, Shapefile, KML)
- Area of interest filtering (bounding box, polygon)
- Layer selection for including specific data types
- Asynchronous job processing with status tracking
- Support for filtering and listing export jobs
- Cancellation of in-progress export jobs

## API Endpoints

### Submit Export Job

```
POST /plugins/v1/gis-export/run
```

Request body:
```json
{
  "export_format": "GeoJSON",
  "county_id": "COUNTY01",
  "area_of_interest": {
    "type": "bbox",
    "coordinates": [-120.5, 46.0, -120.0, 46.5]
  },
  "layers": ["parcels", "zoning"],
  "parameters": {
    "include_assessment_data": true,
    "simplify_geometries": true
  }
}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "export_format": "GeoJSON",
  "county_id": "COUNTY01",
  "status": "PENDING",
  "message": "GIS export job accepted and queued for processing.",
  "parameters": {
    "area_of_interest": {
      "type": "bbox",
      "coordinates": [-120.5, 46.0, -120.0, 46.5]
    },
    "layers": ["parcels", "zoning"],
    "include_assessment_data": true,
    "simplify_geometries": true
  },
  "created_at": "2025-05-13T12:34:56.789Z",
  "updated_at": "2025-05-13T12:34:56.789Z",
  "started_at": null,
  "completed_at": null
}
```

### Check Job Status

```
GET /plugins/v1/gis-export/status/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "export_format": "GeoJSON",
  "county_id": "COUNTY01",
  "status": "RUNNING",
  "message": "GIS export job is being processed.",
  "parameters": { ... },
  "created_at": "2025-05-13T12:34:56.789Z",
  "updated_at": "2025-05-13T12:35:00.123Z",
  "started_at": "2025-05-13T12:35:00.123Z",
  "completed_at": null
}
```

### Get Job Results

```
GET /plugins/v1/gis-export/results/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "export_format": "GeoJSON",
  "county_id": "COUNTY01",
  "status": "COMPLETED",
  "message": "GIS export completed successfully.",
  "parameters": { ... },
  "created_at": "2025-05-13T12:34:56.789Z",
  "updated_at": "2025-05-13T12:36:30.456Z",
  "started_at": "2025-05-13T12:35:00.123Z",
  "completed_at": "2025-05-13T12:36:30.456Z",
  "result": {
    "result_file_location": "/gis_exports/COUNTY01/550e8400-e29b-41d4-a716-446655440000_parcels_zoning.geojson",
    "result_file_size_kb": 5120,
    "result_record_count": 2500
  }
}
```

### List Jobs

```
GET /plugins/v1/gis-export/list?county_id=COUNTY01&export_format=GeoJSON&status=COMPLETED&limit=20&offset=0
```

Response:
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "export_format": "GeoJSON",
    "county_id": "COUNTY01",
    "status": "COMPLETED",
    "message": "GIS export completed successfully.",
    "parameters": { ... },
    "created_at": "2025-05-13T12:34:56.789Z",
    "updated_at": "2025-05-13T12:36:30.456Z",
    "started_at": "2025-05-13T12:35:00.123Z",
    "completed_at": "2025-05-13T12:36:30.456Z"
  },
  ...
]
```

### Cancel Job

```
POST /plugins/v1/gis-export/cancel/{job_id}
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "export_format": "GeoJSON",
  "county_id": "COUNTY01",
  "status": "FAILED",
  "message": "Job cancelled by user request",
  "parameters": { ... },
  "created_at": "2025-05-13T12:34:56.789Z",
  "updated_at": "2025-05-13T12:35:10.789Z",
  "started_at": "2025-05-13T12:35:00.123Z",
  "completed_at": "2025-05-13T12:35:10.789Z"
}
```

### Health Check

```
GET /plugins/v1/gis-export/health
```

Response:
```json
{
  "status": "healthy",
  "plugin": "gis_export",
  "version": "1.0.0",
  "timestamp": "2025-05-13T12:34:56.789Z"
}
```

## Export Formats

The plugin supports the following export formats:

- **GeoJSON**: Standard format for representing geographic features with non-spatial attributes
- **Shapefile**: ESRI format widely used in desktop GIS applications (exported as a ZIP archive)
- **KML**: Keyhole Markup Language format for use with Google Earth and similar applications

## Layer Types

Available layers include:

- **parcels**: Property parcel boundaries with basic attributes
- **zoning**: Zoning information for parcels
- **assessments**: Property assessment data
- **sales**: Historical sales data
- **improvements**: Building and improvement data

## Metrics

The plugin collects the following Prometheus metrics:

- `gis_export_jobs_submitted_total`: Total number of export jobs submitted
- `gis_export_jobs_completed_total`: Total number of successful export jobs
- `gis_export_jobs_failed_total`: Total number of failed export jobs
- `gis_export_processing_duration_seconds`: Time spent processing export jobs
- `gis_export_file_size_kb`: Size of exported files in kilobytes
- `gis_export_record_count`: Number of records in exported files

## Local Development

For testing during development, use the simplified API launcher:

```
python simplified_gis_export_api.py
```

This will start a FastAPI server on port 8083 with just the GIS Export endpoints enabled.

## Testing

Use the included test script to verify functionality:

```
python run_gis_export_tests.py
```

This will submit a test export job and verify that it completes successfully.