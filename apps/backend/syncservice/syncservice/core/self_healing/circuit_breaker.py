"""
Circuit Breaker implementation for the SyncService.

This module provides a circuit breaker pattern implementation that prevents
repeated failures when interacting with external systems by temporarily
disabling operations that are failing consistently.
"""

import time
import logging
from enum import Enum, auto
from typing import Callable, Any, Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Enumeration of possible circuit breaker states."""
    CLOSED = auto()  # Normal operation, requests pass through
    OPEN = auto()    # Circuit is open, requests fail fast
    HALF_OPEN = auto()  # Testing if system has recovered


class CircuitBreaker:
    """
    Circuit breaker implementation for protecting against cascading failures.
    
    The circuit breaker monitors failures in operations and temporarily
    disables them if they are consistently failing, allowing the system
    to recover without further stress.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        half_open_max_calls: int = 1,
        reset_timeout: int = 300
    ):
        """
        Initialize a new circuit breaker.
        
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of consecutive failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery (half-open)
            half_open_max_calls: Number of test calls allowed in half-open state
            reset_timeout: Maximum seconds to keep circuit open before forced reset
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.reset_timeout = reset_timeout
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.opened_time = None
        self.half_open_calls = 0
        self.success_count = 0
        self.failure_history = []
        
        logger.info(f"Circuit breaker '{name}' initialized with threshold {failure_threshold}")
    
    def record_failure(self, exception: Exception) -> None:
        """
        Record a failure in the protected operation.
        
        Args:
            exception: The exception that caused the failure
        """
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        self.failure_history.append({
            'time': self.last_failure_time,
            'exception': str(exception),
            'type': type(exception).__name__
        })
        
        # Trim history to most recent 100 failures
        if len(self.failure_history) > 100:
            self.failure_history = self.failure_history[-100:]
        
        # Check if we should open the circuit
        if self.state == CircuitState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker '{self.name}' tripped open after {self.failure_count} "
                f"consecutive failures. Last error: {str(exception)}"
            )
            self.state = CircuitState.OPEN
            self.opened_time = datetime.now()
    
    def record_success(self) -> None:
        """Record a successful operation."""
        self.success_count += 1
        
        # If we're half-open and have a success, close the circuit
        if self.state == CircuitState.HALF_OPEN:
            logger.info(f"Circuit breaker '{self.name}' closing after successful test call")
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.half_open_calls = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count after successful closed operation
            self.failure_count = 0
    
    def check_state(self) -> None:
        """
        Check and update the circuit breaker state based on timing.
        
        This should be called before attempting an operation to ensure
        the circuit is in the correct state.
        """
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has elapsed
            if self.opened_time and datetime.now() - self.opened_time > timedelta(seconds=self.recovery_timeout):
                logger.info(f"Circuit breaker '{self.name}' switching to half-open state for testing")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            
            # Force reset if circuit has been open too long
            elif self.opened_time and datetime.now() - self.opened_time > timedelta(seconds=self.reset_timeout):
                logger.warning(f"Circuit breaker '{self.name}' forced reset after {self.reset_timeout} seconds")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.half_open_calls = 0
    
    def is_allowed(self) -> bool:
        """
        Check if an operation is allowed to proceed.
        
        Returns:
            True if the operation can proceed, False if it should fail fast
        """
        self.check_state()
        
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            return False
        elif self.state == CircuitState.HALF_OPEN:
            # Allow a limited number of test calls in half-open state
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        return False  # Fallback
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function if successful
            
        Raises:
            Exception: If the circuit is open or the function fails
        """
        if not self.is_allowed():
            raise RuntimeError(f"Circuit breaker '{self.name}' is open, failing fast")
        
        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the circuit breaker.
        
        Returns:
            Dictionary with current status information
        """
        return {
            'name': self.name,
            'state': self.state.name,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'failure_threshold': self.failure_threshold,
            'recovery_timeout': self.recovery_timeout,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'opened_time': self.opened_time.isoformat() if self.opened_time else None,
            'half_open_calls': self.half_open_calls,
            'recent_failures': len(self.failure_history),
            'uptime_percentage': self._calculate_uptime_percentage()
        }
    
    def _calculate_uptime_percentage(self) -> float:
        """
        Calculate approximate uptime percentage based on success vs. failure.
        
        Returns:
            Float from 0-100 representing uptime percentage
        """
        total_operations = self.success_count + sum(1 for f in self.failure_history if f['time'] is not None)
        if total_operations == 0:
            return 100.0  # No operations means no failures
            
        return (self.success_count / total_operations) * 100
    
    def reset(self) -> None:
        """
        Reset the circuit breaker to its initial closed state.
        
        This can be used for manual intervention when necessary.
        """
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_calls = 0
        self.opened_time = None