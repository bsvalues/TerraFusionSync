# GIS Export Plugin Testing Guide

This document explains how to run the tests for the GIS Export plugin in the TerraFusion platform.

## Overview

The GIS Export plugin testing consists of several components:

1. **Isolated Metrics Service** - A standalone service that handles metrics recording
2. **GIS Export API Tests** - Tests for the main plugin functionality
3. **End-to-end Workflow Tests** - Tests that validate the complete export process

## Testing Components

### 1. Isolated Metrics Service

The isolated metrics service runs on port 8090 and provides a separate Prometheus registry for GIS Export metrics. This design prevents conflicts with other plugins' metrics.

**Files:**
- `isolated_gis_export_metrics.py` - The standalone metrics service
- `run_isolated_gis_export_metrics.py` - Script to run the metrics service manually

### 2. GIS Export API Tests

The GIS Export API tests verify that the plugin's endpoints work correctly, including job creation, status checking, and result retrieval.

**Files:**
- `run_fixed_gis_export_tests.py` - The main test script
- `run_gis_export_api_test.py` - Orchestrator script that runs both the metrics service and tests

### 3. Integration with County Configurations

Tests verify that export requests respect county-specific configurations for supported formats, coordinate systems, and boundaries.

## Running the Tests

### Prerequisites

1. Make sure the SyncService is running on port 8080
2. Database is properly set up with the GIS Export tables

### Option 1: Run the Complete Test Suite

To run the complete test suite, which includes starting the metrics service and running all tests:

```bash
python run_gis_export_api_test.py
```

This script will:
1. Start the isolated metrics service on port 8090
2. Run the GIS Export tests
3. Display the test results
4. Clean up by stopping the metrics service

### Option 2: Run Individual Components

#### Step 1: Start the Isolated Metrics Service

```bash
python isolated_gis_export_metrics.py --port 8090
```

#### Step 2: Run the GIS Export Tests

In a separate terminal, run:

```bash
python run_fixed_gis_export_tests.py
```

### Option 3: Run as a Replit Workflow

To run the tests as part of a Replit workflow:

```bash
python run_gis_export_metrics_workflow.py
```

## Test Flow

The tests perform the following operations:

1. **Health Check**
   - Verify SyncService is healthy
   - Verify GIS Export plugin is healthy
   - Verify Isolated Metrics service is healthy

2. **Metrics Endpoints**
   - Verify isolated metrics endpoint is accessible
   - Verify SyncService main metrics endpoint is accessible

3. **Job Creation**
   - Create a test GIS export job for Benton County
   - Record the job submission in the metrics service
   - Verify metrics are updated to reflect the new job

4. **Job Status**
   - Poll the job status endpoint until the job completes
   - Record the job completion in the metrics service
   - Verify metrics are updated to reflect the completed job

5. **Metrics Validation**
   - Verify that the appropriate metrics counters have incremented
   - Verify that histograms for processing time, file size, and record count are updated

## Troubleshooting

### Common Issues and Solutions

1. **Metrics Endpoint 404 Error**
   - Ensure the isolated metrics service is running on port 8090
   - Check for any error messages in the isolated metrics service logs

2. **Job Status Endpoint 404 Error**
   - Verify that you're using the correct endpoint format: `/plugins/v1/gis-export/status/{job_id}`
   - The job ID in the endpoint should match the one returned from the job creation API

3. **Duplicate Metrics Registration Errors**
   - This is the exact issue our isolated metrics solution addresses
   - If you see this error, ensure you're using the isolated metrics service, not the default registry

4. **Jobs Stuck in RUNNING State**
   - Check the SyncService logs for any errors in the job processing
   - Ensure that the county configuration exists for the county being tested

## County-Specific Test Cases

For each supported county, the test should verify:

1. Supported formats are accepted (GeoJSON, Shapefile, KML, etc.)
2. Unsupported formats are rejected with appropriate error messages
3. Export area boundaries are properly validated
4. County-specific coordinate systems are correctly applied

## Next Steps for Testing

1. Add more comprehensive county configuration tests
2. Implement performance tests for large export regions
3. Add stress tests for concurrent export requests
4. Create integration tests with other plugins like Valuation and Market Analysis