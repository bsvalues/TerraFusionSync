# Reporting Plugin CI Testing Guide

This document outlines how the Reporting Plugin tests are integrated into the CI/CD pipeline for the TerraFusion Platform.

## Test Files

The Reporting Plugin tests are located in the following files:

1. **Integration Tests:** `tests/plugins/test_reporting.py`
2. **Stale Reports Test:** `test_stale_reports.py` 
3. **Metrics Registration Test:** `test_reporting_metrics.py`

## CI Integration

The Reporting Plugin tests have been integrated into the TerraFusion Platform CI pipeline through a dedicated step in the `.github/workflows/ci.yml` file. This ensures that all tests run automatically on pull requests and merges to `main` and `develop` branches.

### CI Step Details

The CI step for Reporting Plugin tests:
- Runs after the main integration tests 
- Includes both pytest-based tests and standalone scripts
- Uses the same PostgreSQL test database as other CI tests
- Has more verbose logging to help diagnose issues in CI

```yaml
- name: Run Reporting Plugin Integration Tests
  run: |
    echo "Running Reporting Plugin Integration Tests..."
    # Run the reporting plugin tests with verbose output and showing print statements
    pytest tests/plugins/test_reporting.py -v -s -m "integration"
    
    # Also run the standalone stale reports test
    python test_stale_reports.py
    
    # Verify reporting metrics registration
    python test_reporting_metrics.py
  env:
    # Ensure all necessary environment variables for tests are available
    TEST_TERRAFUSION_OPERATIONAL_DB_URL: ${{ env.TEST_DATABASE_URL }}
    DATABASE_URL: ${{ env.TEST_DATABASE_URL }}
    LOG_LEVEL: DEBUG # More verbose logging for CI tests can be helpful
```

## Test Markers

All integration tests in `test_reporting.py` are marked with both `@pytest.mark.asyncio` (for async test support) and `@pytest.mark.integration` (for CI filtering).

Example:

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_report(cleanup_test_reports):
    """Test creating a new report job."""
    # Test implementation...
```

## What Is Tested

The Reporting Plugin tests cover:

1. **CRUD Operations:**
   - Creating new report jobs
   - Retrieving report details
   - Listing reports with filtering
   - Running report jobs

2. **CDC Reconciliation:**
   - Detection of stale reports
   - Proper timeout handling
   - Appropriate metadata updates for timed-out reports

3. **Metrics Registration:**
   - Verification of all 5 required Prometheus metrics:
     - `report_jobs_submitted_total`
     - `report_processing_duration_seconds`
     - `report_jobs_failed_total`
     - `report_jobs_pending`
     - `report_jobs_in_progress`

## Running Tests Locally

To run the same tests locally before pushing to CI:

```bash
# Run just the integration tests
pytest tests/plugins/test_reporting.py -v -m "integration"

# Run the standalone stale reports test
python test_stale_reports.py

# Check metrics registration
python test_reporting_metrics.py
```

## Debugging CI Test Failures

If the Reporting Plugin tests fail in CI:

1. Check the CI logs for the specific test failure
2. Look for database connection issues - the most common source of failures
3. Verify the SyncService is starting correctly in the CI environment
4. Check if any type errors are causing issues in the async environment

## Maintenance Responsibilities

When making changes to the Reporting Plugin:

1. Ensure test coverage is maintained or improved
2. Update test data and expected results when API contracts change
3. Add new tests when adding new functionality
4. Run tests locally before submitting PRs