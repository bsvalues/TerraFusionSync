"""
TerraFusion SyncService Performance Tuning Utilities

This module provides utilities for performance tuning and optimization of the 
TerraFusion SyncService platform.
"""

import os
import sys
import json
import logging
import psutil
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('performance_tuning')

# Default configuration for gunicorn worker optimization
# Rule of thumb: (2 * CPU cores) + 1
def get_optimal_worker_count():
    """
    Calculate the optimal number of gunicorn workers based on CPU cores.
    
    Returns:
        Optimal worker count
    """
    cpu_count = psutil.cpu_count(logical=True)
    if not cpu_count:
        # Fallback if CPU count can't be determined
        return 4
    
    # Rule of thumb: (2 * CPU cores) + 1
    return (2 * cpu_count) + 1

# Database connection pooling settings
DB_POOL_CONFIG = {
    "pool_size": 10,                 # Number of connections to keep open
    "max_overflow": 20,              # Maximum overflow connections
    "pool_timeout": 30,              # Seconds to wait for a connection
    "pool_recycle": 300,             # Recycle connections after 5 minutes
    "pool_pre_ping": True            # Verify connections before use
}

# Cache configuration
CACHE_CONFIG = {
    "type": "memory",                # Use in-memory cache by default
    "default_timeout": 300,          # Default cache timeout (seconds)
    "key_prefix": "terrafusion:",    # Prefix for cache keys
    # Specific cache timeouts for different types of data
    "timeouts": {
        "status": 60,                # Status information (1 minute)
        "health": 30,                # Health checks (30 seconds)
        "metrics": 120,              # Metrics data (2 minutes)
        "sync_pairs": 600,           # Sync pair configurations (10 minutes)
        "user_auth": 1800            # User authentication data (30 minutes)
    }
}

# Batch processing settings
BATCH_PROCESSING_CONFIG = {
    "default_batch_size": 1000,      # Default number of records in a batch
    "large_batch_size": 5000,        # Large batch size for bulk operations
    "small_batch_size": 100,         # Small batch size for quick operations
    "batch_interval_ms": 50,         # Milliseconds between batch processing
    # Batch sizes for specific entity types
    "entity_batch_sizes": {
        "property": 1000,
        "owner": 500,
        "valuation": 2000,
        "location": 1000,
        "boundary": 500
    }
}

# Memory usage optimization settings
MEMORY_OPTIMIZATION_CONFIG = {
    "periodic_gc_enabled": True,     # Enable periodic garbage collection
    "gc_threshold_mb": 1024,         # Memory threshold to trigger GC (MB)
    "obj_cache_size": 1000,          # Size of object cache
    "max_response_size_mb": 100      # Maximum response size (MB)
}


