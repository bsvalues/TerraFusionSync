"""
TerraFusion SyncService Monitoring Service

This script implements the monitoring service for the TerraFusion SyncService platform.
It periodically checks system health and metrics against defined thresholds and
generates alerts when thresholds are exceeded.
"""

import os
import time
import json
import logging
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Import monitoring configuration
from monitoring_config import (
    MONITORING_THRESHOLDS,
    HEALTH_CHECK_ENDPOINTS,
    ALERT_NOTIFICATION_CONFIG,
    get_alert_message
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('monitoring_service')

# Database access (for production, move this to a separate module)
try:
    from app import app, db
    from models import SystemMetrics, AuditEntry
    DB_AVAILABLE = True
except ImportError:
    logger.warning("Database models not available, running in standalone mode")
    DB_AVAILABLE = False

# Global state
last_check_time = datetime.utcnow()
active_alerts = {}  # Keep track of active alerts to avoid duplicates


def check_endpoint_health(endpoint_config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Check the health of a service endpoint.
    
    Args:
        endpoint_config: Configuration for the endpoint
        
    Returns:
        Tuple of (success, response_data)
    """
    url = endpoint_config.get("url")
    method = endpoint_config.get("method", "GET")
    timeout = endpoint_config.get("timeout", 5)
    expected_status = endpoint_config.get("expected_status", 200)
    
    logger.info(f"Checking health of endpoint: {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            logger.warning(f"Unsupported method: {method}, using GET")
            response = requests.get(url, timeout=timeout)
        
        is_healthy = response.status_code == expected_status
        
        try:
            response_data = response.json()
        except ValueError:
            response_data = {"status": "unknown", "response_text": response.text[:100]}
        
        return is_healthy, response_data
    
    except requests.RequestException as e:
        logger.error(f"Error checking endpoint {url}: {str(e)}")
        return False, {"error": str(e)}


def check_system_metrics() -> Dict[str, Any]:
    """
    Retrieve and check the latest system metrics against thresholds.
    
    Returns:
        Dictionary with metrics and alert status
    """
    metrics = {}
    alerts = []
    
    # Fetch the latest metrics from SyncService
    try:
        response = requests.get(f"{HEALTH_CHECK_ENDPOINTS['sync_service']['url']}", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            system_data = data.get("system", {})
            
            # Extract metrics
            metrics["cpu_usage_percent"] = system_data.get("cpu_usage", 0.0)
            metrics["memory_usage_percent"] = system_data.get("memory_usage", 0.0)
            metrics["disk_usage_percent"] = system_data.get("disk_usage", 0.0)
            
            # Check each metric against thresholds
            for metric_name, value in metrics.items():
                if metric_name in MONITORING_THRESHOLDS:
                    thresholds = MONITORING_THRESHOLDS[metric_name]
                    
                    # Check critical threshold
                    if value >= thresholds.get("critical", float('inf')):
                        alert = get_alert_message(
                            metric_name, value, thresholds["critical"], "critical"
                        )
                        alerts.append({"metric": metric_name, "severity": "critical", "message": alert})
                    
                    # Check warning threshold
                    elif value >= thresholds.get("warning", float('inf')):
                        alert = get_alert_message(
                            metric_name, value, thresholds["warning"], "warning"
                        )
                        alerts.append({"metric": metric_name, "severity": "warning", "message": alert})
    
    except requests.RequestException as e:
        logger.error(f"Error fetching metrics: {str(e)}")
        alerts.append({
            "metric": "metrics_collection",
            "severity": "error",
            "message": f"ERROR: Failed to collect metrics: {str(e)}"
        })
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "alerts": alerts
    }


def check_service_health() -> Dict[str, Any]:
    """
    Perform a comprehensive service health check.
    
    Returns:
        Dictionary with health status of all components
    """
    health_results = {}
    
    # Check all endpoints
    for name, config in HEALTH_CHECK_ENDPOINTS.items():
        is_healthy, data = check_endpoint_health(config)
        health_results[name] = {
            "status": "healthy" if is_healthy else "unhealthy",
            "data": data,
            "last_check": datetime.utcnow().isoformat()
        }
    
    # Get system metrics and alerts
    metrics_check = check_system_metrics()
    health_results["system_metrics"] = metrics_check
    
    # Calculate overall health
    component_statuses = [r["status"] for r in health_results.values() 
                         if isinstance(r, dict) and "status" in r]
    
    if all(status == "healthy" for status in component_statuses):
        overall_status = "healthy"
    elif "unhealthy" in component_statuses:
        overall_status = "degraded"
    else:
        overall_status = "unknown"
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": overall_status,
        "components": health_results
    }


def handle_alerts(alerts: List[Dict[str, Any]]):
    """
    Process and send alerts based on configuration.
    
    Args:
        alerts: List of alert dictionaries
    """
    if not alerts:
        return
    
    for alert in alerts:
        logger.warning(f"ALERT: {alert['message']}")
        
        # Create audit entry if database is available
        if DB_AVAILABLE:
            try:
                with app.app_context():
                    entry = AuditEntry(
                        event_type="alert_triggered",
                        resource_type="system_metrics",
                        description=alert["message"],
                        severity=alert["severity"],
                        new_state={"metric": alert["metric"]}
                    )
                    db.session.add(entry)
                    db.session.commit()
            except Exception as e:
                logger.error(f"Failed to create audit entry: {str(e)}")
        
        # Here you would implement notification sending based on ALERT_NOTIFICATION_CONFIG
        # For now, we just log the alerts


def run_monitoring_service(interval_seconds=60):
    """
    Run the monitoring service main loop.
    
    Args:
        interval_seconds: How often to run checks
    """
    logger.info(f"Starting TerraFusion monitoring service with {interval_seconds}s interval")
    
    while True:
        try:
            # Run health check
            logger.info("Running service health check")
            health_results = check_service_health()
            
            # Log overall status
            logger.info(f"Overall system status: {health_results['overall_status']}")
            
            # Handle any alerts
            all_alerts = []
            if "system_metrics" in health_results["components"]:
                all_alerts.extend(health_results["components"]["system_metrics"].get("alerts", []))
            
            if all_alerts:
                handle_alerts(all_alerts)
            else:
                logger.info("No alerts detected")
            
            # Save health check results to a file for reference
            with open('latest_health_check.json', 'w') as f:
                json.dump(health_results, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error in monitoring service: {str(e)}")
        
        # Sleep until next check
        time.sleep(interval_seconds)


if __name__ == "__main__":
    try:
        # Run the monitoring service
        run_monitoring_service()
    except KeyboardInterrupt:
        logger.info("Monitoring service stopped by user")
    except Exception as e:
        logger.error(f"Monitoring service error: {str(e)}")