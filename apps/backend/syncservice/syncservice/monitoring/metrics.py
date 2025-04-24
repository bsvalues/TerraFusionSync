"""
Metrics collection for SyncService.

This module provides utilities for collecting and storing performance metrics
for the SyncService, including counters, gauges, and histograms.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import threading
import json
import os

logger = logging.getLogger(__name__)

# Global metrics registry
_metrics_registry = {}

# Thread lock for thread-safe metric updates
_metrics_lock = threading.Lock()

# Directory for storing metric data
_metrics_dir = 'data/metrics'

# Default retention period for metrics (in days)
DEFAULT_RETENTION_DAYS = 30


class MetricCounter:
    """A counter metric that only increases."""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Initialize a counter metric.
        
        Args:
            name: Name of the counter
            description: Description of what the counter measures
            labels: Optional list of label names that can be used with this counter
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values = {}  # Dict mapping label combinations to values
        self.created_at = datetime.utcnow()
        self.last_updated = self.created_at
    
    def inc(self, value: int = 1, **labels) -> None:
        """
        Increment the counter by the given value.
        
        Args:
            value: Value to increment by (default: 1)
            **labels: Label values keyed by label names
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Increment the counter
            if label_key not in self.values:
                self.values[label_key] = 0
            
            self.values[label_key] += value
            self.last_updated = datetime.utcnow()
    
    def get(self, **labels) -> int:
        """
        Get the current value of the counter.
        
        Args:
            **labels: Label values keyed by label names
            
        Returns:
            Current counter value
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Return the counter value or 0 if not found
            return self.values.get(label_key, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the counter to a dictionary.
        
        Returns:
            Dictionary representation of the counter
        """
        with _metrics_lock:
            # Convert label keys to strings
            values_dict = {}
            for label_key, value in self.values.items():
                if label_key:
                    key_str = ','.join(f"{k}={v}" for k, v in label_key)
                else:
                    key_str = 'default'
                
                values_dict[key_str] = value
            
            return {
                'name': self.name,
                'type': 'counter',
                'description': self.description,
                'labels': self.labels,
                'values': values_dict,
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat()
            }


class MetricGauge:
    """A gauge metric that can increase or decrease."""
    
    def __init__(self, name: str, description: str, labels: Optional[List[str]] = None):
        """
        Initialize a gauge metric.
        
        Args:
            name: Name of the gauge
            description: Description of what the gauge measures
            labels: Optional list of label names that can be used with this gauge
        """
        self.name = name
        self.description = description
        self.labels = labels or []
        self.values = {}  # Dict mapping label combinations to values
        self.created_at = datetime.utcnow()
        self.last_updated = self.created_at
    
    def set(self, value: float, **labels) -> None:
        """
        Set the gauge to the given value.
        
        Args:
            value: Value to set
            **labels: Label values keyed by label names
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Set the gauge value
            self.values[label_key] = value
            self.last_updated = datetime.utcnow()
    
    def inc(self, value: float = 1, **labels) -> None:
        """
        Increment the gauge by the given value.
        
        Args:
            value: Value to increment by (default: 1)
            **labels: Label values keyed by label names
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Increment the gauge
            if label_key not in self.values:
                self.values[label_key] = 0
            
            self.values[label_key] += value
            self.last_updated = datetime.utcnow()
    
    def dec(self, value: float = 1, **labels) -> None:
        """
        Decrement the gauge by the given value.
        
        Args:
            value: Value to decrement by (default: 1)
            **labels: Label values keyed by label names
        """
        self.inc(-value, **labels)
    
    def get(self, **labels) -> float:
        """
        Get the current value of the gauge.
        
        Args:
            **labels: Label values keyed by label names
            
        Returns:
            Current gauge value
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Return the gauge value or 0 if not found
            return self.values.get(label_key, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the gauge to a dictionary.
        
        Returns:
            Dictionary representation of the gauge
        """
        with _metrics_lock:
            # Convert label keys to strings
            values_dict = {}
            for label_key, value in self.values.items():
                if label_key:
                    key_str = ','.join(f"{k}={v}" for k, v in label_key)
                else:
                    key_str = 'default'
                
                values_dict[key_str] = value
            
            return {
                'name': self.name,
                'type': 'gauge',
                'description': self.description,
                'labels': self.labels,
                'values': values_dict,
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat()
            }