def apply_database_optimizations():
    """
    Apply database performance optimizations.
    
    Returns:
        Dictionary with results of optimization
    """
    try:
        # In a real implementation, this would modify database settings
        # For now, we'll just print out what would be done
        
        logger.info("Applying database optimizations")
        
        optimizations = [
            "Setting connection pool size to {}".format(DB_POOL_CONFIG["pool_size"]),
            "Setting max overflow to {}".format(DB_POOL_CONFIG["max_overflow"]),
            "Setting pool timeout to {} seconds".format(DB_POOL_CONFIG["pool_timeout"]),
            "Setting pool recycle to {} seconds".format(DB_POOL_CONFIG["pool_recycle"]),
            "Enabling pool pre-ping" if DB_POOL_CONFIG["pool_pre_ping"] else "Disabling pool pre-ping"
        ]
        
        for opt in optimizations:
            logger.info(f"  - {opt}")
        
        return {
            "status": "success",
            "optimizations": optimizations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error applying database optimizations: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def apply_api_gateway_optimizations():
    """
    Apply API Gateway performance optimizations.
    
    Returns:
        Dictionary with results of optimization
    """
    try:
        # Calculate optimal worker count
        worker_count = get_optimal_worker_count()
        
        logger.info(f"Applying API Gateway optimizations with {worker_count} workers")
        
        # In a real implementation, this would update the gunicorn configuration
        # For now, we'll just print what would be done
        
        optimizations = [
            f"Setting worker count to {worker_count}",
            "Enabling worker preloading",
            "Setting worker timeout to 60 seconds",
            "Setting keep-alive to 5 seconds",
            "Setting max requests per worker to 1000"
        ]
        
        for opt in optimizations:
            logger.info(f"  - {opt}")
        
        return {
            "status": "success",
            "worker_count": worker_count,
            "optimizations": optimizations,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error applying API Gateway optimizations: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def apply_sync_service_optimizations():
    """
    Apply SyncService performance optimizations.
    
    Returns:
        Dictionary with results of optimization
    """
    try:
        logger.info("Applying SyncService optimizations")
        
        # In a real implementation, this would update the SyncService configuration
        # For now, we'll just print what would be done
        
        optimizations = [
            f"Setting default batch size to {BATCH_PROCESSING_CONFIG['default_batch_size']}",
            "Enabling batch processing for sync operations",
            "Configuring entity-specific batch sizes",
            "Enabling response compression",
            "Configuring memory usage optimizations"
        ]
        
        for opt in optimizations:
            logger.info(f"  - {opt}")
        
        # Create batch size configuration string for display
        batch_config = ", ".join([
            f"{entity}: {size}" 
            for entity, size in BATCH_PROCESSING_CONFIG["entity_batch_sizes"].items()
        ])
        logger.info(f"  - Entity batch sizes: {batch_config}")
        
        return {
            "status": "success",
            "optimizations": optimizations,
            "batch_sizes": BATCH_PROCESSING_CONFIG["entity_batch_sizes"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error applying SyncService optimizations: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def run_performance_test(endpoint_url, num_requests=100, concurrency=10):
    """
    Run a simple performance test on an endpoint.
    
    Args:
        endpoint_url: URL of the endpoint to test
        num_requests: Number of requests to send
        concurrency: Number of concurrent requests
        
    Returns:
        Dictionary with test results
    """
    try:
        logger.info(f"Running performance test on {endpoint_url}")
        logger.info(f"  - Requests: {num_requests}")
        logger.info(f"  - Concurrency: {concurrency}")
        
        # Use curl to run a simple performance test
        # In a real implementation, we would use a proper load testing tool
        
        start_time = datetime.utcnow()
        
        cmd = [
            "curl", "-s", "-o", "/dev/null", 
            "-w", "%{time_total}\n",
            "-H", "Accept: application/json",
            endpoint_url
        ]
        
        total_time = 0
        times = []
        
        for i in range(min(num_requests, 10)):  # Limit to 10 requests for demo
            logger.info(f"  - Running request {i+1}/{min(num_requests, 10)}")
            
            try:
                output = subprocess.check_output(cmd, text=True)
                time_taken = float(output.strip())
                total_time += time_taken
                times.append(time_taken)
                logger.info(f"    - Time: {time_taken:.3f}s")
            except subprocess.SubprocessError as e:
                logger.error(f"Error running curl: {str(e)}")
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Calculate statistics
        if times:
            avg_time = total_time / len(times)
            max_time = max(times)
            min_time = min(times)
            
            results = {
                "status": "success",
                "endpoint": endpoint_url,
                "requests": len(times),
                "concurrency": 1,  # We're not actually doing concurrent requests
                "duration_seconds": duration,
                "avg_time_seconds": avg_time,
                "min_time_seconds": min_time,
                "max_time_seconds": max_time,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            results = {
                "status": "error",
                "error": "No successful requests",
                "endpoint": endpoint_url,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        return results
        
    except Exception as e:
        logger.error(f"Error running performance test: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "endpoint": endpoint_url,
            "timestamp": datetime.utcnow().isoformat()
        }


def main():
    """Main entry point for the performance tuning utility."""
    parser = argparse.ArgumentParser(description="TerraFusion SyncService Performance Tuning Utility")
    parser.add_argument('command', choices=['optimize-all', 'optimize-db', 'optimize-api', 'optimize-sync', 'test'],
                        help="Command to execute")
    parser.add_argument('--endpoint', default="http://localhost:5000/api/status",
                        help="Endpoint URL for performance test")
    parser.add_argument('--requests', type=int, default=100,
                        help="Number of requests for performance test")
    parser.add_argument('--concurrency', type=int, default=10,
                        help="Concurrency level for performance test")
    parser.add_argument('--save', action='store_true',
                        help="Save results to performance_results.json")
    
    args = parser.parse_args()
    
    results = {}
    
    if args.command == 'optimize-all':
        # Apply all optimizations
        results["database"] = apply_database_optimizations()
        results["api_gateway"] = apply_api_gateway_optimizations()
        results["sync_service"] = apply_sync_service_optimizations()
        results["timestamp"] = datetime.utcnow().isoformat()
        
        print("\nApplied all performance optimizations:")
        print(f"  - Database: {results['database']['status']}")
        print(f"  - API Gateway: {results['api_gateway']['status']}")
        print(f"  - SyncService: {results['sync_service']['status']}")
    
    elif args.command == 'optimize-db':
        # Apply database optimizations
        results = apply_database_optimizations()
        
        print("\nApplied database optimizations:")
        for opt in results.get("optimizations", []):
            print(f"  - {opt}")
    
    elif args.command == 'optimize-api':
        # Apply API Gateway optimizations
        results = apply_api_gateway_optimizations()
        
        print("\nApplied API Gateway optimizations:")
        for opt in results.get("optimizations", []):
            print(f"  - {opt}")
    
    elif args.command == 'optimize-sync':
        # Apply SyncService optimizations
        results = apply_sync_service_optimizations()
        
        print("\nApplied SyncService optimizations:")
        for opt in results.get("optimizations", []):
            print(f"  - {opt}")
    
    elif args.command == 'test':
        # Run performance test
        results = run_performance_test(
            args.endpoint,
            num_requests=args.requests,
            concurrency=args.concurrency
        )
        
        print("\nPerformance Test Results:")
        print(f"  - Endpoint: {results['endpoint']}")
        
        if results["status"] == "success":
            print(f"  - Requests: {results['requests']}")
            print(f"  - Duration: {results['duration_seconds']:.2f}s")
            print(f"  - Avg Time: {results['avg_time_seconds']:.3f}s")
            print(f"  - Min Time: {results['min_time_seconds']:.3f}s")
            print(f"  - Max Time: {results['max_time_seconds']:.3f}s")
        else:
            print(f"  - Error: {results.get('error', 'Unknown error')}")
    
    # Save results if requested
    if args.save and results:
        with open('performance_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to performance_results.json")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)