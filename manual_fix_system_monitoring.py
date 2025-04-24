"""
Manual fix for the system monitoring component.

This script manually creates safer instances of the system monitoring component
with proper defensive programming to avoid NoneType errors.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SafeSystemMonitor:
    """
    Monitor system resources with enhanced error handling.
    This implementation provides robust fallbacks for all operations.
    """
    
    def __init__(self):
        """Initialize the safe system monitor."""
        self.last_metrics = {}
        self.last_update_time = None
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health with robust error handling.
        
        Returns:
            Dictionary with system health metrics or safe fallback values
        """
        try:
            # Basic metrics with timestamp
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "status": "OK"
            }
            
            # Safe CPU metrics
            try:
                import psutil
                cpu_percent = psutil.cpu_percent(interval=0.5)
                metrics["cpu_count"] = psutil.cpu_count() or 0
                metrics["cpu_percent"] = cpu_percent
            except Exception as e:
                logger.warning(f"Error getting CPU metrics: {str(e)}")
                metrics["cpu_percent"] = 0
                metrics["cpu_count"] = 0
                metrics["cpu_error"] = str(e)
            
            # Safe Memory metrics
            try:
                import psutil
                mem = psutil.virtual_memory()
                metrics["memory_total"] = getattr(mem, 'total', 0)
                metrics["memory_available"] = getattr(mem, 'available', 0)
                metrics["memory_used"] = getattr(mem, 'used', 0)
                metrics["memory_percent"] = getattr(mem, 'percent', 0)
            except Exception as e:
                logger.warning(f"Error getting memory metrics: {str(e)}")
                metrics["memory_percent"] = 0
                metrics["memory_error"] = str(e)
            
            # Safe Disk metrics
            try:
                import psutil
                disk = psutil.disk_usage('/')
                metrics["disk_total"] = getattr(disk, 'total', 0)
                metrics["disk_used"] = getattr(disk, 'used', 0)
                metrics["disk_free"] = getattr(disk, 'free', 0)
                metrics["disk_percent"] = getattr(disk, 'percent', 0)
            except Exception as e:
                logger.warning(f"Error getting disk metrics: {str(e)}")
                metrics["disk_percent"] = 0
                metrics["disk_error"] = str(e)
            
            # Process info (safely)
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                process_mem = process.memory_info()
                metrics["process_memory_rss"] = getattr(process_mem, 'rss', 0)
                metrics["process_memory_vms"] = getattr(process_mem, 'vms', 0)
                metrics["process_cpu_percent"] = process.cpu_percent(interval=None)
                metrics["process_threads"] = len(process.threads())
                metrics["process_connections"] = len(process.connections(kind='all'))
            except Exception as e:
                logger.warning(f"Error getting process metrics: {str(e)}")
                metrics["process_error"] = str(e)
            
            # System boot time (safely)
            try:
                import psutil
                metrics["boot_time"] = datetime.fromtimestamp(psutil.boot_time()).isoformat()
            except Exception as e:
                logger.warning(f"Error getting boot time: {str(e)}")
                metrics["boot_time_error"] = str(e)
            
            # Save metrics for reference
            self.last_metrics = metrics
            self.last_update_time = datetime.utcnow()
            
            return metrics
            
        except Exception as e:
            logger.error(f"Unexpected error in get_system_health: {str(e)}", exc_info=True)
            # Return minimal system health info on error
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "ERROR",
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0
            }
    
    def get_as_json(self) -> str:
        """
        Get the system health as a JSON string.
        
        Returns:
            JSON string representation of system health
        """
        try:
            metrics = self.get_system_health()
            return json.dumps(metrics, indent=2)
        except Exception as e:
            logger.error(f"Error converting metrics to JSON: {str(e)}")
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "status": "ERROR"
            }, indent=2)

def main():
    """
    Run a test of the safe system monitor.
    """
    monitor = SafeSystemMonitor()
    
    # Get and display system health
    print("System Health:")
    metrics = monitor.get_system_health()
    print(monitor.get_as_json())
    
    # Log key metrics
    cpu = metrics.get('cpu_percent', 0)
    memory = metrics.get('memory_percent', 0)
    disk = metrics.get('disk_percent', 0)
    print(f"\nKey Metrics: CPU {cpu}%, Memory {memory}%, Disk {disk}%")

    # Save metrics to a file
    with open('system_health.json', 'w') as f:
        f.write(monitor.get_as_json())
    print("\nSystem health saved to system_health.json")

if __name__ == '__main__':
    main()