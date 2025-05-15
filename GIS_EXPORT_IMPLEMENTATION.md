# GIS Export Plugin Implementation

## Overview

The GIS Export plugin provides functionality for exporting geographic data in various formats, including GeoJSON, Shapefile, and KML. It integrates with county-specific configurations to support different data formats, coordinate systems, and export limitations.

## Architecture

The plugin uses a modular architecture with the following components:

1. **Core Plugin Router** - Manages API endpoints for job creation, status checking, and result retrieval
2. **GIS Export Service** - Handles the business logic of processing export requests
3. **County Configuration** - Provides county-specific settings and validation
4. **Isolated Metrics Service** - Tracks usage metrics independently to avoid conflicts

## Isolated Metrics Solution

### Problem Statement

Initial implementation encountered metric registration conflicts between plugins, specifically:

- Multiple plugins (GIS Export, Market Analysis, etc.) attempted to register metrics with the same Prometheus registry
- Resulted in `ValueError: Duplicated timeseries in CollectorRegistry` errors
- Prevented reliable metrics collection and monitoring

### Solution

Implemented a standalone metrics service with the following features:

1. **Isolated Registry**: Each plugin has its own Prometheus registry, preventing conflicts
2. **Dedicated Metrics Endpoint**: Runs on a separate port (8090), keeping metrics separate from the main API
3. **Custom Record Endpoints**: Provides specific endpoints for recording job submission, completion, and failures
4. **Stateful Job Tracking**: Maintains a record of jobs for consistent metrics recording

### Implementation Details

#### 1. Isolated Metrics API

The `isolated_gis_export_metrics.py` file implements a standalone FastAPI service that:

- Creates a dedicated Prometheus `CollectorRegistry`
- Defines metrics specific to GIS Export operations
- Exposes endpoints for recording job events
- Provides a Prometheus-compatible metrics endpoint

```python
# Key metrics tracked:
gis_export_jobs_submitted = Counter(
    'gis_export_jobs_submitted_total',
    'Total number of GIS export jobs submitted',
    ['county_id', 'export_format'],
    registry=registry
)

gis_export_jobs_completed = Counter(
    'gis_export_jobs_completed_total',
    'Total number of GIS export jobs completed successfully',
    ['county_id', 'export_format'],
    registry=registry
)

gis_export_processing_duration = Histogram(
    'gis_export_processing_duration_seconds',
    'Duration of GIS export job processing in seconds',
    ['county_id', 'export_format'],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
    registry=registry
)
```

#### 2. Integration with Main Plugin

The GIS Export plugin router now communicates with the metrics service via HTTP:

1. When a job is created, the plugin sends a record to the metrics service
2. When a job completes or fails, the status is recorded in the metrics service
3. Monitoring systems query the isolated metrics endpoint for statistics

#### 3. Enhanced Simulation Processing Logic

The GIS Export plugin now includes a more realistic simulation of GIS data processing tasks to better represent actual processing times and file characteristics in a production environment:

1. **Complexity-Based Processing Time**:
   - Processing time varies based on layer count and complexity
   - GeoJSON feature complexity is analyzed by examining geometry types and coordinate counts
   - More complex exports (more layers, complex geometries) take proportionally longer to process

2. **Cloud Storage Integration**:
   - Simulates realistic file paths using standard Azure Blob or AWS S3 conventions
   - Creates organized storage paths with county/date-based folder hierarchy
   - Uses deterministic file naming with timestamp and content hash for idempotency

3. **Format-Specific Output Characteristics**:
   - Different export formats (GeoJSON, Shapefile, KML, etc.) have different file size characteristics
   - Format-specific size factors reflect real-world differences (e.g., XML-based formats are larger)
   - Output file size scales with the complexity of the input data

4. **Layer-Type Record Counts**:
   - Record counts are based on realistic expectations for different layer types
   - Parcel layers typically contain thousands of records
   - Building layers have higher record density
   - Boundary layers have fewer, more complex records

5. **Performance Monitoring**:
   - Comprehensive logging of export parameters, processing time, and results
   - Deterministic but randomized file sizes and record counts for realistic testing

#### 4. Testing Strategy

The implementation includes a comprehensive testing strategy:

- `run_fixed_gis_export_tests.py` - Tests the entire GIS Export plugin workflow with metrics
- `run_gis_export_api_test.py` - Manages both the metrics service and test execution
- `run_gis_export_metrics_workflow.py` - Runs the metrics service as a Replit workflow

## API Endpoints

### Main GIS Export API (Port 8080)

- `/plugins/v1/gis-export/run` - Create a new export job
- `/plugins/v1/gis-export/status/{job_id}` - Check job status
- `/plugins/v1/gis-export/results/{job_id}` - Get job results
- `/plugins/v1/gis-export/list` - List all jobs with optional filtering
- `/plugins/v1/gis-export/health` - Plugin health check
- `/plugins/v1/gis-export/formats/{county_id}` - Get supported formats for a county
- `/plugins/v1/gis-export/defaults/{county_id}` - Get default export parameters

### Isolated Metrics API (Port 8090)

- `/metrics` - Prometheus-compatible metrics endpoint
- `/health` - Health check for the metrics service
- `/record/job_submitted` - Record a new job submission
- `/record/job_completed` - Record a job completion
- `/record/job_failed` - Record a job failure
- `/jobs` - Get all tracked jobs (debugging)

## Processing Parameters

The GIS Export plugin accepts and processes the following parameters:

| Parameter | Description | Default |
|-----------|-------------|---------|
| format | Export format (geojson, shapefile, kml, etc.) | (Required) |
| county_id | County identifier | (Required) |
| area_of_interest | GeoJSON object defining the export area | (Required) |
| layers | Array of layer identifiers to export | (Required) |
| coordinate_system | Coordinate system code (e.g., "EPSG:4326") | County default |
| simplify_tolerance | Geometry simplification tolerance | 0.0001 |
| max_precision | Maximum coordinate decimal precision | County default |
| include_attributes | Attributes to include for each feature | All |
| filter_expression | Expression to filter features | None |

## File Output Characteristics

Different export formats produce files with different characteristics:

| Format | Size Factor | Typical Use Case |
|--------|-------------|-----------------|
| GeoJSON | 1.2x | Web mapping and visualization |
| Shapefile | 0.8x | Desktop GIS applications |
| KML | 1.5x | Google Earth and similar tools |
| TopoJSON | 0.7x | Web visualization with topology preservation |
| GeoPackage | 0.9x | OGC standard format for multiple datasets |
| GeoTIFF | 2.5x | Raster data with spatial reference |

## County Configuration Integration

The GIS Export plugin integrates with county-specific configurations to:

1. Validate requested export formats against county-supported formats
2. Apply county-specific coordinate systems to exports
3. Verify export area is within county boundaries
4. Apply county-specific data transformations and filters

## Deployment Strategy

For production deployment to Azure, the isolated metrics service is deployed as a separate microservice with:

1. Its own App Service instance
2. Proper network security rules to allow only internal communication
3. Integration with Azure Monitor for metrics collection
4. Health checks and auto-recovery

## Future Improvements

1. Add support for more export formats (GML, FGDB, etc.)
2. Implement county-specific data transformations
3. Add caching for frequently requested exports
4. Implement multi-region export capability
5. Add rate limiting based on county configurations