"""
Prometheus Metrics Module for TerraFusion SyncService.

This module provides Prometheus metrics instrumentation for the TerraFusion
API Gateway and SyncService components.
"""

import time
from typing import Callable, Dict, List, Optional
from functools import wraps

# Using direct import pattern for cleaner error handling in case prometheus_client isn't available
try:
    import prometheus_client
    from prometheus_client import Counter, Gauge, Histogram, Summary, multiprocess, CollectorRegistry
    from prometheus_client.exposition import generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Create dummy classes and functions for graceful degradation
    class DummyMetric:
        def __init__(self, *args, **kwargs):
            # Initialize with any arguments, but just ignore them
            pass
            
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def time(self): 
            return DummyContextManager()
    
    class DummyContextManager:
        def __enter__(self): pass
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        
    Counter = Gauge = Histogram = Summary = DummyMetric
    multiprocess = None
    generate_latest = lambda x: b''
    CONTENT_TYPE_LATEST = 'text/plain'
    CollectorRegistry = object


# Create a registry
registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None

# Define metrics
# API Gateway metrics
REQUEST_COUNT = Counter(
    'terrafusion_request_total', 
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

REQUEST_LATENCY = Histogram(
    'terrafusion_request_latency_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    registry=registry,
    buckets=(0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, float('inf')),
)

REQUEST_IN_PROGRESS = Gauge(
    'terrafusion_requests_in_progress',
    'Number of HTTP requests in progress',
    ['method', 'endpoint'],
    registry=registry
)

ERROR_COUNT = Counter(
    'terrafusion_errors_total',
    'Total number of errors',
    ['type', 'code', 'message'],
    registry=registry
)

# Sync operation metrics
SYNC_OPERATIONS_TOTAL = Counter(
    'terrafusion_sync_operations_total',
    'Total number of sync operations started',
    ['type', 'source', 'target'],
    registry=registry
)

SYNC_OPERATIONS_FAILED = Counter(
    'terrafusion_sync_operations_failed',
    'Number of failed sync operations',
    ['type', 'source', 'target', 'reason'],
    registry=registry
)

SYNC_OPERATION_DURATION = Histogram(
    'terrafusion_sync_operation_duration_seconds',
    'Duration of sync operations in seconds',
    ['type', 'source', 'target'],
    registry=registry,
    buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600, 7200, float('inf')),
)

RECORDS_PROCESSED = Counter(
    'terrafusion_records_processed_total',
    'Total number of records processed',
    ['type', 'source', 'target', 'result'],
    registry=registry
)

# System metrics
SYSTEM_CPU_USAGE = Gauge(
    'terrafusion_system_cpu_usage',
    'Current CPU usage percentage',
    registry=registry
)

SYSTEM_MEMORY_USAGE = Gauge(
    'terrafusion_system_memory_usage',
    'Current memory usage percentage',
    registry=registry
)

SYSTEM_DISK_USAGE = Gauge(
    'terrafusion_system_disk_usage',
    'Current disk usage percentage',
    registry=registry
)

ACTIVE_CONNECTIONS = Gauge(
    'terrafusion_active_connections',
    'Number of active connections',
    registry=registry
)


