# TerraFusion Platform Monitoring

This document describes how to use the monitoring stack (Prometheus and Grafana) with the TerraFusion platform.

## Overview

The monitoring stack consists of:

- **Prometheus**: A time-series database that collects and stores metrics
- **Grafana**: A visualization and alerting tool for metrics

## Running the Monitoring Stack

### Option 1: Using Docker Compose (local development)

1. Make sure Docker and Docker Compose are installed
2. Start the services:

```bash
docker-compose up -d
```

3. Access the UIs:
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (login with admin/admin)

### Option 2: Using the Standalone Scripts (Replit)

Use the combined monitoring script:

```bash
./start_monitoring.sh
```

Or run each service individually:

1. Start Prometheus:
```bash
python run_prometheus.py
```

2. Start Grafana:
```bash
python run_grafana.py
```

## Dashboards

The monitoring stack comes with pre-configured dashboards:

- **TerraFusion SyncService Overview**: Shows service health, sync operations, and API metrics

## Metrics

The following metrics are available:

### Service Health
- `process_cpu_usage`: CPU usage of the SyncService
- `process_resident_memory_bytes`: Memory usage of the SyncService
- `up`: Health status of the SyncService (1 = healthy, 0 = down)

### Sync Operations
- `valuation_jobs_submitted_total`: Total number of valuation jobs submitted
- `valuation_jobs_completed_total`: Total number of valuation jobs completed
- `valuation_jobs_failed_total`: Total number of valuation jobs failed
- `valuation_jobs_pending_count`: Current number of pending valuation jobs
- `valuation_jobs_running_count`: Current number of running valuation jobs
- `valuation_jobs_by_status_count`: Count of jobs by status

### API Metrics
- `http_requests_total`: Total number of HTTP requests
- `http_request_duration_seconds`: HTTP request duration in seconds

## Adding Custom Metrics

To add custom metrics to your application:

1. Import the Prometheus client library
2. Define metrics (counters, gauges, histograms, etc.)
3. Update the metrics in your code
4. Expose the metrics at an HTTP endpoint (typically `/metrics`)

Example:

```python
from prometheus_client import Counter, Gauge, Histogram

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
ACTIVE_REQUESTS = Gauge('http_requests_active', 'Active HTTP requests', ['method', 'endpoint'])

# Update metrics in your code
REQUEST_COUNT.labels(method='GET', endpoint='/api/data').inc()
with REQUEST_LATENCY.labels(method='GET', endpoint='/api/data').time():
    # Your code here
    pass
```

## Troubleshooting

- **Prometheus cannot scrape metrics**: Check if the SyncService is running and the `/metrics` endpoint is accessible
- **Grafana cannot connect to Prometheus**: Check if Prometheus is running and the URL is correct
- **Metrics not showing in Grafana**: Check if Prometheus is collecting the metrics and the queries in Grafana are correct