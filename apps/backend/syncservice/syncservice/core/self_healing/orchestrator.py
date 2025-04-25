"""
Self-healing orchestrator for the SyncService.

This module provides the main orchestrator that coordinates self-healing
mechanisms, including circuit breakers, retry strategies, and health monitoring.
It serves as the central point for implementing resilience patterns.
"""

import os
import time
import logging
import threading
from enum import Enum, auto
from typing import Dict, Any, Callable, Optional, List, Type, Set, Union
from datetime import datetime, timedelta

from .circuit_breaker import CircuitBreaker
from .retry_strategy import RetryStrategy

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Enumeration of possible health status values."""
    HEALTHY = auto()
    DEGRADED = auto()
    UNHEALTHY = auto()


class SelfHealingOrchestrator:
    """
    Main orchestrator for self-healing capabilities in the SyncService.
    
    This class combines circuit breakers, retry strategies, and health monitoring
    to provide comprehensive resilience for the SyncService's interactions with
    external systems.
    """
    
    def __init__(self, service_name: str = "SyncService"):
        """
        Initialize the self-healing orchestrator.
        
        Args:
            service_name: Name of the service this orchestrator is protecting
        """
        self.service_name = service_name
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}
        self.health_checks: Dict[str, Callable[[], bool]] = {}
        self.last_health_check = None
        self.health_status = HealthStatus.HEALTHY
        self.health_history = []
        self.recovery_actions = []
        
        # Default recovery settings
        self.recovery_threshold = int(os.environ.get("RECOVERY_THRESHOLD", "3"))
        self.recovery_window = int(os.environ.get("RECOVERY_WINDOW", "1800"))  # 30 minutes
        self.max_auto_recoveries = int(os.environ.get("MAX_AUTO_RECOVERIES", "5"))
        
        # Internal state
        self._recoveries_in_window = 0
        self._last_recovery_time = None
        
        logger.info(f"SelfHealingOrchestrator initialized for {service_name}")
        
        # Start background health check thread
        self._start_health_check_thread()
    
    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1,
        reset_timeout: int = 300
    ) -> CircuitBreaker:
        """
        Register a new circuit breaker for a specific component.
        
        Args:
            name: Identifier for the circuit breaker
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            half_open_max_calls: Number of test calls allowed in half-open state
            reset_timeout: Maximum seconds to keep circuit open before forced reset
            
        Returns:
            The created CircuitBreaker instance
        """
        if name in self.circuit_breakers:
            logger.warning(f"Circuit breaker '{name}' already exists, returning existing instance")
            return self.circuit_breakers[name]
        
        cb = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
            reset_timeout=reset_timeout
        )
        
        self.circuit_breakers[name] = cb
        logger.info(f"Registered circuit breaker '{name}'")
        return cb
    
    def register_retry_strategy(
        self,
        name: str,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: Optional[Set[Type[Exception]]] = None
    ) -> RetryStrategy:
        """
        Register a new retry strategy for a specific component.
        
        Args:
            name: Identifier for the retry strategy
            max_attempts: Maximum number of attempts including the initial one
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add randomized jitter to delays
            retry_on_exceptions: Set of exception types to retry on
            
        Returns:
            The created RetryStrategy instance
        """
        if name in self.retry_strategies:
            logger.warning(f"Retry strategy '{name}' already exists, returning existing instance")
            return self.retry_strategies[name]
        
        rs = RetryStrategy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            jitter=jitter,
            retry_on_exceptions=retry_on_exceptions
        )
        
        self.retry_strategies[name] = rs
        logger.info(f"Registered retry strategy '{name}'")
        return rs
    
    def register_health_check(self, name: str, check_func: Callable[[], bool]) -> None:
        """
        Register a health check function.
        
        Args:
            name: Identifier for the health check
            check_func: Function that returns True if healthy, False otherwise
        """
        self.health_checks[name] = check_func
        logger.info(f"Registered health check '{name}'")
    
    def execute_with_resilience(
        self,
        func: Callable,
        circuit_name: str,
        retry_name: str,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with both circuit breaker and retry protection.
        
        This method combines circuit breaker and retry strategy to provide
        comprehensive resilience for external system interactions.
        
        Args:
            func: The function to execute
            circuit_name: Name of the circuit breaker to use
            retry_name: Name of the retry strategy to use
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function if successful
            
        Raises:
            Exception: If the operation fails after all retry attempts or
                       if the circuit breaker is open
        """
        # Get or create circuit breaker and retry strategy
        circuit_breaker = self.get_or_create_circuit_breaker(circuit_name)
        retry_strategy = self.get_or_create_retry_strategy(retry_name)
        
        # Execute with both protections
        try:
            # Use circuit breaker to wrap the retry strategy
            return circuit_breaker.execute(
                lambda: retry_strategy.execute(func, *args, **kwargs)
            )
        except Exception as e:
            logger.error(f"Operation failed with resilience protection: {str(e)}")
            # Record the failure for health assessment
            self._record_failure(circuit_name, str(e))
            raise
    
    def get_or_create_circuit_breaker(self, name: str) -> CircuitBreaker:
        """
        Get an existing circuit breaker or create a new one if it doesn't exist.
        
        Args:
            name: Name of the circuit breaker
            
        Returns:
            CircuitBreaker instance
        """
        if name not in self.circuit_breakers:
            logger.info(f"Auto-creating circuit breaker '{name}'")
            return self.register_circuit_breaker(name)
        return self.circuit_breakers[name]
    
    def get_or_create_retry_strategy(self, name: str) -> RetryStrategy:
        """
        Get an existing retry strategy or create a new one if it doesn't exist.
        
        Args:
            name: Name of the retry strategy
            
        Returns:
            RetryStrategy instance
        """
        if name not in self.retry_strategies:
            logger.info(f"Auto-creating retry strategy '{name}'")
            return self.register_retry_strategy(name)
        return self.retry_strategies[name]
    
    def check_health(self) -> Dict[str, Any]:
        """
        Check the health of all registered components.
        
        Returns:
            Dictionary with health status information
        """
        results = {}
        all_checks_passed = True
        any_checks_failed = False
        check_time = datetime.now()
        
        # Execute all registered health checks
        for name, check_func in self.health_checks.items():
            try:
                passed = check_func()
                results[name] = passed
                if not passed:
                    all_checks_passed = False
                    any_checks_failed = True
            except Exception as e:
                logger.error(f"Health check '{name}' failed with exception: {str(e)}")
                results[name] = False
                all_checks_passed = False
                any_checks_failed = True
        
        # Check circuit breakers
        circuit_status = {}
        for name, cb in self.circuit_breakers.items():
            cb_status = cb.get_status()
            circuit_status[name] = cb_status
            if cb_status['state'] != 'CLOSED':
                all_checks_passed = False
        
        # Determine overall health status
        if all_checks_passed:
            status = HealthStatus.HEALTHY
        elif any_checks_failed:
            status = HealthStatus.UNHEALTHY
        else:
            status = HealthStatus.DEGRADED
        
        # Update internal state
        self.health_status = status
        self.last_health_check = check_time
        
        # Record health check in history
        health_record = {
            'timestamp': check_time,
            'status': status.name,
            'check_results': results,
            'circuit_status': circuit_status
        }
        self.health_history.append(health_record)
        
        # Trim history to most recent 100 checks
        if len(self.health_history) > 100:
            self.health_history = self.health_history[-100:]
        
        return health_record
    
    def attempt_recovery(self, component_name: Optional[str] = None) -> bool:
        """
        Attempt to recover a degraded or unhealthy component.
        
        Args:
            component_name: Name of the component to recover, or None for all
            
        Returns:
            True if recovery was attempted, False otherwise
        """
        # Check if we've exceeded the maximum auto-recoveries in the window
        current_time = datetime.now()
        if self._last_recovery_time:
            # Reset counter if we're outside the window
            if current_time - self._last_recovery_time > timedelta(seconds=self.recovery_window):
                self._recoveries_in_window = 0
            # Check if we've exceeded the limit
            elif self._recoveries_in_window >= self.max_auto_recoveries:
                logger.warning(
                    f"Maximum auto-recoveries ({self.max_auto_recoveries}) "
                    f"reached in {self.recovery_window}s window, skipping recovery"
                )
                return False
        
        # Update recovery counters
        self._recoveries_in_window += 1
        self._last_recovery_time = current_time
        
        recovery_actions = []
        
        # Reset circuit breakers
        if component_name:
            if component_name in self.circuit_breakers:
                cb = self.circuit_breakers[component_name]
                logger.info(f"Attempting recovery of circuit breaker '{component_name}'")
                cb.reset()
                recovery_actions.append(f"Reset circuit breaker '{component_name}'")
        else:
            # Reset all circuit breakers if no specific component
            for name, cb in self.circuit_breakers.items():
                logger.info(f"Attempting recovery of circuit breaker '{name}'")
                cb.reset()
                recovery_actions.append(f"Reset circuit breaker '{name}'")
        
        # Record recovery attempt
        recovery_record = {
            'timestamp': current_time,
            'component': component_name or 'all',
            'actions': recovery_actions,
            'recovery_count': self._recoveries_in_window
        }
        self.recovery_actions.append(recovery_record)
        
        # Trim history to most recent 100 recoveries
        if len(self.recovery_actions) > 100:
            self.recovery_actions = self.recovery_actions[-100:]
        
        return True
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of the service.
        
        Returns:
            Dictionary with health status information
        """
        # Perform a health check if we haven't done one yet or it's been too long
        if not self.last_health_check or \
           datetime.now() - self.last_health_check > timedelta(minutes=1):
            self.check_health()
        
        return {
            'service_name': self.service_name,
            'status': self.health_status.name,
            'last_check': self.last_health_check.isoformat() if self.last_health_check else None,
            'circuit_breakers': {name: cb.get_status() for name, cb in self.circuit_breakers.items()},
            'recovery_attempts': len(self.recovery_actions),
            'recovery_window_remaining': self._get_recovery_window_remaining(),
            'recoveries_available': max(0, self.max_auto_recoveries - self._recoveries_in_window)
        }
    
    def _get_recovery_window_remaining(self) -> int:
        """
        Get the number of seconds remaining in the current recovery window.
        
        Returns:
            Seconds remaining in the recovery window, or 0 if no window is active
        """
        if not self._last_recovery_time:
            return 0
        
        window_end = self._last_recovery_time + timedelta(seconds=self.recovery_window)
        now = datetime.now()
        
        if now >= window_end:
            return 0
        
        return int((window_end - now).total_seconds())
    
    def _record_failure(self, component_name: str, error_message: str) -> None:
        """
        Record a component failure for health assessment.
        
        Args:
            component_name: Name of the component that failed
            error_message: Error message from the failure
        """
        failure_record = {
            'timestamp': datetime.now(),
            'component': component_name,
            'error': error_message
        }
        
        # This could be expanded to store failures in a database or other persistent storage
        logger.warning(f"Component '{component_name}' failed: {error_message}")
    
    def _start_health_check_thread(self) -> None:
        """Start a background thread for periodic health checks."""
        def health_check_worker():
            while True:
                try:
                    # Run health check every 60 seconds
                    self.check_health()
                    
                    # Auto-recover if unhealthy
                    if self.health_status == HealthStatus.UNHEALTHY:
                        logger.warning("Service is unhealthy, attempting auto-recovery")
                        self.attempt_recovery()
                        
                except Exception as e:
                    logger.error(f"Error in health check thread: {str(e)}")
                
                # Sleep for 60 seconds
                time.sleep(60)
        
        # Start thread
        thread = threading.Thread(target=health_check_worker, daemon=True)
        thread.start()
        logger.info("Started background health check thread")