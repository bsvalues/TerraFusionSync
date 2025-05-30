# 📊 TerraFusion Platform Grafana Monitoring

This document provides setup instructions for the unified TerraFusion monitoring dashboard that tracks GIS Export, NarratorAI, and system performance in real-time.

## 🎯 Dashboard Overview

The TerraFusion monitoring dashboard provides:

- **📊 GIS Export Performance**: Job duration, failure rates, format distribution by county
- **🤖 NarratorAI Analytics**: Response times, model success rates, task distribution
- **🖥️ System Health**: CPU, memory, HTTP request rates, service status
- **📈 Real-time Metrics**: 30-second refresh with historical data

## 🚀 Quick Setup

### 1. Import the Dashboard

1. Open Grafana (typically at `http://localhost:3000`)
2. Login with your Grafana credentials
3. Navigate to **"+"** → **"Import"**
4. Upload the file: `grafana/terrafusion_monitoring.json`
5. Select your Prometheus data source
6. Click **"Import"**

### 2. Configure Prometheus

Copy the Prometheus configuration:
```bash
cp prometheus_terrafusion.yml /path/to/prometheus/prometheus.yml
```

Or add these scrape targets to your existing `prometheus.yml`:

```yaml
scrape_configs:
  # TerraFusion API Gateway
  - job_name: 'terrafusion_api_gateway'
    metrics_path: '/gateway-metrics'
    static_configs:
      - targets: ['localhost:5000']

  # TerraFusion Sync Service  
  - job_name: 'terrafusion_sync_service'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8080']
```

### 3. Restart Services

```bash
# Restart Prometheus to pick up new configuration
sudo systemctl restart prometheus

# Or if running manually:
./prometheus --config.file=prometheus_terrafusion.yml
```

## 📈 Key Metrics Tracked

### GIS Export Metrics
- `gis_export_jobs_total{status, format, county_id}` - Total export jobs
- `gis_export_job_duration_seconds` - Job processing time
- `gis_export_failures_total{format}` - Failed export attempts

### NarratorAI Metrics  
- `ai_tasks_total{action, model_name}` - AI task executions
- `ai_latency_seconds` - AI response time
- `ai_failures_total{model_name}` - AI processing failures

### System Metrics
- `process_cpu_usage{job}` - CPU utilization per service
- `process_memory_usage{job}` - Memory consumption
- `http_requests_total{method, path, job}` - HTTP traffic
- `up{job}` - Service availability status

## 🎛️ Dashboard Sections

### 🎯 Platform Overview
- **GIS Export Jobs by Status**: Pie chart showing completed vs failed jobs
- **NarratorAI Tasks by Type**: Distribution of AI operations (summarize, classify, explain)

### 📊 GIS Export Performance
- **Job Duration Trends**: 95th and 50th percentile processing times
- **Failure Rate Monitoring**: Real-time failure detection
- **County & Format Heatmap**: Usage patterns across different regions

### 🤖 NarratorAI Performance
- **Response Time Analysis**: AI latency percentiles
- **Model Success Rates**: Performance by AI model
- **Failure Rate Tracking**: Error monitoring

### 🖥️ System Health
- **Resource Utilization**: CPU and memory usage with thresholds
- **Request Volume**: HTTP traffic patterns
- **Service Status**: Real-time health checks

## ⚠️ Alert Thresholds

The dashboard includes visual indicators for:

- **CPU Usage**: Warning at 70%, Critical at 80%
- **Memory Usage**: Warning at 70%, Critical at 80%
- **Response Times**: Monitoring for degradation trends
- **Service Availability**: Immediate notification if services go down

## 🔧 Troubleshooting

### Common Issues

**Dashboard shows "No data":**
- Verify Prometheus is scraping your services: `http://localhost:9090/targets`
- Check that services are exposing metrics endpoints
- Confirm firewall settings allow metric collection

**Metrics missing:**
- Ensure your services are running and healthy
- Verify metric endpoint paths in Prometheus config
- Check service logs for metric registration errors

**Grafana connection issues:**
- Confirm Prometheus data source is configured correctly
- Test connection in Grafana data source settings
- Verify Prometheus URL is accessible from Grafana

### Service Endpoints

Verify these endpoints are accessible:
- **API Gateway**: `http://localhost:5000/gateway-metrics`
- **Sync Service**: `http://localhost:8080/metrics`
- **Prometheus**: `http://localhost:9090/targets`

## 🎨 Customization

### Adding New Panels

1. Click **"Add Panel"** in the dashboard
2. Select your metric from the Prometheus query builder
3. Configure visualization type (timeseries, gauge, table, etc.)
4. Set appropriate thresholds and legends

### Custom Alerts

Create alerts for critical metrics:
1. Edit a panel → Alert tab
2. Set query conditions (e.g., `cpu_usage > 80`)
3. Configure notification channels
4. Test alert rules

## 📱 Mobile Access

The dashboard is optimized for:
- **Desktop**: Full feature access
- **Tablet**: Responsive layout with touch navigation  
- **Mobile**: Essential metrics in streamlined view

## 🔄 Automatic Refresh

Dashboard refreshes every **30 seconds** by default. Adjust the refresh rate:
- Top right corner → Refresh dropdown
- Options: 5s, 10s, 30s, 1m, 5m, 15m, 30m, 1h

## 📊 Export & Sharing

- **Share Dashboard**: Generate public links or embed codes
- **Export Data**: Download metrics as CSV or JSON
- **PDF Reports**: Schedule automated performance reports
- **API Access**: Programmatic access to dashboard data

---

## 🚀 Next Steps

Once monitoring is active, consider:

1. **🧪 Performance Benchmarking**: Compare Rust vs Python GIS performance
2. **🔧 UX Enhancements**: Add validation endpoints and error handling
3. **📱 Mobile Dashboard**: County staff mobile monitoring app
4. **⚡ Real-time Alerts**: SMS/email notifications for critical issues

Your TerraFusion platform now has enterprise-grade observability! 🎉