"""
Metrics collection and management for SyncService.

This module provides utilities for collecting, storing, and retrieving metrics data
about the SyncService operations and performance.
"""

import os
import json
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Callable

logger = logging.getLogger(__name__)

# Thread lock for metrics operations
_metrics_lock = threading.RLock()

# Metrics storage
_counters = {}  # name -> {description, value, labels}
_gauges = {}    # name -> {description, value, labels}
_histograms = {}  # name -> {description, buckets, values, counts, sums, labels}

# Directory for metrics persistence
METRICS_DIR = os.environ.get('METRICS_DIR', os.path.join('data', 'metrics'))

# Ensure metrics directory exists
os.makedirs(METRICS_DIR, exist_ok=True)


# Counter operations
def create_counter(name: str, description: str, initial_value: int = 0,
                  labels: Optional[Dict[str, str]] = None) -> None:
    """
    Create a new counter with the given name and description.
    
    Args:
        name: Counter name
        description: Counter description
        initial_value: Initial counter value
        labels: Optional labels for the counter
    """
    with _metrics_lock:
        if name in _counters:
            logger.warning(f"Counter {name} already exists, not creating again")
            return
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if name not in _counters:
            _counters[name] = {
                "description": description,
                "values": {},
                "labels": {}
            }
        
        _counters[name]["values"][label_str] = initial_value
        if labels:
            _counters[name]["labels"][label_str] = labels


def increment_counter(name: str, value: int = 1, labels: Optional[Dict[str, str]] = None) -> None:
    """
    Increment a counter by the given value.
    
    Args:
        name: Counter name
        value: Value to increment by
        labels: Optional labels for the counter
    """
    with _metrics_lock:
        if name not in _counters:
            logger.warning(f"Counter {name} does not exist, creating with default description")
            create_counter(name, f"Counter for {name}", 0, labels)
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _counters[name]["values"]:
            _counters[name]["values"][label_str] = 0
            if labels:
                _counters[name]["labels"][label_str] = labels
        
        _counters[name]["values"][label_str] += value


def get_counter_value(name: str, labels: Optional[Dict[str, str]] = None) -> Optional[int]:
    """
    Get the current value of a counter.
    
    Args:
        name: Counter name
        labels: Optional labels to identify the counter
        
    Returns:
        Current counter value or None if counter doesn't exist
    """
    with _metrics_lock:
        if name not in _counters:
            return None
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _counters[name]["values"]:
            return None
        
        return _counters[name]["values"][label_str]


# Gauge operations
def create_gauge(name: str, description: str, initial_value: float = 0.0,
                labels: Optional[Dict[str, str]] = None) -> None:
    """
    Create a new gauge with the given name and description.
    
    Args:
        name: Gauge name
        description: Gauge description
        initial_value: Initial gauge value
        labels: Optional labels for the gauge
    """
    with _metrics_lock:
        if name in _gauges:
            logger.warning(f"Gauge {name} already exists, not creating again")
            return
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if name not in _gauges:
            _gauges[name] = {
                "description": description,
                "values": {},
                "labels": {}
            }
        
        _gauges[name]["values"][label_str] = initial_value
        if labels:
            _gauges[name]["labels"][label_str] = labels


def update_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """
    Update a gauge to the given value.
    
    Args:
        name: Gauge name
        value: New gauge value
        labels: Optional labels for the gauge
    """
    with _metrics_lock:
        if name not in _gauges:
            logger.warning(f"Gauge {name} does not exist, creating with default description")
            create_gauge(name, f"Gauge for {name}", value, labels)
            return
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _gauges[name]["values"]:
            _gauges[name]["values"][label_str] = 0.0
            if labels:
                _gauges[name]["labels"][label_str] = labels
        
        _gauges[name]["values"][label_str] = value


