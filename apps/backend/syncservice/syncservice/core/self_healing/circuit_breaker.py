"""
Circuit Breaker implementation for the TerraFusion SyncService platform.

This module provides a circuit breaker pattern implementation to prevent
cascading failures and allow the system to fail fast when external
dependencies are unavailable.
"""

import time
import logging
from enum import Enum
from typing import Callable, Any, Optional, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Enum for the possible states of a circuit breaker."""
    CLOSED = "closed"  # Circuit is closed, operations are allowed
    OPEN = "open"      # Circuit is open, operations are blocked
    HALF_OPEN = "half_open"  # Circuit is half-open, testing if operations can be allowed again


class CircuitBreaker:
    """
    Implementation of the Circuit Breaker pattern.
    
    The circuit breaker monitors operations and trips open if failures exceed a threshold,
    preventing further operations until a cooling period has passed.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout_seconds: int = 60,
        half_open_max_calls: int = 1,
        excluded_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize a new circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of consecutive failures before opening the circuit
            reset_timeout_seconds: Seconds to wait before attempting to close the circuit again
            half_open_max_calls: Maximum number of calls to allow in half-open state
            excluded_exceptions: Exceptions that should not count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout_seconds = reset_timeout_seconds
        self.half_open_max_calls = half_open_max_calls
        self.excluded_exceptions = excluded_exceptions or []
        
        # Internal state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._successful_half_open_calls = 0
        self._half_open_calls_remaining = half_open_max_calls
        
        logger.info(f"Circuit breaker '{name}' initialized")
    
    @property
    def state(self) -> CircuitState:
        """Get the current state of the circuit breaker."""
        # Check if we need to transition from OPEN to HALF_OPEN
        if self._state == CircuitState.OPEN and self._last_failure_time:
            cooling_period_end = self._last_failure_time + timedelta(seconds=self.reset_timeout_seconds)
            if datetime.utcnow() >= cooling_period_end:
                self._transition_to_half_open()
        
        return self._state
    
    def _transition_to_open(self):
        """Transition the circuit breaker to the open state."""
        if self._state != CircuitState.OPEN:
            previous_state = self._state
            self._state = CircuitState.OPEN
            self._last_failure_time = datetime.utcnow()
            logger.warning(f"Circuit breaker '{self.name}' transitioned from {previous_state.value} to OPEN")
    
    def _transition_to_half_open(self):
        """Transition the circuit breaker to the half-open state."""
        if self._state != CircuitState.HALF_OPEN:
            previous_state = self._state
            self._state = CircuitState.HALF_OPEN
            self._half_open_calls_remaining = self.half_open_max_calls
            self._successful_half_open_calls = 0
            logger.info(f"Circuit breaker '{self.name}' transitioned from {previous_state.value} to HALF_OPEN")
    
    def _transition_to_closed(self):
        """Transition the circuit breaker to the closed state."""
        if self._state != CircuitState.CLOSED:
            previous_state = self._state
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' transitioned from {previous_state.value} to CLOSED")
    
    def record_success(self):
        """Record a successful operation."""
        if self._state == CircuitState.CLOSED:
            # Reset the failure count
            self._failure_count = 0
            
        elif self._state == CircuitState.HALF_OPEN:
            # Record successful call in half-open state
            self._successful_half_open_calls += 1
            
            # If we've had enough successful calls, close the circuit
            if self._successful_half_open_calls >= self.half_open_max_calls:
                self._transition_to_closed()
                logger.info(f"Circuit breaker '{self.name}' closed after {self._successful_half_open_calls} successful calls")
    
    def record_failure(self, exception: Optional[Exception] = None):
        """
        Record a failed operation.
        
        Args:
            exception: The exception that caused the failure, if any
        """
        # If the exception is in the excluded list, don't count it as a failure
        if exception and any(isinstance(exception, exc_type) for exc_type in self.excluded_exceptions):
            logger.debug(f"Circuit breaker '{self.name}' ignoring excluded exception: {type(exception).__name__}")
            return
        
        if self._state == CircuitState.CLOSED:
            # Increment the failure count
            self._failure_count += 1
            
            # If we've reached the threshold, open the circuit
            if self._failure_count >= self.failure_threshold:
                self._transition_to_open()
                logger.warning(f"Circuit breaker '{self.name}' opened after {self._failure_count} consecutive failures")
                
        elif self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit again
            self._transition_to_open()
            logger.warning(f"Circuit breaker '{self.name}' reopened after failure in half-open state")
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            CircuitBreakerOpenError: If the circuit is open
            Any exception raised by the function
        """
        current_state = self.state
        
        # If the circuit is open, don't allow the call
        if current_state == CircuitState.OPEN:
            remaining_seconds = self._get_remaining_open_seconds()
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is open. Will retry in {remaining_seconds} seconds."
            )
        
        # If the circuit is half-open, only allow a limited number of calls
        if current_state == CircuitState.HALF_OPEN:
            if self._half_open_calls_remaining <= 0:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is half-open but no more test calls are permitted at this time."
                )
            self._half_open_calls_remaining -= 1
        
        # Execute the function and record success or failure
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise
    
    def _get_remaining_open_seconds(self) -> int:
        """Get the number of seconds remaining before the circuit can be half-open."""
        if not self._last_failure_time:
            return self.reset_timeout_seconds
        
        cooling_period_end = self._last_failure_time + timedelta(seconds=self.reset_timeout_seconds)
        remaining = (cooling_period_end - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the circuit breaker.
        
        Returns:
            Dictionary with circuit breaker metrics
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout_seconds": self.reset_timeout_seconds,
            "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
            "remaining_open_seconds": self._get_remaining_open_seconds() if self._state == CircuitState.OPEN else 0,
            "half_open_calls_remaining": self._half_open_calls_remaining if self._state == CircuitState.HALF_OPEN else None,
            "successful_half_open_calls": self._successful_half_open_calls if self._state == CircuitState.HALF_OPEN else None
        }
    
    def reset(self):
        """Reset the circuit breaker to its initial closed state."""
        previous_state = self._state
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = None
        self._successful_half_open_calls = 0
        self._half_open_calls_remaining = self.half_open_max_calls
        logger.info(f"Circuit breaker '{self.name}' manually reset from {previous_state.value} to CLOSED")


class CircuitBreakerOpenError(Exception):
    """Exception raised when attempting to execute a function with an open circuit breaker."""
    pass