def record_metrics_for_sync_operation(
    operation_type: str,
    source_system: str,
    target_system: str,
    duration_seconds: float,
    total_records: int,
    successful_records: int,
    failed_records: int,
    error_message: Optional[str] = None
):
    """
    Record metrics for a sync operation.
    
    Args:
        operation_type: Type of operation (full or incremental)
        source_system: Source system name
        target_system: Target system name
        duration_seconds: Duration of the operation in seconds
        total_records: Total number of records processed
        successful_records: Number of records successfully processed
        failed_records: Number of records that failed processing
        error_message: Error message if the operation failed
    """
    if not PROMETHEUS_AVAILABLE:
        return
        
    # Increment operation counter
    SYNC_OPERATIONS_TOTAL.labels(
        type=operation_type,
        source=source_system,
        target=target_system
    ).inc()
    
    # Record operation duration
    SYNC_OPERATION_DURATION.labels(
        type=operation_type,
        source=source_system,
        target=target_system
    ).observe(duration_seconds)
    
    # Record successful records
    if successful_records > 0:
        RECORDS_PROCESSED.labels(
            type=operation_type,
            source=source_system,
            target=target_system,
            result='success'
        ).inc(successful_records)
    
    # Record failed records
    if failed_records > 0:
        RECORDS_PROCESSED.labels(
            type=operation_type,
            source=source_system,
            target=target_system,
            result='failed'
        ).inc(failed_records)
        
        if error_message:
            SYNC_OPERATIONS_FAILED.labels(
                type=operation_type,
                source=source_system,
                target=target_system,
                reason=error_message[:100]  # Truncate long error messages
            ).inc()


def record_system_metrics(
    cpu_usage: float,
    memory_usage: float,
    disk_usage: float,
    active_connections: int
):
    """
    Record system metrics.
    
    Args:
        cpu_usage: CPU usage percentage
        memory_usage: Memory usage percentage
        disk_usage: Disk usage percentage
        active_connections: Number of active connections
    """
    if not PROMETHEUS_AVAILABLE:
        return
        
    SYSTEM_CPU_USAGE.set(cpu_usage)
    SYSTEM_MEMORY_USAGE.set(memory_usage)
    SYSTEM_DISK_USAGE.set(disk_usage)
    ACTIVE_CONNECTIONS.set(active_connections)


def flask_metrics_middleware(app):
    """
    Middleware for Flask to record request metrics.
    
    Args:
        app: Flask application
    """
    if not PROMETHEUS_AVAILABLE:
        return
        
    @app.before_request
    def before_request():
        request = app.current_request
        endpoint = request.endpoint or 'unknown'
        method = request.method
        
        # Increment in-progress requests
        REQUEST_IN_PROGRESS.labels(
            method=method,
            endpoint=endpoint
        ).inc()
        
        # Store the start time in the request context
        request.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        request = app.current_request
        endpoint = request.endpoint or 'unknown'
        method = request.method
        status = response.status_code
        
        # Calculate request duration
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            REQUEST_LATENCY.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        # Count the request
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        # Decrement in-progress requests
        REQUEST_IN_PROGRESS.labels(
            method=method,
            endpoint=endpoint
        ).dec()
        
        return response
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        error_type = type(e).__name__
        error_message = str(e)
        error_code = getattr(e, 'code', 500)
        
        ERROR_COUNT.labels(
            type=error_type,
            code=error_code,
            message=error_message[:100]  # Truncate long error messages
        ).inc()
        
        # Let Flask handle the exception normally
        return app.handle_user_exception(e)


def track_time(name, labels=None):
    """
    Decorator to track time spent in a function.
    
    Args:
        name: Name of the metric
        labels: Dict of labels to apply to the metric
    
    Returns:
        Decorator function
    """
    if not PROMETHEUS_AVAILABLE:
        def dummy_decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper
        return dummy_decorator
    
    # Create a Summary metric
    metric = Summary(
        f'terrafusion_{name}_duration_seconds',
        f'Time spent in {name} function',
        list(labels.keys()) if labels else [],
        registry=registry
    )
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if labels:
                label_values = {k: v for k, v in labels.items()}
                with metric.labels(**label_values).time():
                    return f(*args, **kwargs)
            else:
                with metric.time():
                    return f(*args, **kwargs)
        return wrapper
    
    return decorator


def metrics_endpoint():
    """
    Return metrics in Prometheus format.
    
    Returns:
        Tuple of (metrics_data, content_type)
    """
    if not PROMETHEUS_AVAILABLE:
        return b'# Prometheus metrics not available', 'text/plain'
    
    return generate_latest(registry), CONTENT_TYPE_LATEST