class MetricHistogram:
    """A histogram metric that records value distributions."""
    
    def __init__(self, name: str, description: str, buckets: List[float], labels: Optional[List[str]] = None):
        """
        Initialize a histogram metric.
        
        Args:
            name: Name of the histogram
            description: Description of what the histogram measures
            buckets: List of bucket boundaries (inclusive upper bounds)
            labels: Optional list of label names that can be used with this histogram
        """
        self.name = name
        self.description = description
        self.buckets = sorted(buckets)
        self.labels = labels or []
        self.values = {}  # Dict mapping (label_combo, bucket) to counts
        self.sums = {}  # Dict mapping label_combo to sum of observed values
        self.counts = {}  # Dict mapping label_combo to count of observed values
        self.created_at = datetime.utcnow()
        self.last_updated = self.created_at
    
    def observe(self, value: float, **labels) -> None:
        """
        Record a value observation.
        
        Args:
            value: Observed value
            **labels: Label values keyed by label names
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Update sum and count
            if label_key not in self.sums:
                self.sums[label_key] = 0
                self.counts[label_key] = 0
            
            self.sums[label_key] += value
            self.counts[label_key] += 1
            
            # Update bucket counts
            for bucket in self.buckets:
                bucket_key = (label_key, bucket)
                if bucket_key not in self.values:
                    self.values[bucket_key] = 0
                
                if value <= bucket:
                    self.values[bucket_key] += 1
            
            self.last_updated = datetime.utcnow()
    
    def get_bucket_count(self, bucket: float, **labels) -> int:
        """
        Get the count for a specific bucket.
        
        Args:
            bucket: Bucket upper bound
            **labels: Label values keyed by label names
            
        Returns:
            Bucket count
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Get bucket count
            bucket_key = (label_key, bucket)
            return self.values.get(bucket_key, 0)
    
    def get_sum(self, **labels) -> float:
        """
        Get the sum of observed values.
        
        Args:
            **labels: Label values keyed by label names
            
        Returns:
            Sum of observed values
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Get sum
            return self.sums.get(label_key, 0)
    
    def get_count(self, **labels) -> int:
        """
        Get the count of observed values.
        
        Args:
            **labels: Label values keyed by label names
            
        Returns:
            Count of observed values
        """
        with _metrics_lock:
            # Create a key from the labels
            if self.labels:
                label_key = tuple((k, labels.get(k, '')) for k in self.labels)
            else:
                label_key = ()
            
            # Get count
            return self.counts.get(label_key, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the histogram to a dictionary.
        
        Returns:
            Dictionary representation of the histogram
        """
        with _metrics_lock:
            # Convert to dictionary
            buckets_dict = {}
            sums_dict = {}
            counts_dict = {}
            
            # Process buckets
            for (label_key, bucket), count in self.values.items():
                if label_key:
                    key_str = ','.join(f"{k}={v}" for k, v in label_key)
                else:
                    key_str = 'default'
                
                if key_str not in buckets_dict:
                    buckets_dict[key_str] = {}
                
                buckets_dict[key_str][str(bucket)] = count
            
            # Process sums and counts
            for label_key, sum_value in self.sums.items():
                if label_key:
                    key_str = ','.join(f"{k}={v}" for k, v in label_key)
                else:
                    key_str = 'default'
                
                sums_dict[key_str] = sum_value
                counts_dict[key_str] = self.counts.get(label_key, 0)
            
            return {
                'name': self.name,
                'type': 'histogram',
                'description': self.description,
                'labels': self.labels,
                'buckets': self.buckets,
                'values': buckets_dict,
                'sums': sums_dict,
                'counts': counts_dict,
                'created_at': self.created_at.isoformat(),
                'last_updated': self.last_updated.isoformat()
            }


