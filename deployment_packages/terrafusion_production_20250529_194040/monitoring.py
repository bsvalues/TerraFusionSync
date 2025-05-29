"""
TerraFusion Platform - Monitoring Module

This module provides monitoring functionality for the TerraFusion Platform,
collecting metrics on API requests, database operations, and system resources.
"""

import os
import time
import threading
import logging
import psutil
from datetime import datetime
from flask import request, g
from functools import wraps
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize metrics
API_REQUEST_COUNT = Counter(
    'terrafusion_api_requests_total', 
    'Total count of API requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'terrafusion_request_latency_seconds', 
    'Request latency in seconds',
    ['method', 'endpoint']
)

DB_OPERATION_LATENCY = Histogram(
    'terrafusion_db_operation_latency_seconds', 
    'Database operation latency in seconds',
    ['operation', 'table']
)

ACTIVE_REQUESTS = Gauge(
    'terrafusion_active_requests', 
    'Number of active requests'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'terrafusion_system_memory_usage_bytes', 
    'Current system memory usage in bytes'
)

SYSTEM_CPU_USAGE = Gauge(
    'terrafusion_system_cpu_usage_percent', 
    'Current system CPU usage percentage'
)

GIS_EXPORT_JOBS = Counter(
    'terrafusion_gis_export_jobs_total', 
    'Total count of GIS export jobs',
    ['status', 'county', 'format']
)

SYNC_JOBS = Counter(
    'terrafusion_sync_jobs_total', 
    'Total count of sync jobs',
    ['status', 'county', 'source', 'target']
)

EXPORT_FILE_SIZE = Summary(
    'terrafusion_export_file_size_bytes', 
    'Size of export files in bytes',
    ['format']
)

class TerraFusionMonitoring:
    """
    TerraFusion Monitoring class for collecting and exposing metrics.
    """
    
    def __init__(self, app=None, port=8000, disable_metrics_endpoint=False):
        """
        Initialize the monitoring system.
        
        Args:
            app: Flask app to register middleware with (optional)
            port: Port to expose Prometheus metrics on (default: 8000)
            disable_metrics_endpoint: If True, don't start the metrics HTTP server
        """
        self.port = port
        self.metrics_thread = None
        
        if app:
            self.init_app(app)
        
        if not disable_metrics_endpoint:
            self.start_metrics_server()
            
        # Start system metrics collection
        self.start_system_metrics_collection()
    
    def init_app(self, app):
        """
        Initialize the Flask app with monitoring middleware.
        
        Args:
            app: Flask app to register middleware with
        """
        # Register before_request handler
        @app.before_request
        def before_request():
            g.start_time = time.time()
            ACTIVE_REQUESTS.inc()
        
        # Register after_request handler
        @app.after_request
        def after_request(response):
            if hasattr(g, 'start_time'):
                request_latency = time.time() - g.start_time
                REQUEST_LATENCY.labels(
                    method=request.method,
                    endpoint=request.path
                ).observe(request_latency)
                
                API_REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.path,
                    status=response.status_code
                ).inc()
                
                ACTIVE_REQUESTS.dec()
            
            return response
    
    def start_metrics_server(self):
        """Start the Prometheus metrics HTTP server in a separate thread."""
        def run_metrics_server():
            logger.info(f"Starting metrics server on port {self.port}")
            try:
                start_http_server(self.port)
                logger.info(f"Metrics server started on port {self.port}")
            except Exception as e:
                logger.error(f"Failed to start metrics server: {str(e)}")
        
        self.metrics_thread = threading.Thread(target=run_metrics_server)
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
    
    def start_system_metrics_collection(self):
        """Start collecting system metrics in a separate thread."""
        def collect_system_metrics():
            logger.info("Starting system metrics collection")
            while True:
                try:
                    # Collect CPU usage
                    cpu_percent = psutil.cpu_percent(interval=1)
                    SYSTEM_CPU_USAGE.set(cpu_percent)
                    
                    # Collect memory usage
                    memory = psutil.virtual_memory()
                    SYSTEM_MEMORY_USAGE.set(memory.used)
                    
                    # Sleep before next collection
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Error collecting system metrics: {str(e)}")
                    time.sleep(10)  # Longer sleep on error
        
        metrics_thread = threading.Thread(target=collect_system_metrics)
        metrics_thread.daemon = True
        metrics_thread.start()

def track_db_operation(operation, table):
    """
    Decorator to track database operation latency.
    
    Args:
        operation: Type of operation (e.g., 'select', 'insert', 'update', 'delete')
        table: Name of the database table
        
    Returns:
        Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            operation_time = time.time() - start_time
            
            DB_OPERATION_LATENCY.labels(
                operation=operation,
                table=table
            ).observe(operation_time)
            
            return result
        return wrapper
    return decorator

def track_gis_export_job(status, county, export_format):
    """
    Track a GIS export job.
    
    Args:
        status: Job status (e.g., 'created', 'completed', 'failed')
        county: County ID
        export_format: Export format (e.g., 'shapefile', 'geojson')
    """
    GIS_EXPORT_JOBS.labels(
        status=status,
        county=county,
        format=export_format
    ).inc()

def track_export_file_size(export_format, size_bytes):
    """
    Track the size of an export file.
    
    Args:
        export_format: Export format (e.g., 'shapefile', 'geojson')
        size_bytes: Size of the file in bytes
    """
    EXPORT_FILE_SIZE.labels(
        format=export_format
    ).observe(size_bytes)

def track_sync_job(status, county, source, target):
    """
    Track a sync job.
    
    Args:
        status: Job status (e.g., 'created', 'completed', 'failed')
        county: County ID
        source: Source system
        target: Target system
    """
    SYNC_JOBS.labels(
        status=status,
        county=county,
        source=source,
        target=target
    ).inc()

# Create a global monitoring instance
monitoring = TerraFusionMonitoring(disable_metrics_endpoint=True)