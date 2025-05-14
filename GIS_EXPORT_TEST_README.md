# GIS Export Plugin Testing Guide

This guide explains how to test the GIS Export plugin functionality, including county-specific configuration integration, API endpoints, and job processing.

## Overview

The GIS Export plugin in the TerraFusion Platform allows county users to export geospatial data in various formats with county-specific configurations. This guide covers testing the different components of the plugin.

## Prerequisites

Ensure that your environment is properly set up:

1. Database is initialized with GIS export tables
2. County configuration files are in place under `county_configs/`
3. TerraFusion SyncService is running
4. TerraFusion API Gateway is running

## County Configuration Testing

### Standalone Configuration Test

The standalone configuration test validates that county-specific settings are properly loaded and applied:

```bash
python test_gis_export_county_config_standalone.py
```

This test verifies:
- Available export formats per county
- Format validation against county-allowed formats
- Default coordinate systems and parameters
- Maximum export area limits

### County Configuration Demo

To see a visual demonstration of how county configurations work with export requests:

```bash
python demo_gis_export_county_config.py
```

This demo shows:
- The configuration for multiple counties
- Validation of export formats against county settings
- Application of default parameters
- Error handling for unsupported formats

## API Endpoint Testing

To test the API endpoints directly, ensure the SyncService is running, then try:

### Health Check

```bash
curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/health
```

Expected response: `{"status": "healthy", "timestamp": "2025-05-14T12:00:00Z"}`

### Available Formats for County

```bash
curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/formats/benton_wa
```

Expected response: `{"formats": ["GeoJSON", "Shapefile", "KML"]}`

### Default Parameters for County

```bash
curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/defaults/benton_wa
```

Expected response: 
```json
{
  "parameters": {
    "simplify_tolerance": 0.0001,
    "include_attributes": true,
    "coordinate_system": "EPSG:4326"
  }
}
```

### Submit Export Job

```bash
curl -X POST http://0.0.0.0:8080/plugins/v1/gis-export/run \
  -H "Content-Type: application/json" \
  -d '{
    "county_id": "benton_wa",
    "format": "GeoJSON",
    "username": "county_user",
    "area_of_interest": {
      "type": "Polygon",
      "coordinates": [[
        [-119.48, 46.21],
        [-119.48, 46.26],
        [-119.42, 46.26],
        [-119.42, 46.21],
        [-119.48, 46.21]
      ]]
    },
    "layers": ["parcels", "zoning"],
    "parameters": {
      "simplify_tolerance": 0.0001,
      "include_attributes": true
    }
  }'
```

Expected response: `{"job_id": "...", "status": "PENDING"}`

### Check Job Status

```bash
curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/status/{job_id}
```

Expected response: `{"status": "COMPLETED", "message": "Export completed successfully"}`

## End-to-End Testing

For comprehensive end-to-end testing, run:

```bash
python run_gis_export_tests.py
```

This script runs a series of tests including:
1. Health check endpoint
2. County configuration integration
3. Format validation
4. Job submission
5. Job status checking
6. Results retrieval

## Testing with Different Counties

To verify that the system works with different county configurations:

1. Create test configurations for multiple counties:
   ```
   county_configs/benton_wa/benton_wa_config.json
   county_configs/clark_wa/clark_wa_config.json
   county_configs/king_wa/king_wa_config.json
   ```

2. Run the demo with different county IDs:
   ```bash
   python demo_gis_export_county_config.py
   ```

3. Test API endpoints with different county IDs:
   ```bash
   curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/formats/clark_wa
   curl -X GET http://0.0.0.0:8080/plugins/v1/gis-export/defaults/king_wa
   ```

## Troubleshooting

If tests fail, check the following:

1. **Service Connection**: Ensure SyncService is running on the expected port
2. **Database Connection**: Verify database connectivity
3. **County Configuration**: Check that county configuration files exist and have the correct format
4. **Format Validation**: Verify that the requested export format is in the county's allowed formats list
5. **CORS Issues**: For browser-based testing, ensure CORS headers are properly set

## Metrics Verification

To verify that metrics are being collected:

```bash
curl -X GET http://0.0.0.0:8080/metrics
```

Look for GIS Export-specific metrics such as:
- `gis_export_jobs_submitted_total`
- `gis_export_jobs_completed_total`
- `gis_export_processing_duration_seconds`