def get_gauge_value(name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
    """
    Get the current value of a gauge.
    
    Args:
        name: Gauge name
        labels: Optional labels to identify the gauge
        
    Returns:
        Current gauge value or None if gauge doesn't exist
    """
    with _metrics_lock:
        if name not in _gauges:
            return None
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _gauges[name]["values"]:
            return None
        
        return _gauges[name]["values"][label_str]


# Histogram operations
def create_histogram(name: str, description: str, buckets: List[float],
                    labels: Optional[Dict[str, str]] = None) -> None:
    """
    Create a new histogram with the given name, description, and buckets.
    
    Args:
        name: Histogram name
        description: Histogram description
        buckets: List of bucket boundaries
        labels: Optional labels for the histogram
    """
    with _metrics_lock:
        if name in _histograms:
            logger.warning(f"Histogram {name} already exists, not creating again")
            return
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if name not in _histograms:
            _histograms[name] = {
                "description": description,
                "buckets": buckets,
                "values": {},  # label_str -> values array
                "counts": {},  # label_str -> count
                "sums": {},    # label_str -> sum
                "labels": {}   # label_str -> labels dict
            }
        
        _histograms[name]["values"][label_str] = [0] * (len(buckets) + 1)  # +1 for +Inf bucket
        _histograms[name]["counts"][label_str] = 0
        _histograms[name]["sums"][label_str] = 0.0
        if labels:
            _histograms[name]["labels"][label_str] = labels


def observe_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """
    Record an observation in a histogram.
    
    Args:
        name: Histogram name
        value: Observed value
        labels: Optional labels for the histogram
    """
    with _metrics_lock:
        if name not in _histograms:
            logger.warning(f"Histogram {name} does not exist")
            return
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _histograms[name]["values"]:
            # Create new label dimension if this label hasn't been seen before
            _histograms[name]["values"][label_str] = [0] * (len(_histograms[name]["buckets"]) + 1)
            _histograms[name]["counts"][label_str] = 0
            _histograms[name]["sums"][label_str] = 0.0
            if labels:
                _histograms[name]["labels"][label_str] = labels
        
        # Increment bucket counts
        bucket_idx = len(_histograms[name]["buckets"])  # Default to +Inf bucket
        for i, boundary in enumerate(_histograms[name]["buckets"]):
            if value <= boundary:
                bucket_idx = i
                break
        
        _histograms[name]["values"][label_str][bucket_idx] += 1
        _histograms[name]["counts"][label_str] += 1
        _histograms[name]["sums"][label_str] += value


def get_histogram_buckets(name: str) -> Optional[List[float]]:
    """
    Get the bucket boundaries for a histogram.
    
    Args:
        name: Histogram name
        
    Returns:
        List of bucket boundaries or None if histogram doesn't exist
    """
    with _metrics_lock:
        if name not in _histograms:
            return None
        
        return _histograms[name]["buckets"]


def get_histogram_values(name: str, labels: Optional[Dict[str, str]] = None) -> Optional[List[int]]:
    """
    Get the current bucket values for a histogram.
    
    Args:
        name: Histogram name
        labels: Optional labels to identify the histogram
        
    Returns:
        List of bucket values or None if histogram doesn't exist
    """
    with _metrics_lock:
        if name not in _histograms:
            return None
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _histograms[name]["values"]:
            return None
        
        return _histograms[name]["values"][label_str]


def get_histogram_sum(name: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
    """
    Get the current sum for a histogram.
    
    Args:
        name: Histogram name
        labels: Optional labels to identify the histogram
        
    Returns:
        Current sum or None if histogram doesn't exist
    """
    with _metrics_lock:
        if name not in _histograms:
            return None
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _histograms[name]["sums"]:
            return None
        
        return _histograms[name]["sums"][label_str]


def get_histogram_count(name: str, labels: Optional[Dict[str, str]] = None) -> Optional[int]:
    """
    Get the current count for a histogram.
    
    Args:
        name: Histogram name
        labels: Optional labels to identify the histogram
        
    Returns:
        Current count or None if histogram doesn't exist
    """
    with _metrics_lock:
        if name not in _histograms:
            return None
        
        label_str = "default"
        if labels:
            label_str = ",".join([f"{k}={v}" for k, v in labels.items()])
        
        if label_str not in _histograms[name]["counts"]:
            return None
        
        return _histograms[name]["counts"][label_str]


# Get all metrics as dictionary
def get_metrics_as_dict() -> Dict[str, Any]:
    """
    Get all metrics as a dictionary.
    
    Returns:
        Dictionary of all metrics
    """
    with _metrics_lock:
        return {
            **{name: {"type": "counter", "description": info["description"], "values": info["values"]}
               for name, info in _counters.items()},
            **{name: {"type": "gauge", "description": info["description"], "values": info["values"]}
               for name, info in _gauges.items()},
            **{name: {"type": "histogram", "description": info["description"],
                    "buckets": info["buckets"], "values": info["values"],
                    "counts": info["counts"], "sums": info["sums"]}
               for name, info in _histograms.items()}
        }


# Save metrics to disk (persistence)
def save_metrics_to_disk() -> None:
    """
    Save all metrics to disk for persistence.
    """
    try:
        with _metrics_lock:
            metrics_data = {
                "counters": _counters,
                "gauges": _gauges,
                "histograms": _histograms
            }
            
            metrics_file = os.path.join(METRICS_DIR, "metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
            
            logger.debug(f"Metrics saved to {metrics_file}")
    except Exception as e:
        logger.error(f"Error saving metrics to disk: {str(e)}")


# Load metrics from disk (persistence)
def load_metrics_from_disk() -> bool:
    """
    Load metrics from disk.
    
    Returns:
        True if metrics were loaded successfully, False otherwise
    """
    global _counters, _gauges, _histograms
    
    try:
        metrics_file = os.path.join(METRICS_DIR, "metrics.json")
        
        if not os.path.exists(metrics_file):
            logger.info(f"Metrics file {metrics_file} does not exist, starting with empty metrics")
            return False
        
        with open(metrics_file, 'r') as f:
            metrics_data = json.load(f)
        
        with _metrics_lock:
            _counters = metrics_data.get("counters", {})
            _gauges = metrics_data.get("gauges", {})
            _histograms = metrics_data.get("histograms", {})
        
        logger.info(f"Metrics loaded from {metrics_file}")
        return True
    except Exception as e:
        logger.error(f"Error loading metrics from disk: {str(e)}")
        return False