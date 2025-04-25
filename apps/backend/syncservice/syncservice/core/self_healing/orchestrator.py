"""
Self-healing orchestrator for the TerraFusion SyncService platform.

This module provides the main orchestrator that coordinates self-healing
activities, including circuit breakers, retry strategies, and recovery operations.
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Tuple, Set
from datetime import datetime, timedelta

from .circuit_breaker import CircuitBreaker
from .retry_strategy import RetryStrategy, ExponentialBackoffStrategy

logger = logging.getLogger(__name__)


class ResourceStatus:
    """Status of a monitored resource."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILING = "failing"
    RECOVERING = "recovering"


class SelfHealingOrchestrator:
    """
    Orchestrator for self-healing operations.
    
    This class coordinates circuit breakers, retry strategies, and recovery
    operations for different components of the system.
    """
    
    def __init__(self):
        """Initialize a new self-healing orchestrator."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        self.resource_monitors: Dict[str, Callable[[], bool]] = {}
        self.recovery_handlers: Dict[str, Callable[[], bool]] = {}
        self.status_history: Dict[str, List[Tuple[datetime, str]]] = {}
        self.health_check_intervals: Dict[str, int] = {}
        self.last_health_check: Dict[str, datetime] = {}
        self.resource_dependencies: Dict[str, Set[str]] = {}
        
        # Lock for thread safety
        self._lock = threading.RLock()
        
        # Start the health check thread
        self._stop_health_check = threading.Event()
        self._health_check_thread = None
        
        logger.info("Self-healing orchestrator initialized")
    
    def register_circuit_breaker(
        self,
        resource_id: str,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_max_calls: int = 1,
        excluded_exceptions: Optional[List[type]] = None
    ) -> CircuitBreaker:
        """
        Register a circuit breaker for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            failure_threshold: Number of consecutive failures before opening the circuit
            reset_timeout: Seconds to wait before attempting to close the circuit again
            half_open_max_calls: Maximum number of calls to allow in half-open state
            excluded_exceptions: Exceptions that should not count as failures
            
        Returns:
            The created circuit breaker
        """
        with self._lock:
            circuit_breaker = CircuitBreaker(
                name=resource_id,
                failure_threshold=failure_threshold,
                reset_timeout_seconds=reset_timeout,
                half_open_max_calls=half_open_max_calls,
                excluded_exceptions=excluded_exceptions
            )
            self.circuit_breakers[resource_id] = circuit_breaker
            logger.info(f"Registered circuit breaker for resource: {resource_id}")
            
            # Initialize status history
            if resource_id not in self.status_history:
                self.status_history[resource_id] = [(datetime.utcnow(), ResourceStatus.HEALTHY)]
            
            return circuit_breaker
    
    def register_retry_strategy(
        self,
        resource_id: str,
        strategy_type: str = "exponential",
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs
    ) -> RetryStrategy:
        """
        Register a retry strategy for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            strategy_type: Type of retry strategy ('exponential' or 'linear')
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            **kwargs: Additional parameters for the specific strategy
            
        Returns:
            The created retry strategy
        """
        with self._lock:
            if strategy_type.lower() == "exponential":
                multiplier = kwargs.get("multiplier", 2.0)
                jitter_factor = kwargs.get("jitter_factor", 0.2)
                retryable_exceptions = kwargs.get("retryable_exceptions", None)
                
                strategy = ExponentialBackoffStrategy(
                    base_delay=base_delay,
                    max_delay=max_delay,
                    multiplier=multiplier,
                    jitter_factor=jitter_factor,
                    retryable_exceptions=retryable_exceptions
                )
            else:
                raise ValueError(f"Unsupported retry strategy type: {strategy_type}")
            
            self.retry_strategies[resource_id] = strategy
            logger.info(f"Registered {strategy_type} retry strategy for resource: {resource_id}")
            
            return strategy
    
    def register_resource_monitor(
        self,
        resource_id: str,
        monitor_func: Callable[[], bool],
        health_check_interval: int = 60,
        dependencies: Optional[List[str]] = None
    ):
        """
        Register a health check function for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            monitor_func: Function that returns True if the resource is healthy
            health_check_interval: Interval in seconds between health checks
            dependencies: List of resource IDs that this resource depends on
        """
        with self._lock:
            self.resource_monitors[resource_id] = monitor_func
            self.health_check_intervals[resource_id] = health_check_interval
            self.last_health_check[resource_id] = datetime.utcnow() - timedelta(seconds=health_check_interval)
            
            # Initialize status history if not already present
            if resource_id not in self.status_history:
                self.status_history[resource_id] = [(datetime.utcnow(), ResourceStatus.HEALTHY)]
            
            # Register dependencies
            if dependencies:
                self.resource_dependencies[resource_id] = set(dependencies)
                logger.info(f"Resource {resource_id} depends on: {', '.join(dependencies)}")
            else:
                self.resource_dependencies[resource_id] = set()
            
            logger.info(f"Registered resource monitor for: {resource_id} with interval {health_check_interval}s")
    
    def register_recovery_handler(
        self,
        resource_id: str,
        recovery_func: Callable[[], bool]
    ):
        """
        Register a recovery function for a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            recovery_func: Function that attempts to recover the resource,
                           returns True if recovery was successful
        """
        with self._lock:
            self.recovery_handlers[resource_id] = recovery_func
            logger.info(f"Registered recovery handler for resource: {resource_id}")
    
    def start_health_monitoring(self, interval: int = 30):
        """
        Start the health monitoring thread.
        
        Args:
            interval: Interval in seconds to run the health check loop
        """
        if self._health_check_thread and self._health_check_thread.is_alive():
            logger.warning("Health monitoring thread already running")
            return
        
        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_check_loop,
            args=(interval,),
            daemon=True
        )
        self._health_check_thread.start()
        logger.info(f"Started health monitoring thread with interval {interval}s")
    
    def stop_health_monitoring(self):
        """Stop the health monitoring thread."""
        if not self._health_check_thread or not self._health_check_thread.is_alive():
            logger.warning("Health monitoring thread not running")
            return
        
        self._stop_health_check.set()
        self._health_check_thread.join(timeout=5.0)
        logger.info("Stopped health monitoring thread")
    
    def _health_check_loop(self, interval: int):
        """
        Main health check loop.
        
        Args:
            interval: Interval in seconds to run the health check loop
        """
        logger.info("Health check loop started")
        
        while not self._stop_health_check.is_set():
            try:
                self.check_all_resources()
            except Exception as e:
                logger.error(f"Error in health check loop: {str(e)}")
            
            # Wait for the next interval or until stopped
            self._stop_health_check.wait(interval)
    
    def check_all_resources(self):
        """Check the health of all registered resources."""
        with self._lock:
            now = datetime.utcnow()
            
            # Top-down approach: check resources with no dependencies first
            resources_to_check = []
            resource_dependencies = self.resource_dependencies.copy()
            
            # Find resources that are due for a health check
            due_resources = {
                resource_id for resource_id in self.resource_monitors
                if (now - self.last_health_check.get(resource_id, datetime.min)).total_seconds() 
                >= self.health_check_intervals.get(resource_id, 60)
            }
            
            # Build a list of resources to check in dependency order
            while due_resources:
                # Find resources with no pending dependencies
                independent_resources = {
                    resource_id for resource_id in due_resources
                    if not resource_dependencies.get(resource_id, set())
                }
                
                if not independent_resources:
                    # Circular dependency detected, log and break
                    logger.warning(f"Circular dependency detected in resources: {due_resources}")
                    break
                
                # Add independent resources to the check list
                resources_to_check.extend(independent_resources)
                
                # Remove checked resources from the pending list
                due_resources -= independent_resources
                
                # Remove checked resources from dependencies
                for deps in resource_dependencies.values():
                    deps -= independent_resources
            
            # Now check the resources in order
            for resource_id in resources_to_check:
                try:
                    self.check_resource(resource_id)
                except Exception as e:
                    logger.error(f"Error checking resource {resource_id}: {str(e)}")
                finally:
                    self.last_health_check[resource_id] = now
    
    def check_resource(self, resource_id: str) -> bool:
        """
        Check the health of a specific resource.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            True if the resource is healthy, False otherwise
        """
        if resource_id not in self.resource_monitors:
            logger.warning(f"No monitor registered for resource: {resource_id}")
            return False
        
        monitor_func = self.resource_monitors[resource_id]
        circuit_breaker = self.circuit_breakers.get(resource_id)
        retry_strategy = self.retry_strategies.get(resource_id)
        
        # Determine current status
        current_status = self.get_resource_status(resource_id)
        
        try:
            # Execute the monitor function with circuit breaker protection if available
            if circuit_breaker:
                try:
                    if retry_strategy:
                        # Use both circuit breaker and retry strategy
                        result = circuit_breaker.execute(
                            lambda: retry_strategy.execute_with_retry(
                                monitor_func,
                                max_attempts=3,
                                on_retry_callback=lambda attempt, exc: logger.warning(
                                    f"Retry {attempt} for resource {resource_id} after error: {str(exc)}"
                                )
                            )
                        )
                    else:
                        # Use only circuit breaker
                        result = circuit_breaker.execute(monitor_func)
                except Exception as e:
                    logger.warning(f"Health check failed for resource {resource_id}: {str(e)}")
                    result = False
            else:
                # No circuit breaker, use retry strategy if available
                if retry_strategy:
                    try:
                        result = retry_strategy.execute_with_retry(
                            monitor_func,
                            max_attempts=3,
                            on_retry_callback=lambda attempt, exc: logger.warning(
                                f"Retry {attempt} for resource {resource_id} after error: {str(exc)}"
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Health check failed for resource {resource_id}: {str(e)}")
                        result = False
                else:
                    # No circuit breaker or retry strategy
                    result = monitor_func()
            
            # Update status based on result
            if result:
                if current_status != ResourceStatus.HEALTHY:
                    self._update_resource_status(resource_id, ResourceStatus.HEALTHY)
                    logger.info(f"Resource {resource_id} is now HEALTHY")
            else:
                if current_status == ResourceStatus.HEALTHY:
                    self._update_resource_status(resource_id, ResourceStatus.DEGRADED)
                    logger.warning(f"Resource {resource_id} is now DEGRADED")
                elif current_status == ResourceStatus.DEGRADED:
                    self._update_resource_status(resource_id, ResourceStatus.FAILING)
                    logger.error(f"Resource {resource_id} is now FAILING")
                
                # Attempt recovery if the resource is failing
                if self.get_resource_status(resource_id) == ResourceStatus.FAILING:
                    self._initiate_recovery(resource_id)
            
            return result
        except Exception as e:
            logger.error(f"Error monitoring resource {resource_id}: {str(e)}")
            
            # Update status to failing on exception
            if current_status != ResourceStatus.FAILING:
                self._update_resource_status(resource_id, ResourceStatus.FAILING)
                logger.error(f"Resource {resource_id} is now FAILING due to exception: {str(e)}")
                
                # Attempt recovery
                self._initiate_recovery(resource_id)
            
            return False
    
    def _initiate_recovery(self, resource_id: str):
        """
        Initiate recovery for a failing resource.
        
        Args:
            resource_id: Unique identifier for the resource
        """
        if resource_id not in self.recovery_handlers:
            logger.warning(f"No recovery handler registered for resource: {resource_id}")
            return
        
        # Update status to recovering
        self._update_resource_status(resource_id, ResourceStatus.RECOVERING)
        logger.info(f"Initiating recovery for resource: {resource_id}")
        
        recovery_func = self.recovery_handlers[resource_id]
        retry_strategy = self.retry_strategies.get(resource_id, 
                                                 ExponentialBackoffStrategy(
                                                     base_delay=1.0,
                                                     max_delay=30.0,
                                                     multiplier=2.0,
                                                     jitter_factor=0.2
                                                 ))
        
        # Execute the recovery function with retry
        try:
            success = retry_strategy.execute_with_retry(
                recovery_func,
                max_attempts=3,
                on_retry_callback=lambda attempt, exc: logger.warning(
                    f"Retry {attempt} for recovery of resource {resource_id} after error: {str(exc)}"
                )
            )
            
            if success:
                logger.info(f"Recovery successful for resource: {resource_id}")
                self._update_resource_status(resource_id, ResourceStatus.HEALTHY)
                
                # Reset the circuit breaker if one exists
                circuit_breaker = self.circuit_breakers.get(resource_id)
                if circuit_breaker:
                    circuit_breaker.reset()
                    logger.info(f"Reset circuit breaker for resource: {resource_id}")
            else:
                logger.error(f"Recovery failed for resource: {resource_id}")
                self._update_resource_status(resource_id, ResourceStatus.FAILING)
        except Exception as e:
            logger.error(f"Error during recovery for resource {resource_id}: {str(e)}")
            self._update_resource_status(resource_id, ResourceStatus.FAILING)
    
    def _update_resource_status(self, resource_id: str, status: str):
        """
        Update the status of a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            status: New status
        """
        with self._lock:
            # Initialize history if needed
            if resource_id not in self.status_history:
                self.status_history[resource_id] = []
            
            # Add the new status
            self.status_history[resource_id].append((datetime.utcnow(), status))
            
            # Limit history size
            if len(self.status_history[resource_id]) > 100:
                self.status_history[resource_id] = self.status_history[resource_id][-100:]
    
    def get_resource_status(self, resource_id: str) -> str:
        """
        Get the current status of a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            Current status of the resource, or HEALTHY if no status is available
        """
        with self._lock:
            if resource_id not in self.status_history or not self.status_history[resource_id]:
                return ResourceStatus.HEALTHY
            
            return self.status_history[resource_id][-1][1]
    
    def get_status_history(self, resource_id: str) -> List[Tuple[datetime, str]]:
        """
        Get the status history of a resource.
        
        Args:
            resource_id: Unique identifier for the resource
            
        Returns:
            List of (timestamp, status) tuples
        """
        with self._lock:
            if resource_id not in self.status_history:
                return []
            
            return self.status_history[resource_id].copy()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the orchestrator and its components.
        
        Returns:
            Dictionary with orchestrator metrics
        """
        with self._lock:
            metrics = {
                "resources": {}
            }
            
            for resource_id in set(self.resource_monitors.keys()) | set(self.circuit_breakers.keys()):
                resource_metrics = {
                    "status": self.get_resource_status(resource_id),
                    "last_check": self.last_health_check.get(resource_id, "never").isoformat() 
                                if isinstance(self.last_health_check.get(resource_id), datetime) else "never",
                    "check_interval": self.health_check_intervals.get(resource_id),
                    "dependencies": list(self.resource_dependencies.get(resource_id, set())),
                    "has_monitor": resource_id in self.resource_monitors,
                    "has_recovery": resource_id in self.recovery_handlers
                }
                
                # Add circuit breaker metrics if available
                if resource_id in self.circuit_breakers:
                    circuit_breaker = self.circuit_breakers[resource_id]
                    resource_metrics["circuit_breaker"] = circuit_breaker.get_metrics()
                
                # Add retry strategy metrics if available
                if resource_id in self.retry_strategies:
                    retry_strategy = self.retry_strategies[resource_id]
                    resource_metrics["retry_strategy"] = retry_strategy.get_metrics()
                
                metrics["resources"][resource_id] = resource_metrics
            
            return metrics