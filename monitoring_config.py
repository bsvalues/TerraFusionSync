"""
TerraFusion SyncService Monitoring Configuration

This module defines monitoring thresholds and alert configurations for the 
TerraFusion SyncService platform.
"""

# Monitoring thresholds for metrics
MONITORING_THRESHOLDS = {
    # Resource usage thresholds
    "cpu_usage_percent": {
        "warning": 70.0,
        "critical": 80.0,
        "description": "CPU usage percentage",
        "unit": "%"
    },
    "memory_usage_percent": {
        "warning": 70.0,
        "critical": 80.0,
        "description": "Memory usage percentage",
        "unit": "%"
    },
    "disk_usage_percent": {
        "warning": 75.0,
        "critical": 85.0,
        "description": "Disk usage percentage",
        "unit": "%"
    },
    
    # Service performance thresholds
    "response_time_ms": {
        "warning": 200.0,
        "critical": 500.0,
        "description": "Service response time",
        "unit": "ms"
    },
    
    # Operation thresholds
    "failed_operations_per_hour": {
        "warning": 3,
        "critical": 5,
        "description": "Failed sync operations per hour",
        "unit": "count"
    },
    "service_restarts_per_day": {
        "warning": 2,
        "critical": 3,
        "description": "Service restart count per day",
        "unit": "count"
    }
}

# Log rotation configuration
LOG_ROTATION_CONFIG = {
    "max_size": 100 * 1024 * 1024,  # 100 MB
    "backup_count": 7,              # Keep 7 backup files
    "encoding": "utf-8"
}

# Alert notification settings - these would be configured for production
ALERT_NOTIFICATION_CONFIG = {
    "email": {
        "enabled": False,
        "recipients": ["admin@example.com"],
        "from_address": "alerts@example.com",
        "subject_prefix": "[TerraFusion Alert]",
    },
    "webhook": {
        "enabled": False,
        "url": "https://example.com/alert-webhook",
        "timeout": 5,  # seconds
    }
}

# Health check endpoints
HEALTH_CHECK_ENDPOINTS = {
    "api_gateway": {
        "url": "http://localhost:5000/api/status",
        "method": "GET",
        "timeout": 5,  # seconds
        "expected_status": 200
    },
    "sync_service": {
        "url": "http://localhost:8080/health",
        "method": "GET",
        "timeout": 5,  # seconds
        "expected_status": 200
    },
    "sync_service_liveness": {
        "url": "http://localhost:8080/health/live",
        "method": "GET",
        "timeout": 2,  # seconds
        "expected_status": 200
    },
    "sync_service_readiness": {
        "url": "http://localhost:8080/health/ready",
        "method": "GET",
        "timeout": 2,  # seconds
        "expected_status": 200
    }
}

def get_alert_message(metric_name, current_value, threshold_value, severity):
    """
    Generate a formatted alert message.
    
    Args:
        metric_name: Name of the metric
        current_value: Current value of the metric
        threshold_value: Threshold that was crossed
        severity: Alert severity (warning or critical)
        
    Returns:
        Formatted alert message string
    """
    metric_config = MONITORING_THRESHOLDS.get(metric_name, {})
    description = metric_config.get("description", metric_name)
    unit = metric_config.get("unit", "")
    
    return f"{severity.upper()}: {description} is {current_value}{unit}, threshold: {threshold_value}{unit}"