class MetricTimer:
    """A utility for timing operations and recording them in a histogram."""
    
    def __init__(self, histogram: MetricHistogram, **labels):
        """
        Initialize a timer.
        
        Args:
            histogram: Histogram to record timing in
            **labels: Labels to apply to the histogram
        """
        self.histogram = histogram
        self.labels = labels
        self.start_time = None
    
    def __enter__(self):
        """Start the timer."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the timer and record the elapsed time.
        
        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        """
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            self.histogram.observe(elapsed_time, **self.labels)


def create_counter(name: str, description: str, labels: Optional[List[str]] = None) -> MetricCounter:
    """
    Create a counter metric.
    
    Args:
        name: Name of the counter
        description: Description of what the counter measures
        labels: Optional list of label names that can be used with this counter
        
    Returns:
        Newly created counter
    """
    with _metrics_lock:
        if name in _metrics_registry:
            # Return existing counter
            metric = _metrics_registry[name]
            if not isinstance(metric, MetricCounter):
                raise ValueError(f"Metric {name} exists but is not a counter")
            return metric
        
        # Create new counter
        counter = MetricCounter(name, description, labels)
        _metrics_registry[name] = counter
        return counter


def create_gauge(name: str, description: str, labels: Optional[List[str]] = None) -> MetricGauge:
    """
    Create a gauge metric.
    
    Args:
        name: Name of the gauge
        description: Description of what the gauge measures
        labels: Optional list of label names that can be used with this gauge
        
    Returns:
        Newly created gauge
    """
    with _metrics_lock:
        if name in _metrics_registry:
            # Return existing gauge
            metric = _metrics_registry[name]
            if not isinstance(metric, MetricGauge):
                raise ValueError(f"Metric {name} exists but is not a gauge")
            return metric
        
        # Create new gauge
        gauge = MetricGauge(name, description, labels)
        _metrics_registry[name] = gauge
        return gauge


def create_histogram(
    name: str, 
    description: str, 
    buckets: List[float], 
    labels: Optional[List[str]] = None
) -> MetricHistogram:
    """
    Create a histogram metric.
    
    Args:
        name: Name of the histogram
        description: Description of what the histogram measures
        buckets: List of bucket boundaries (inclusive upper bounds)
        labels: Optional list of label names that can be used with this histogram
        
    Returns:
        Newly created histogram
    """
    with _metrics_lock:
        if name in _metrics_registry:
            # Return existing histogram
            metric = _metrics_registry[name]
            if not isinstance(metric, MetricHistogram):
                raise ValueError(f"Metric {name} exists but is not a histogram")
            return metric
        
        # Create new histogram
        histogram = MetricHistogram(name, description, buckets, labels)
        _metrics_registry[name] = histogram
        return histogram


def get_metric(name: str) -> Optional[Any]:
    """
    Get a metric by name.
    
    Args:
        name: Name of the metric
        
    Returns:
        Metric if found, None otherwise
    """
    with _metrics_lock:
        return _metrics_registry.get(name)


def get_all_metrics() -> Dict[str, Any]:
    """
    Get all registered metrics.
    
    Returns:
        Dictionary mapping metric names to metrics
    """
    with _metrics_lock:
        return dict(_metrics_registry)


def get_metrics_as_dict() -> Dict[str, Dict[str, Any]]:
    """
    Get all metrics as dictionaries.
    
    Returns:
        Dictionary mapping metric names to metric dictionaries
    """
    with _metrics_lock:
        return {name: metric.to_dict() for name, metric in _metrics_registry.items()}


