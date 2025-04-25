"""
Self-healing orchestrator for the TerraFusion SyncService platform.

This module provides the main orchestrator for the self-healing functionality,
coordinating circuit breakers, retry strategies, and health checks.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union

from .circuit_breaker import CircuitBreaker, CircuitOpenError
from .retry_strategy import (
    BaseRetryStrategy,
    ExponentialWithJitterRetryStrategy,
    RetryStrategyType,
    create_retry_strategy
)

T = TypeVar('T')
logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of resources that can be monitored and self-healed."""
    SYNC_PAIR = "sync_pair"
    SOURCE_SYSTEM = "source_system"
    TARGET_SYSTEM = "target_system"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"


class HealthStatus(Enum):
    """Possible health statuses for monitored resources."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheck:
    """Health check configuration and status tracking."""
    
    def __init__(
        self,
        resource_type: ResourceType,
        resource_id: str,
        check_function: Callable[[], bool],
        description: str,
        interval_seconds: int = 60,
        failure_threshold: int = 3,
        recovery_threshold: int = 2
    ):
        """
        Initialize a health check.
        
        Args:
            resource_type: Type of resource being checked
            resource_id: Identifier for the specific resource
            check_function: Function that returns True if healthy, False otherwise
            description: Human-readable description of the health check
            interval_seconds: How often to run the check in seconds
            failure_threshold: Number of consecutive failures before marking unhealthy
            recovery_threshold: Number of consecutive successes before marking healthy
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.check_function = check_function
        self.description = description
        self.interval_seconds = interval_seconds
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        
        # Status tracking
        self.status = HealthStatus.UNKNOWN
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time = None
        self.last_status_change_time = datetime.utcnow()
        self.total_checks = 0
        self.total_failures = 0
    
    def should_check(self) -> bool:
        """
        Determine if it's time to run this health check again.
        
        Returns:
            True if the check should be run, False otherwise
        """
        if not self.last_check_time:
            return True
        
        elapsed = (datetime.utcnow() - self.last_check_time).total_seconds()
        return elapsed >= self.interval_seconds
    
    def run_check(self) -> HealthStatus:
        """
        Run the health check and update status.
        
        Returns:
            The current HealthStatus after running the check
        """
        self.last_check_time = datetime.utcnow()
        self.total_checks += 1
        
        try:
            is_healthy = self.check_function()
            
            if is_healthy:
                self.consecutive_successes += 1
                self.consecutive_failures = 0
                
                # If we've reached the recovery threshold, mark as healthy
                if (self.status != HealthStatus.HEALTHY and 
                    self.consecutive_successes >= self.recovery_threshold):
                    self._transition_to(HealthStatus.HEALTHY)
                
                logger.info(f"Health check '{self.description}' passed "
                           f"({self.consecutive_successes}/{self.recovery_threshold} "
                           f"consecutive successes)")
            else:
                self.consecutive_failures += 1
                self.consecutive_successes = 0
                self.total_failures += 1
                
                # Update status based on consecutive failures
                if self.consecutive_failures >= self.failure_threshold:
                    if self.status == HealthStatus.HEALTHY:
                        self._transition_to(HealthStatus.DEGRADED)
                    elif self.status == HealthStatus.DEGRADED:
                        self._transition_to(HealthStatus.UNHEALTHY)
                
                logger.warning(f"Health check '{self.description}' failed "
                             f"({self.consecutive_failures}/{self.failure_threshold} "
                             f"consecutive failures)")
            
            return self.status
            
        except Exception as e:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.total_failures += 1
            
            # Update status based on consecutive failures
            if self.consecutive_failures >= self.failure_threshold:
                if self.status == HealthStatus.HEALTHY:
                    self._transition_to(HealthStatus.DEGRADED)
                elif self.status == HealthStatus.DEGRADED:
                    self._transition_to(HealthStatus.UNHEALTHY)
            
            logger.error(f"Health check '{self.description}' raised exception: {str(e)}"
                        f"({self.consecutive_failures}/{self.failure_threshold} "
                        f"consecutive failures)")
            
            return self.status
    
    def _transition_to(self, new_status: HealthStatus) -> None:
        """
        Transition to a new health status.
        
        Args:
            new_status: The new health status
        """
        old_status = self.status
        self.status = new_status
        self.last_status_change_time = datetime.utcnow()
        
        logger.info(f"Health check '{self.description}' status changed from "
                  f"{old_status.value} to {new_status.value}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the health check.
        
        Returns:
            Dictionary with health check metrics
        """
        uptime = None
        if self.status == HealthStatus.HEALTHY and self.last_status_change_time:
            uptime = (datetime.utcnow() - self.last_status_change_time).total_seconds()
        
        return {
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "description": self.description,
            "status": self.status.value,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "failure_rate": (self.total_failures / self.total_checks) 
                          if self.total_checks > 0 else 0.0,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "last_status_change_time": self.last_status_change_time.isoformat() 
                                     if self.last_status_change_time else None,
            "uptime_seconds": uptime
        }
    
    def reset(self) -> None:
        """Reset the health check state."""
        self.status = HealthStatus.UNKNOWN
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.last_check_time = None
        self.last_status_change_time = datetime.utcnow()


class SelfHealingOrchestrator:
    """
    Orchestrate self-healing capabilities across the SyncService.
    
    This class coordinates circuit breakers, retry strategies, and health checks
    to provide comprehensive self-healing capabilities.
    """
    
    def __init__(self):
        """Initialize the self-healing orchestrator."""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[str, BaseRetryStrategy] = {}
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Recovery actions registry
        self.recovery_actions: Dict[
            Tuple[ResourceType, str], Callable[[ResourceType, str, HealthStatus], bool]
        ] = {}
        
        # Tracking for recovery attempts
        self.recovery_attempts: Dict[Tuple[ResourceType, str], List[datetime]] = {}
        self.recovery_cooldowns: Dict[Tuple[ResourceType, str], datetime] = {}
        
        # Default settings
        self.default_circuit_breaker_settings = {
            "failure_threshold": 5,
            "reset_timeout": 30,
            "half_open_success_threshold": 1
        }
        
        self.default_retry_strategy_settings = {
            "strategy_type": RetryStrategyType.EXPONENTIAL_WITH_JITTER,
            "max_retries": 3,
            "initial_wait_time": 1.0,
            "base": 2.0,
            "max_wait_time": 60.0,
            "jitter_factor": 0.2
        }
        
        logger.info("Self-healing orchestrator initialized")
    
    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = None,
        reset_timeout: int = None,
        half_open_success_threshold: int = None,
        monitored_exceptions: List[type] = None,
        on_open_callback: Optional[Callable[[str], None]] = None,
        on_close_callback: Optional[Callable[[str], None]] = None
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker.
        
        Args:
            name: Unique name for the circuit breaker
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Seconds to wait before attempting to close circuit
            half_open_success_threshold: Number of successes in half-open state
                required to close the circuit
            monitored_exceptions: List of exception types to monitor
            on_open_callback: Callback to execute when circuit transitions to open
            on_close_callback: Callback to execute when circuit transitions to closed
            
        Returns:
            The created CircuitBreaker instance
            
        Raises:
            ValueError: If a circuit breaker with this name already exists
        """
        if name in self.circuit_breakers:
            raise ValueError(f"Circuit breaker '{name}' already exists")
        
        # Use default values if not provided
        if failure_threshold is None:
            failure_threshold = self.default_circuit_breaker_settings["failure_threshold"]
        
        if reset_timeout is None:
            reset_timeout = self.default_circuit_breaker_settings["reset_timeout"]
        
        if half_open_success_threshold is None:
            half_open_success_threshold = self.default_circuit_breaker_settings["half_open_success_threshold"]
        
        # Create the circuit breaker
        cb = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            reset_timeout=reset_timeout,
            half_open_success_threshold=half_open_success_threshold,
            monitored_exceptions=monitored_exceptions,
            on_open_callback=on_open_callback,
            on_close_callback=on_close_callback
        )
        
        self.circuit_breakers[name] = cb
        logger.info(f"Registered circuit breaker '{name}'")
        
        return cb
    
    def register_retry_strategy(
        self,
        name: str,
        strategy_type: Union[str, RetryStrategyType] = None,
        **kwargs
    ) -> BaseRetryStrategy:
        """
        Register a new retry strategy.
        
        Args:
            name: Unique name for the retry strategy
            strategy_type: Type of retry strategy to create
            **kwargs: Additional arguments for the retry strategy
            
        Returns:
            The created retry strategy instance
            
        Raises:
            ValueError: If a retry strategy with this name already exists
        """
        if name in self.retry_strategies:
            raise ValueError(f"Retry strategy '{name}' already exists")
        
        # Use default strategy type if not provided
        if strategy_type is None:
            strategy_type = self.default_retry_strategy_settings["strategy_type"]
        
        # Merge default settings with provided kwargs
        settings = self.default_retry_strategy_settings.copy()
        settings.update(kwargs)
        
        # Remove strategy_type from settings as it's passed separately
        if "strategy_type" in settings:
            del settings["strategy_type"]
        
        # Create the retry strategy
        strategy = create_retry_strategy(strategy_type, **settings)
        
        self.retry_strategies[name] = strategy
        logger.info(f"Registered retry strategy '{name}' of type {strategy.__class__.__name__}")
        
        return strategy
    
    def register_health_check(
        self,
        resource_type: Union[str, ResourceType],
        resource_id: str,
        check_function: Callable[[], bool],
        description: str,
        interval_seconds: int = 60,
        failure_threshold: int = 3,
        recovery_threshold: int = 2
    ) -> HealthCheck:
        """
        Register a new health check.
        
        Args:
            resource_type: Type of resource being checked
            resource_id: Identifier for the specific resource
            check_function: Function that returns True if healthy, False otherwise
            description: Human-readable description of the health check
            interval_seconds: How often to run the check in seconds
            failure_threshold: Number of consecutive failures before marking unhealthy
            recovery_threshold: Number of consecutive successes before marking healthy
            
        Returns:
            The created HealthCheck instance
            
        Raises:
            ValueError: If a health check for this resource already exists
        """
        # Convert string to enum if needed
        if isinstance(resource_type, str):
            try:
                resource_type = ResourceType[resource_type.upper()]
            except KeyError:
                valid_types = ", ".join(s.name for s in ResourceType)
                raise ValueError(f"Unknown resource type: {resource_type}. "
                                f"Valid types are: {valid_types}")
        
        # Create a unique key for this health check
        key = f"{resource_type.value}:{resource_id}"
        
        if key in self.health_checks:
            raise ValueError(f"Health check for {resource_type.value} '{resource_id}' already exists")
        
        # Create the health check
        hc = HealthCheck(
            resource_type=resource_type,
            resource_id=resource_id,
            check_function=check_function,
            description=description,
            interval_seconds=interval_seconds,
            failure_threshold=failure_threshold,
            recovery_threshold=recovery_threshold
        )
        
        self.health_checks[key] = hc
        logger.info(f"Registered health check for {resource_type.value} '{resource_id}': {description}")
        
        return hc
    
    def register_recovery_action(
        self,
        resource_type: Union[str, ResourceType],
        resource_id: str,
        recovery_function: Callable[[ResourceType, str, HealthStatus], bool],
        cooldown_seconds: int = 300  # 5 minutes default cooldown
    ) -> None:
        """
        Register a recovery action for a resource.
        
        Args:
            resource_type: Type of resource to recover
            resource_id: Identifier for the specific resource
            recovery_function: Function to call for recovery that returns True if successful
            cooldown_seconds: Minimum time between recovery attempts in seconds
            
        Raises:
            ValueError: If resource_type is not valid
        """
        # Convert string to enum if needed
        if isinstance(resource_type, str):
            try:
                resource_type = ResourceType[resource_type.upper()]
            except KeyError:
                valid_types = ", ".join(s.name for s in ResourceType)
                raise ValueError(f"Unknown resource type: {resource_type}. "
                                f"Valid types are: {valid_types}")
        
        key = (resource_type, resource_id)
        self.recovery_actions[key] = recovery_function
        
        # Initialize tracking for this resource
        if key not in self.recovery_attempts:
            self.recovery_attempts[key] = []
        
        # Set initial cooldown (if any)
        if cooldown_seconds > 0:
            self.recovery_cooldowns[key] = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
        
        logger.info(f"Registered recovery action for {resource_type.value} '{resource_id}'")
    
    def unregister_recovery_action(
        self,
        resource_type: Union[str, ResourceType],
        resource_id: str
    ) -> bool:
        """
        Unregister a recovery action.
        
        Args:
            resource_type: Type of resource
            resource_id: Identifier for the specific resource
            
        Returns:
            True if the recovery action was removed, False if it didn't exist
        """
        # Convert string to enum if needed
        if isinstance(resource_type, str):
            try:
                resource_type = ResourceType[resource_type.upper()]
            except KeyError:
                return False
        
        key = (resource_type, resource_id)
        
        if key in self.recovery_actions:
            del self.recovery_actions[key]
            
            # Clean up tracking data as well
            if key in self.recovery_attempts:
                del self.recovery_attempts[key]
            
            if key in self.recovery_cooldowns:
                del self.recovery_cooldowns[key]
            
            logger.info(f"Unregistered recovery action for {resource_type.value} '{resource_id}'")
            return True
        
        return False
    
    def execute_with_resilience(
        self,
        function: Callable[..., T],
        circuit_name: str = None,
        retry_name: str = None,
        error_message: str = None,
        **kwargs
    ) -> T:
        """
        Execute a function with circuit breaker and retry protections.
        
        This method combines circuit breakers and retry strategies for robust
        resilience. If both are specified, the circuit breaker wraps the retry strategy.
        
        Args:
            function: The function to execute
            circuit_name: Name of the circuit breaker to use (if any)
            retry_name: Name of the retry strategy to use (if any)
            error_message: Custom error message for logging
            **kwargs: Arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            CircuitOpenError: If the circuit is open
            Exception: Any exception raised by the function that's not handled
        """
        # Determine which protections to use
        use_circuit = circuit_name is not None and circuit_name in self.circuit_breakers
        use_retry = retry_name is not None and retry_name in self.retry_strategies
        
        # If no protections are specified, just execute the function directly
        if not use_circuit and not use_retry:
            return function(**kwargs)
        
        # Get the circuit breaker and retry strategy if needed
        circuit = self.circuit_breakers.get(circuit_name) if use_circuit else None
        retry = self.retry_strategies.get(retry_name) if use_retry else None
        
        # Configure the execution based on which protections are used
        if use_circuit and use_retry:
            # Both circuit breaker and retry strategy
            try:
                return circuit.execute(lambda: retry.execute(function, **kwargs))
            except CircuitOpenError:
                log_msg = error_message or f"Circuit '{circuit_name}' is open, cannot execute function"
                logger.error(log_msg)
                raise
            except Exception as e:
                log_msg = error_message or f"Function execution failed with circuit '{circuit_name}' and retry '{retry_name}'"
                logger.error(f"{log_msg}: {str(e)}")
                raise
                
        elif use_circuit:
            # Circuit breaker only
            try:
                return circuit.execute(lambda: function(**kwargs))
            except CircuitOpenError:
                log_msg = error_message or f"Circuit '{circuit_name}' is open, cannot execute function"
                logger.error(log_msg)
                raise
            except Exception as e:
                log_msg = error_message or f"Function execution failed with circuit '{circuit_name}'"
                logger.error(f"{log_msg}: {str(e)}")
                raise
                
        else:
            # Retry strategy only
            try:
                return retry.execute(function, **kwargs)
            except Exception as e:
                log_msg = error_message or f"Function execution failed with retry '{retry_name}'"
                logger.error(f"{log_msg}: {str(e)}")
                raise
    
    def run_health_checks(
        self,
        resource_types: Optional[List[Union[str, ResourceType]]] = None,
        resource_ids: Optional[List[str]] = None,
        force_run: bool = False
    ) -> Dict[str, Dict[str, Any]]:
        """
        Run health checks and return their statuses.
        
        Args:
            resource_types: List of resource types to check (all if None)
            resource_ids: List of resource IDs to check (all if None)
            force_run: If True, run checks regardless of their interval
            
        Returns:
            Dictionary mapping health check keys to their metrics
        """
        results = {}
        
        # Filter health checks to run based on resource_types and resource_ids
        checks_to_run = {}
        
        for key, check in self.health_checks.items():
            # Skip checks that shouldn't run yet unless forced
            if not force_run and not check.should_check():
                continue
            
            # Check if resource type matches the filter
            if resource_types is not None:
                should_include = False
                for rt in resource_types:
                    # Convert string to enum if needed
                    if isinstance(rt, str):
                        try:
                            rt = ResourceType[rt.upper()]
                        except KeyError:
                            continue
                    
                    if check.resource_type == rt:
                        should_include = True
                        break
                
                if not should_include:
                    continue
            
            # Check if resource id matches the filter
            if resource_ids is not None and check.resource_id not in resource_ids:
                continue
            
            # This check passed all filters, add it to the list
            checks_to_run[key] = check
        
        # Run the filtered health checks
        for key, check in checks_to_run.items():
            # Update the check
            check.run_check()
            
            # Store the results
            results[key] = check.get_metrics()
            
            # Attempt recovery if needed
            if check.status == HealthStatus.UNHEALTHY:
                self._attempt_recovery(check.resource_type, check.resource_id, check.status)
        
        return results
    
    def _attempt_recovery(
        self,
        resource_type: ResourceType,
        resource_id: str,
        status: HealthStatus
    ) -> bool:
        """
        Attempt to recover an unhealthy resource.
        
        Args:
            resource_type: Type of resource to recover
            resource_id: Identifier for the specific resource
            status: Current health status of the resource
            
        Returns:
            True if recovery was attempted, False otherwise
        """
        key = (resource_type, resource_id)
        
        # Check if there's a recovery action for this resource
        if key not in self.recovery_actions:
            logger.warning(f"No recovery action registered for {resource_type.value} '{resource_id}'")
            return False
        
        # Check if we're still in cooldown period
        if key in self.recovery_cooldowns:
            cooldown_until = self.recovery_cooldowns[key]
            if datetime.utcnow() < cooldown_until:
                remaining = (cooldown_until - datetime.utcnow()).total_seconds()
                logger.info(f"Recovery for {resource_type.value} '{resource_id}' in cooldown "
                           f"for {remaining:.1f} more seconds")
                return False
        
        # We can attempt recovery
        logger.info(f"Attempting recovery for {resource_type.value} '{resource_id}'")
        recovery_function = self.recovery_actions[key]
        
        try:
            success = recovery_function(resource_type, resource_id, status)
            
            # Record the attempt
            now = datetime.utcnow()
            self.recovery_attempts[key].append(now)
            
            # Set a cooldown period
            # More frequent attempts = longer cooldown (adaptive backoff)
            recent_attempts = [t for t in self.recovery_attempts[key] 
                             if (now - t).total_seconds() < 3600]  # 1 hour
            
            cooldown_seconds = min(300 * len(recent_attempts), 3600)  # 5 min to 1 hour
            self.recovery_cooldowns[key] = now + timedelta(seconds=cooldown_seconds)
            
            if success:
                logger.info(f"Recovery for {resource_type.value} '{resource_id}' was successful. "
                           f"Cooldown until: {self.recovery_cooldowns[key].isoformat()}")
            else:
                logger.warning(f"Recovery for {resource_type.value} '{resource_id}' failed. "
                             f"Cooldown until: {self.recovery_cooldowns[key].isoformat()}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during recovery attempt for {resource_type.value} '{resource_id}': {str(e)}")
            
            # Still set a cooldown to prevent hammering with failed recovery attempts
            self.recovery_cooldowns[key] = datetime.utcnow() + timedelta(seconds=300)
            return False
    
    def get_health_status(
        self,
        resource_types: Optional[List[Union[str, ResourceType]]] = None,
        resource_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get the current health status for all monitored resources.
        
        Args:
            resource_types: List of resource types to include (all if None)
            resource_ids: List of resource IDs to include (all if None)
            
        Returns:
            Dictionary with health status information
        """
        # Get health check metrics for the specified filters
        health_checks = {}
        circuit_breakers = {}
        
        # Filter health checks
        for key, check in self.health_checks.items():
            # Determine resource type and ID from the key
            parts = key.split(":", 1)
            rt_str = parts[0]
            rid = parts[1] if len(parts) > 1 else None
            
            # Skip if doesn't match resource_types filter
            if resource_types is not None:
                should_include = False
                for rt in resource_types:
                    if isinstance(rt, str) and rt.lower() == rt_str.lower():
                        should_include = True
                        break
                    elif isinstance(rt, ResourceType) and rt.value.lower() == rt_str.lower():
                        should_include = True
                        break
                
                if not should_include:
                    continue
            
            # Skip if doesn't match resource_ids filter
            if resource_ids is not None and rid not in resource_ids:
                continue
            
            # This check passed all filters, add it to the results
            health_checks[key] = check.get_metrics()
        
        # Filter circuit breakers (by name)
        for name, cb in self.circuit_breakers.items():
            # For simplicity, we'll just include all circuit breakers
            # unless resource_ids filter specifies circuit breaker names
            if resource_ids is not None and name not in resource_ids:
                continue
            
            circuit_breakers[name] = cb.get_status()
        
        # Calculate overall health
        overall_status = HealthStatus.HEALTHY
        unhealthy_count = 0
        degraded_count = 0
        
        for metrics in health_checks.values():
            status = metrics["status"]
            if status == HealthStatus.UNHEALTHY.value:
                unhealthy_count += 1
                overall_status = HealthStatus.UNHEALTHY
            elif status == HealthStatus.DEGRADED.value and overall_status != HealthStatus.UNHEALTHY:
                degraded_count += 1
                overall_status = HealthStatus.DEGRADED
        
        # If any circuit is open, system is at least degraded
        open_circuits = 0
        for metrics in circuit_breakers.values():
            if metrics["state"] == "open":
                open_circuits += 1
                if overall_status != HealthStatus.UNHEALTHY:
                    overall_status = HealthStatus.DEGRADED
        
        # Build the response
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_health_checks": len(health_checks),
                "unhealthy_checks": unhealthy_count,
                "degraded_checks": degraded_count,
                "total_circuits": len(circuit_breakers),
                "open_circuits": open_circuits
            },
            "health_checks": health_checks,
            "circuit_breakers": circuit_breakers
        }
    
    def reset(self) -> None:
        """Reset all circuit breakers, retry strategies, and health checks."""
        # Reset circuit breakers
        for cb in self.circuit_breakers.values():
            cb.reset()
        
        # Reset retry strategies
        for rs in self.retry_strategies.values():
            rs.reset_metrics()
        
        # Reset health checks
        for hc in self.health_checks.values():
            hc.reset()
        
        # Clear recovery tracking
        self.recovery_attempts = {k: [] for k in self.recovery_attempts}
        self.recovery_cooldowns = {}
        
        logger.info("Reset all self-healing components")