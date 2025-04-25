"""
Circuit Breaker pattern implementation for TerraFusion SyncService platform.

This module provides a robust circuit breaker implementation to prevent
cascading failures, provide fast failure detection, and automatic recovery.
"""

import logging
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar('T')
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Possible states for the circuit breaker."""
    CLOSED = "closed"  # Normal operation, requests are allowed
    OPEN = "open"      # Circuit is open, requests are not allowed
    HALF_OPEN = "half_open"  # Testing if service is healthy again


class CircuitBreaker:
    """
    Circuit Breaker implementation to prevent cascading failures.
    
    This implementation follows the circuit breaker pattern:
    - In CLOSED state, all operations execute normally.
    - When failures exceed threshold, circuit opens (OPEN state).
    - After reset_timeout, allows one test request (HALF_OPEN state).
    - If test succeeds, circuit closes; if it fails, reset timeout restarts.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        reset_timeout: int = 30,
        half_open_success_threshold: int = 1,
        monitored_exceptions: List[type] = None,
        on_open_callback: Optional[Callable[[str], None]] = None,
        on_close_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            name: Name of the circuit breaker for identification
            failure_threshold: Number of failures before opening circuit
            reset_timeout: Seconds to wait before attempting to close circuit
            half_open_success_threshold: Number of successes in half-open state
                required to close the circuit
            monitored_exceptions: List of exception types to monitor; any other
                exceptions will be treated as unmonitored and always propagated
            on_open_callback: Callback to execute when circuit transitions to open
            on_close_callback: Callback to execute when circuit transitions to closed
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_success_threshold = half_open_success_threshold
        self.monitored_exceptions = monitored_exceptions or [Exception]
        self.on_open_callback = on_open_callback
        self.on_close_callback = on_close_callback
        
        # Initialize state
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.successful_half_open_calls = 0
        
        # Tracking metrics
        self.total_successful_calls = 0
        self.total_failed_calls = 0
        self.consecutive_successful_calls = 0
        self.last_state_change_time = datetime.utcnow()
        
        logger.info(f"Circuit breaker '{name}' initialized in {self.state.value} state")
    
    def execute(self, function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with circuit breaker protection.
        
        Args:
            function: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            Exception: Any exception raised by the function that's not handled
            CircuitOpenError: If the circuit is open
        """
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            # Check if enough time has passed to try half-open state
            if self._should_attempt_reset():
                logger.info(f"Circuit breaker '{self.name}' trying half-open state")
                self._transition_to_half_open()
            else:
                # Still open with no reset attempt
                reset_at = self.last_failure_time + timedelta(seconds=self.reset_timeout)
                raise CircuitOpenError(
                    f"Circuit '{self.name}' is open. Retry after {reset_at.isoformat()}",
                    self.name,
                    reset_at
                )
        
        # Execute function - both in CLOSED and HALF_OPEN states
        try:
            result = function(*args, **kwargs)
            self._handle_success()
            return result
        except Exception as e:
            # Handle failure based on exception type
            if any(isinstance(e, exc_type) for exc_type in self.monitored_exceptions):
                self._handle_failure(e)
            
            # Always re-raise the exception
            raise
    
    def _handle_success(self) -> None:
        """Handle a successful execution."""
        self.total_successful_calls += 1
        self.consecutive_successful_calls += 1
        
        if self.state == CircuitState.HALF_OPEN:
            self.successful_half_open_calls += 1
            logger.info(f"Circuit '{self.name}' successful half-open call: "
                       f"{self.successful_half_open_calls}/{self.half_open_success_threshold}")
            
            # If we've reached the required successes in half-open state, close the circuit
            if self.successful_half_open_calls >= self.half_open_success_threshold:
                self._transition_to_closed()
    
    def _handle_failure(self, exception: Exception) -> None:
        """
        Handle a failed execution.
        
        Args:
            exception: The exception that caused the failure
        """
        self.total_failed_calls += 1
        self.consecutive_successful_calls = 0
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitState.CLOSED:
            self.failure_count += 1
            logger.warning(f"Circuit '{self.name}' failure: {self.failure_count}/{self.failure_threshold}")
            
            # If we've reached the failure threshold, open the circuit
            if self.failure_count >= self.failure_threshold:
                self._transition_to_open()
        
        elif self.state == CircuitState.HALF_OPEN:
            # Any failure in half-open state opens the circuit again
            logger.warning(f"Circuit '{self.name}' failure in half-open state. Reopening circuit.")
            self._transition_to_open()
    
    def _transition_to_open(self) -> None:
        """Transition the circuit to the open state."""
        self.state = CircuitState.OPEN
        self.last_state_change_time = datetime.utcnow()
        self.last_failure_time = datetime.utcnow()
        
        logger.warning(f"Circuit '{self.name}' opened due to consecutive failures")
        
        # Execute the on_open callback if provided
        if self.on_open_callback:
            try:
                self.on_open_callback(self.name)
            except Exception as e:
                logger.error(f"Error in circuit breaker '{self.name}' on_open_callback: {str(e)}")
    
    def _transition_to_half_open(self) -> None:
        """Transition the circuit to the half-open state."""
        self.state = CircuitState.HALF_OPEN
        self.last_state_change_time = datetime.utcnow()
        self.successful_half_open_calls = 0
        
        logger.info(f"Circuit '{self.name}' transitioned to half-open state")
    
    def _transition_to_closed(self) -> None:
        """Transition the circuit to the closed state."""
        self.state = CircuitState.CLOSED
        self.last_state_change_time = datetime.utcnow()
        self.failure_count = 0
        
        logger.info(f"Circuit '{self.name}' closed after successful half-open calls")
        
        # Execute the on_close callback if provided
        if self.on_close_callback:
            try:
                self.on_close_callback(self.name)
            except Exception as e:
                logger.error(f"Error in circuit breaker '{self.name}' on_close_callback: {str(e)}")
    
    def _should_attempt_reset(self) -> bool:
        """
        Check if enough time has passed to attempt a reset.
        
        Returns:
            True if enough time has passed, False otherwise
        """
        if not self.last_failure_time:
            return True
        
        elapsed_time = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed_time >= self.reset_timeout
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the circuit breaker.
        
        Returns:
            Dictionary with circuit breaker status
        """
        now = datetime.utcnow()
        time_in_current_state = (now - self.last_state_change_time).total_seconds()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "reset_timeout": self.reset_timeout,
            "time_in_current_state_seconds": time_in_current_state,
            "total_successful_calls": self.total_successful_calls,
            "total_failed_calls": self.total_failed_calls,
            "consecutive_successful_calls": self.consecutive_successful_calls,
            "last_state_change": self.last_state_change_time.isoformat() if self.last_state_change_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }
    
    def force_open(self) -> None:
        """Force the circuit to open for testing or management purposes."""
        if self.state != CircuitState.OPEN:
            logger.warning(f"Circuit '{self.name}' manually forced open")
            self._transition_to_open()
    
    def force_close(self) -> None:
        """Force the circuit to close for testing or management purposes."""
        if self.state != CircuitState.CLOSED:
            logger.warning(f"Circuit '{self.name}' manually forced closed")
            self._transition_to_closed()
    
    def reset(self) -> None:
        """Reset the circuit breaker to its initial state."""
        logger.info(f"Circuit '{self.name}' manually reset")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.successful_half_open_calls = 0
        self.last_state_change_time = datetime.utcnow()


class CircuitOpenError(Exception):
    """Exception raised when a circuit is open."""
    
    def __init__(self, message: str, circuit_name: str, reset_at: datetime):
        """
        Initialize CircuitOpenError.
        
        Args:
            message: Error message
            circuit_name: Name of the circuit that is open
            reset_at: Datetime when the circuit will attempt to reset
        """
        super().__init__(message)
        self.circuit_name = circuit_name
        self.reset_at = reset_at