def init_default_metrics():
    """Initialize default metrics for the SyncService."""
    # System metrics
    create_gauge(
        'system_memory_usage_bytes',
        'Memory usage in bytes',
    )
    
    create_gauge(
        'system_cpu_usage_percent',
        'CPU usage as a percentage',
    )
    
    # Sync operation metrics
    create_counter(
        'sync_operations_total',
        'Total number of sync operations',
        ['operation_type', 'source_system', 'target_system', 'status']
    )
    
    create_counter(
        'records_processed_total',
        'Total number of records processed',
        ['operation_type', 'source_system', 'target_system', 'entity_type']
    )
    
    create_counter(
        'records_succeeded_total',
        'Total number of records successfully processed',
        ['operation_type', 'source_system', 'target_system', 'entity_type']
    )
    
    create_counter(
        'records_failed_total',
        'Total number of records that failed processing',
        ['operation_type', 'source_system', 'target_system', 'entity_type', 'failure_reason']
    )
    
    # Performance metrics
    create_histogram(
        'sync_duration_seconds',
        'Duration of sync operations in seconds',
        [0.01, 0.1, 0.5, 1, 5, 10, 30, 60, 300, 600, 1800, 3600],
        ['operation_type', 'source_system', 'target_system']
    )
    
    create_histogram(
        'record_processing_duration_seconds',
        'Duration of record processing in seconds',
        [0.001, 0.01, 0.1, 0.5, 1, 5, 10, 30, 60],
        ['operation_type', 'source_system', 'target_system', 'entity_type']
    )
    
    # Database metrics
    create_gauge(
        'database_connections',
        'Number of active database connections',
        ['database_type']
    )
    
    create_histogram(
        'database_query_duration_seconds',
        'Duration of database queries in seconds',
        [0.001, 0.01, 0.1, 0.5, 1, 5, 10, 30, 60],
        ['database_type', 'query_type']
    )
    
    create_counter(
        'database_error_total',
        'Total number of database errors',
        ['database_type', 'error_type']
    )
    
    # API metrics
    create_counter(
        'api_requests_total',
        'Total number of API requests',
        ['endpoint', 'method', 'status_code']
    )
    
    create_histogram(
        'api_request_duration_seconds',
        'Duration of API requests in seconds',
        [0.001, 0.01, 0.1, 0.5, 1, 5, 10, 30, 60],
        ['endpoint', 'method']
    )


def store_metrics() -> None:
    """
    Store metrics to disk.
    
    This function serializes all metrics to JSON and stores them on disk.
    """
    # Create metrics directory if it doesn't exist
    os.makedirs(_metrics_dir, exist_ok=True)
    
    # Get current timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    # Serialize metrics to JSON
    metrics_dict = get_metrics_as_dict()
    metrics_json = json.dumps(metrics_dict, indent=2)
    
    # Write metrics to file
    file_path = os.path.join(_metrics_dir, f'metrics_{timestamp}.json')
    with open(file_path, 'w') as f:
        f.write(metrics_json)
    
    logger.info(f"Metrics stored to {file_path}")
    
    # Clean up old metric files
    cleanup_old_metrics()


