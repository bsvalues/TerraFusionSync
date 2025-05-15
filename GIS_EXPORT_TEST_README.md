# GIS Export Plugin - Quick Start Guide

This guide provides a quick overview of the GIS Export plugin implementation, focusing on how to run and test it in the TerraFusion platform.

## Overview

The GIS Export plugin allows county staff to export geospatial data in various formats (GeoJSON, Shapefile, KML) with county-specific configurations. A key feature is the isolated metrics implementation that prevents conflicts with other plugins.

## Running the Tests

### Complete Test Suite (Recommended)

```bash
python run_gis_export_api_test.py
```

This will start the metrics service and run all tests automatically.

### Individual Steps

1. Start the isolated metrics service:
   ```bash
   python isolated_gis_export_metrics.py --port 8090
   ```

2. Run the tests:
   ```bash
   python run_fixed_gis_export_tests.py
   ```

## Key Files

- `isolated_gis_export_metrics.py` - Standalone metrics service
- `run_fixed_gis_export_tests.py` - Main test script
- `run_gis_export_api_test.py` - Orchestrator script
- `GIS_EXPORT_IMPLEMENTATION.md` - Detailed implementation documentation
- `GIS_EXPORT_TESTS.md` - Comprehensive testing guide

## API Endpoints

### Main Service (Port 8080)

- **Create Job**: POST `/plugins/v1/gis-export/run`
- **Check Status**: GET `/plugins/v1/gis-export/status/{job_id}`
- **Get Results**: GET `/plugins/v1/gis-export/results/{job_id}`
- **Health Check**: GET `/plugins/v1/gis-export/health`

### Isolated Metrics (Port 8090)

- **Metrics**: GET `/metrics`
- **Health Check**: GET `/health`
- **Record Job Submission**: POST `/record/job_submitted`
- **Record Job Completion**: POST `/record/job_completed`

## Example Job Creation Payload

```json
{
  "county_id": "benton_wa",
  "format": "GeoJSON",
  "username": "test_user",
  "area_of_interest": {
    "type": "Polygon",
    "coordinates": [
      [
        [-119.3, 46.1],
        [-119.2, 46.1],
        [-119.2, 46.2],
        [-119.3, 46.2],
        [-119.3, 46.1]
      ]
    ]
  },
  "layers": ["parcels", "roads"]
}
```

## For More Information

Refer to:
- `GIS_EXPORT_IMPLEMENTATION.md` for detailed architecture
- `GIS_EXPORT_TESTS.md` for comprehensive testing information