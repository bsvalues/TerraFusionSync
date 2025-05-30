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

#### Docker Configuration

When using Docker, the monitoring services are configured to communicate over the Docker network. The Prometheus configuration uses the service names as defined in docker-compose.yml:

```yaml
scrape_configs:
  # Scrape Prometheus itself
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Scrape TerraFusion Sync Service
  - job_name: "terrafusion_sync_service"
    metrics_path: /metrics
    static_configs:
      # 'terrafusion_sync_core' is the service name in docker-compose.yml
      - targets: ["terrafusion_sync_core:8001"]  # service_name:container_port

  # Gateway specific metrics
  - job_name: "terrafusion_api_gateway"
    metrics_path: /gateway-metrics
    static_configs:
      # 'terrafusion_api_gateway' is the service name in docker-compose.yml
      - targets: ["terrafusion_api_gateway:5000"]  # service_name:container_port
```

The local development version of this configuration is available in the `prometheus.yml` file at the root of the project, with Docker-specific sections commented out.

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

- **TerraFusion SyncService Overview**: Shows SyncService health, sync operations, and API metrics
- **TerraFusion Gateway Overview**: Shows Gateway health, request rates, status codes, and latency metrics

## Metrics

The following metrics are available:

### Service Health
- `process_cpu_usage`: CPU usage of the SyncService
- `process_resident_memory_bytes`: Memory usage of the SyncService
- `up`: Health status of the SyncService (1 = healthy, 0 = down)
- `system_cpu_usage_percent`: Current CPU usage percentage (Gateway)
- `system_memory_usage_percent`: Current memory usage percentage (Gateway)

### Sync Operations
- `valuation_jobs_submitted_total`: Total number of valuation jobs submitted
- `valuation_jobs_completed_total`: Total number of valuation jobs completed
- `valuation_jobs_failed_total`: Total number of valuation jobs failed
- `valuation_jobs_pending_count`: Current number of pending valuation jobs
- `valuation_jobs_running_count`: Current number of running valuation jobs
- `valuation_jobs_by_status_count`: Count of jobs by status

### API Gateway Metrics
- `terrafusion_http_requests`: Total count of HTTP requests through the Gateway
- `gateway_http_requests_total`: Detailed count of HTTP requests by endpoint, method, and status
- `gateway_http_request_duration_seconds`: Histogram of HTTP request latency in seconds by endpoint and method

### SyncService API Metrics
- `http_requests_total`: Total number of HTTP requests to the SyncService
- `http_request_duration_seconds`: HTTP request duration in seconds for the SyncService

### Metric Endpoints
- `/metrics`: General metrics endpoint (both Gateway and SyncService)
- `/gateway-metrics`: Gateway-specific metrics with detailed request tracking

## Using the Dashboards

### TerraFusion SyncService Overview Dashboard

This dashboard provides insights into the SyncService component:

- **Service Health**: Shows the status, CPU, and memory usage of the SyncService
- **Sync Operations**: Displays valuation job submission rates, completion rates, and job counts by status
- **API Metrics**: Shows request rates and latencies for SyncService API endpoints

### TerraFusion Gateway Overview Dashboard

This dashboard focuses on the API Gateway component:

- **Service Health**: Shows the status, CPU, and memory usage of the Gateway
- **API Gateway Traffic**: Visualizes HTTP request rates, status code distribution, and response times
- **Top Endpoints**: Identifies the most frequently accessed endpoints and the slowest endpoints

### Accessing the Dashboards

To access the dashboards:

1. Start the monitoring stack using the instructions above
2. Open Grafana at http://localhost:3000 (or the appropriate URL)
3. Log in with the default credentials (admin/admin)
4. Navigate to "Dashboards" in the left sidebar
5. Select either "TerraFusion SyncService Overview" or "TerraFusion Gateway Overview"

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

### Common Issues in Development Environment

- **Prometheus cannot scrape metrics**: Check if the services are running and the metrics endpoints are accessible
  - For SyncService: `/metrics` on port 8080
  - For API Gateway: `/gateway-metrics` on port 5000
- **Grafana cannot connect to Prometheus**: Check if Prometheus is running and the URL is correct
- **Metrics not showing in Grafana**: Check if Prometheus is collecting the metrics and the queries in Grafana are correct
- **Duplicate metrics errors**: Check for duplicate metric registration in the code. For system metrics, ensure metrics are reused instead of recreated on each request

### Docker-Specific Troubleshooting

- **Services can't reach each other**: In Docker, services connect via their service names in the docker-compose network. Verify that:
  - The service names match exactly between docker-compose.yml and prometheus.yml
  - All services are on the same Docker network
  - Port mappings are correct (internal container port vs. exposed port)
- **Container metrics not visible**: Make sure the metrics endpoints are exposed to the Docker network
- **Job name compatibility**: Our dashboards are configured to support both development and Docker environments:
  - Gateway dashboard uses `job=~"terrafusion_gateway_standalone|terrafusion_api_gateway"` patterns
  - SyncService dashboard uses `job=~"terrafusion_sync_service|terrafusion_sync_service_docker"` patterns
  - This allows the same dashboards to work in both environments without modification