def cleanup_old_metrics(retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
    """
    Clean up old metric files.
    
    Args:
        retention_days: Number of days to retain metric files
    """
    if not os.path.exists(_metrics_dir):
        return
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
    
    # Get all metric files
    for filename in os.listdir(_metrics_dir):
        if not filename.startswith('metrics_') or not filename.endswith('.json'):
            continue
        
        file_path = os.path.join(_metrics_dir, filename)
        file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        # Delete old files
        if file_mtime < cutoff_date:
            try:
                os.remove(file_path)
                logger.debug(f"Deleted old metric file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete old metric file {file_path}: {str(e)}")


def load_metrics() -> None:
    """
    Load metrics from disk.
    
    This function loads the most recent metrics from disk and registers them.
    """
    if not os.path.exists(_metrics_dir):
        return
    
    # Find the most recent metric file
    metric_files = [f for f in os.listdir(_metrics_dir) if f.startswith('metrics_') and f.endswith('.json')]
    if not metric_files:
        return
    
    # Sort by filename (timestamp)
    metric_files.sort(reverse=True)
    latest_file = os.path.join(_metrics_dir, metric_files[0])
    
    try:
        # Load metrics from file
        with open(latest_file, 'r') as f:
            metrics_dict = json.loads(f.read())
        
        # Register metrics
        with _metrics_lock:
            for name, metric_dict in metrics_dict.items():
                metric_type = metric_dict.get('type')
                if metric_type == 'counter':
                    # Create counter
                    counter = MetricCounter(
                        name=metric_dict['name'],
                        description=metric_dict['description'],
                        labels=metric_dict.get('labels', [])
                    )
                    
                    # Set values
                    for label_str, value in metric_dict.get('values', {}).items():
                        if label_str == 'default':
                            counter.values[()] = value
                        else:
                            # Parse label string
                            labels = {}
                            for label_pair in label_str.split(','):
                                key, val = label_pair.split('=', 1)
                                labels[key] = val
                            
                            # Create label key
                            label_key = tuple((k, labels.get(k, '')) for k in counter.labels)
                            counter.values[label_key] = value
                    
                    # Set timestamps
                    counter.created_at = datetime.fromisoformat(metric_dict.get('created_at', datetime.utcnow().isoformat()))
                    counter.last_updated = datetime.fromisoformat(metric_dict.get('last_updated', datetime.utcnow().isoformat()))
                    
                    # Register counter
                    _metrics_registry[name] = counter
                
                elif metric_type == 'gauge':
                    # Create gauge
                    gauge = MetricGauge(
                        name=metric_dict['name'],
                        description=metric_dict['description'],
                        labels=metric_dict.get('labels', [])
                    )
                    
                    # Set values
                    for label_str, value in metric_dict.get('values', {}).items():
                        if label_str == 'default':
                            gauge.values[()] = value
                        else:
                            # Parse label string
                            labels = {}
                            for label_pair in label_str.split(','):
                                key, val = label_pair.split('=', 1)
                                labels[key] = val
                            
                            # Create label key
                            label_key = tuple((k, labels.get(k, '')) for k in gauge.labels)
                            gauge.values[label_key] = value
                    
                    # Set timestamps
                    gauge.created_at = datetime.fromisoformat(metric_dict.get('created_at', datetime.utcnow().isoformat()))
                    gauge.last_updated = datetime.fromisoformat(metric_dict.get('last_updated', datetime.utcnow().isoformat()))
                    
                    # Register gauge
                    _metrics_registry[name] = gauge
                
                elif metric_type == 'histogram':
                    # Create histogram
                    histogram = MetricHistogram(
                        name=metric_dict['name'],
                        description=metric_dict['description'],
                        buckets=metric_dict.get('buckets', []),
                        labels=metric_dict.get('labels', [])
                    )
                    
                    # Set bucket values
                    for label_str, buckets in metric_dict.get('values', {}).items():
                        if label_str == 'default':
                            label_key = ()
                        else:
                            # Parse label string
                            labels = {}
                            for label_pair in label_str.split(','):
                                key, val = label_pair.split('=', 1)
                                labels[key] = val
                            
                            # Create label key
                            label_key = tuple((k, labels.get(k, '')) for k in histogram.labels)
                        
                        # Set bucket values
                        for bucket_str, count in buckets.items():
                            bucket = float(bucket_str)
                            bucket_key = (label_key, bucket)
                            histogram.values[bucket_key] = count
                    
                    # Set sums and counts
                    for label_str, sum_value in metric_dict.get('sums', {}).items():
                        if label_str == 'default':
                            label_key = ()
                        else:
                            # Parse label string
                            labels = {}
                            for label_pair in label_str.split(','):
                                key, val = label_pair.split('=', 1)
                                labels[key] = val
                            
                            # Create label key
                            label_key = tuple((k, labels.get(k, '')) for k in histogram.labels)
                        
                        # Set sum and count
                        histogram.sums[label_key] = sum_value
                        histogram.counts[label_key] = metric_dict.get('counts', {}).get(label_str, 0)
                    
                    # Set timestamps
                    histogram.created_at = datetime.fromisoformat(metric_dict.get('created_at', datetime.utcnow().isoformat()))
                    histogram.last_updated = datetime.fromisoformat(metric_dict.get('last_updated', datetime.utcnow().isoformat()))
                    
                    # Register histogram
                    _metrics_registry[name] = histogram
        
        logger.info(f"Loaded metrics from {latest_file}")
    except Exception as e:
        logger.error(f"Failed to load metrics from {latest_file}: {str(e)}")


# Initialize default metrics
init_default_metrics()

# Try to load metrics from disk
try:
    load_metrics()
except Exception as e:
    logger.error(f"Failed to load metrics: {str(e)}")