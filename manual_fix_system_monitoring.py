"""
Manual fix for the system monitoring component.

This script manually creates safer instances of the system monitoring component
with proper defensive programming to avoid NoneType errors.
"""

import os
import time
import logging
import platform
from datetime import datetime
from typing import Dict, Any, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil module not available, using fallback metrics")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SafeSystemMonitor:
    """
    Monitor system resources with enhanced error handling.
    This implementation provides robust fallbacks for all operations.
    """
    
    def __init__(self):
        """Initialize the safe system monitor."""
        self.last_update = datetime.utcnow()
        self.health_metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "active_connections": 0,
            "response_time": 0.0,
            "error_count": 0,
            "sync_operations_count": 0,
            "status": "healthy",
            "last_check": self.last_update.isoformat()
        }
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get current system health with robust error handling.
        
        Returns:
            Dictionary with system health metrics or safe fallback values
        """
        metrics = self.health_metrics.copy()
        
        try:
            # Update timestamp
            self.last_update = datetime.utcnow()
            metrics["last_check"] = self.last_update.isoformat()
            
            # Skip actual metrics collection if psutil is not available
            if not PSUTIL_AVAILABLE:
                metrics["status"] = "limited"
                metrics["status_message"] = "psutil module not available, using fallback metrics"
                return metrics
            
            # Get CPU usage with defensive check
            try:
                metrics["cpu_usage"] = psutil.cpu_percent(interval=0.1)
            except Exception as e:
                logger.warning(f"Error getting CPU usage: {str(e)}")
                metrics["cpu_usage"] = self.health_metrics.get("cpu_usage", 0.0)
            
            # Get memory usage with defensive check
            try:
                memory = psutil.virtual_memory()
                metrics["memory_usage"] = memory.percent
            except Exception as e:
                logger.warning(f"Error getting memory usage: {str(e)}")
                metrics["memory_usage"] = self.health_metrics.get("memory_usage", 0.0)
            
            # Get disk usage with defensive check
            try:
                disk = psutil.disk_usage('/')
                metrics["disk_usage"] = disk.percent
            except Exception as e:
                logger.warning(f"Error getting disk usage: {str(e)}")
                metrics["disk_usage"] = self.health_metrics.get("disk_usage", 0.0)
            
            # Get active connections with defensive check
            try:
                metrics["active_connections"] = len(psutil.net_connections(kind='inet'))
            except (psutil.AccessDenied, PermissionError):
                # This is normal in some environments
                logger.info("Permission denied when getting network connections")
                metrics["active_connections"] = 0
            except Exception as e:
                logger.warning(f"Error getting active connections: {str(e)}")
                metrics["active_connections"] = self.health_metrics.get("active_connections", 0)
            
            # Determine system status based on metrics
            metrics["status"] = "healthy"
            if metrics["cpu_usage"] > 90 or metrics["memory_usage"] > 90 or metrics["disk_usage"] > 90:
                metrics["status"] = "warning"
                metrics["status_message"] = "System resources under high load"
            
            # Update the cached metrics
            self.health_metrics = metrics.copy()
            
            return metrics
        except Exception as e:
            logger.error(f"Unexpected error in get_system_health: {str(e)}")
            # Return at least the timestamp and error info
            metrics["status"] = "error"
            metrics["status_message"] = f"Error collecting metrics: {str(e)}"
            metrics["last_check"] = datetime.utcnow().isoformat()
            return metrics
    
    def get_as_json(self) -> str:
        """
        Get the system health as a JSON string.
        
        Returns:
            JSON string representation of system health
        """
        import json
        try:
            return json.dumps(self.get_system_health())
        except Exception as e:
            logger.error(f"Error converting metrics to JSON: {str(e)}")
            return json.dumps({"status": "error", "message": str(e)})


# Create a singleton instance for easy import
safe_monitor = SafeSystemMonitor()


def get_safe_system_info() -> Dict[str, str]:
    """
    Get basic system information with robust error handling.
    
    Returns:
        Dictionary with basic system information or safe fallback values
    """
    info = {
        "platform": "unknown",
        "python_version": "unknown",
        "processor": "unknown",
        "hostname": "unknown",
        "start_time": datetime.utcnow().isoformat()
    }
    
    # Get basic platform information with defensive checks
    try:
        info["platform"] = platform.platform()
    except Exception:
        pass
    
    try:
        info["python_version"] = platform.python_version()
    except Exception:
        pass
    
    try:
        info["processor"] = platform.processor() or "unknown"
    except Exception:
        pass
    
    try:
        info["hostname"] = platform.node() or "unknown"
    except Exception:
        pass
    
    # Get psutil-dependent information
    if PSUTIL_AVAILABLE:
        try:
            info["cpu_count"] = str(psutil.cpu_count(logical=True) or "N/A")
        except Exception:
            info["cpu_count"] = "N/A"
        
        try:
            info["physical_cpu_count"] = str(psutil.cpu_count(logical=False) or "N/A")
        except Exception:
            info["physical_cpu_count"] = "N/A"
        
        try:
            memory = psutil.virtual_memory()
            info["total_memory"] = f"{memory.total / (1024**3):.2f} GB"
        except Exception:
            info["total_memory"] = "N/A"
    else:
        info["cpu_count"] = "N/A"
        info["physical_cpu_count"] = "N/A"
        info["total_memory"] = "N/A"
    
    return info


def main():
    """
    Run a test of the safe system monitor.
    """
    monitor = SafeSystemMonitor()
    
    print("\nSafe System Monitor Test\n" + "="*25)
    print("\nSystem information:")
    system_info = get_safe_system_info()
    for key, value in system_info.items():
        print(f"  {key}: {value}")
    
    print("\nHealth metrics:")
    metrics = monitor.get_system_health()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\nJSON representation:")
    print(monitor.get_as_json())
    
    print("\nTest complete. All operations completed safely.")


if __name__ == "__main__":
    main()