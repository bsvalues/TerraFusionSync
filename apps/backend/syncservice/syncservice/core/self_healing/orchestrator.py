"""
Self-Healing Orchestrator for Sync Operations.

This module implements robust retry and recovery strategies for sync operations,
allowing the system to automatically handle transient failures and recover from
various error conditions without manual intervention.
"""

import time
import logging
import traceback
from typing import Dict, Any, List, Optional, Callable, Tuple, TypeVar, Generic, Union
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

# Type definitions for better type hinting
T = TypeVar('T')
ErrorHandler = Callable[[Exception], None]
RetryCallback = Callable[[int], None]
CircuitBreakerCallback = Callable[[], None]
Operation = Callable[[], T]


class RetryStrategy:
    """
    Configurable retry strategy for handling transient failures.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        max_delay: float = 30.0,
        jitter: float = 0.1,
        retry_exceptions: tuple = (Exception,),
        timeout: Optional[float] = None
    ):
        """
        Initialize the retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds between retries
            backoff_factor: Multiplier for the delay after each retry
            max_delay: Maximum delay in seconds
            jitter: Random factor to add to delay to prevent thundering herd
            retry_exceptions: Tuple of exception types to retry on
            timeout: Maximum time in seconds to keep retrying
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        self.jitter = jitter
        self.retry_exceptions = retry_exceptions
        self.timeout = timeout
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            exception: The exception that was raised
            attempt: The current attempt number
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Check if we've exceeded the maximum number of attempts
        if attempt >= self.max_attempts:
            return False
        
        # Check if the exception is one we should retry on
        for retry_exception in self.retry_exceptions:
            if isinstance(exception, retry_exception):
                return True
        
        return False
    
    def get_delay(self, attempt: int) -> float:
        """
        Calculate the delay for the current retry attempt.
        
        Args:
            attempt: The current attempt number
            
        Returns:
            Delay in seconds before the next retry
        """
        import random
        
        # Calculate exponential backoff
        delay = min(
            self.initial_delay * (self.backoff_factor ** (attempt - 1)),
            self.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.jitter > 0:
            delay += random.uniform(0, self.jitter * delay)
        
        return delay


class CircuitBreakerState(Enum):
    """
    States for the circuit breaker pattern.
    """
    CLOSED = "closed"  # Normal operation, requests pass through
    OPEN = "open"  # Failure threshold exceeded, requests are rejected
    HALF_OPEN = "half_open"  # Trying a single request to see if system has recovered


class CircuitBreaker:
    """
    Implementation of the circuit breaker pattern to prevent cascading failures.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        monitored_exceptions: tuple = (Exception,)
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening the circuit
            recovery_timeout: Time in seconds before attempting recovery after opening
            monitored_exceptions: Tuple of exception types to count as failures
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.monitored_exceptions = monitored_exceptions
        
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
    
    def record_failure(self) -> None:
        """
        Record a failure and potentially open the circuit.
        """
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.state == CircuitBreakerState.CLOSED and self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker opened after {self.failure_count} consecutive failures")
            self.state = CircuitBreakerState.OPEN
    
    def record_success(self) -> None:
        """
        Record a success and potentially close the circuit.
        """
        self.failure_count = 0
        
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker closed after successful recovery")
            self.state = CircuitBreakerState.CLOSED
    
    def allow_request(self) -> bool:
        """
        Check if a request should be allowed to proceed.
        
        Returns:
            True if the request should proceed, False otherwise
        """
        # If the circuit is closed, allow the request
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        # If the circuit is open, check if it's time to try a recovery
        if self.state == CircuitBreakerState.OPEN:
            recovery_time = self.last_failure_time + timedelta(seconds=self.recovery_timeout)
            
            if datetime.utcnow() >= recovery_time:
                logger.info("Circuit breaker transitioning to half-open state for recovery attempt")
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            
            return False
        
        # If the circuit is half-open, allow only one request to test the service
        if self.state == CircuitBreakerState.HALF_OPEN:
            return True
        
        return False


class SelfHealingOrchestrator(Generic[T]):
    """
    Orchestrator for self-healing operations with circuit breaking and retry capabilities.
    
    This class provides comprehensive error handling for critical operations,
    applying best practices from resilience engineering:
    
    1. Retry with exponential backoff for transient failures
    2. Circuit breaking to prevent cascading failures
    3. Fallback mechanisms for graceful degradation
    4. Comprehensive error tracking and reporting
    
    Usage example:
    ```
    orchestrator = SelfHealingOrchestrator(
        retry_strategy=RetryStrategy(max_attempts=3, backoff_factor=2.0),
        circuit_breaker=CircuitBreaker(failure_threshold=5, recovery_timeout=60.0)
    )
    
    def my_operation():
        # Business logic here
        return result
    
    def on_retry(attempt):
        logger.info(f"Retrying operation, attempt {attempt}")
    
    def on_circuit_break():
        logger.warning("Circuit broken, operation not executed")
    
    result = orchestrator.execute(
        operation=my_operation,
        retry_callback=on_retry,
        circuit_breaker_callback=on_circuit_break
    )
    ```
    """
    
    def __init__(
        self,
        retry_strategy: Optional[RetryStrategy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize the self-healing orchestrator.
        
        Args:
            retry_strategy: Strategy for retrying failed operations
            circuit_breaker: Circuit breaker to prevent cascading failures
        """
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
    
    def execute(
        self,
        operation: Operation[T],
        error_handler: Optional[ErrorHandler] = None,
        retry_callback: Optional[RetryCallback] = None,
        circuit_breaker_callback: Optional[CircuitBreakerCallback] = None,
        fallback_value: Optional[T] = None
    ) -> Union[T, None]:
        """
        Execute an operation with self-healing capabilities.
        
        Args:
            operation: The function to execute
            error_handler: Callback for handling exceptions
            retry_callback: Callback for retry attempts
            circuit_breaker_callback: Callback for when the circuit breaker trips
            fallback_value: Value to return if all retries fail
            
        Returns:
            Result of the operation or fallback value if operation fails
        """
        # Check if circuit breaker allows the request
        if not self.circuit_breaker.allow_request():
            logger.warning("Circuit breaker open, skipping operation")
            if circuit_breaker_callback:
                circuit_breaker_callback()
            return fallback_value
        
        # Execute the operation with retries
        attempt = 0
        start_time = time.time()
        
        while True:
            attempt += 1
            try:
                # Execute the operation
                result = operation()
                
                # Record success in circuit breaker
                self.circuit_breaker.record_success()
                
                return result
                
            except Exception as e:
                # Log the error
                logger.error(f"Operation failed on attempt {attempt}: {str(e)}")
                logger.debug(f"Detailed error: {traceback.format_exc()}")
                
                # Record failure in circuit breaker
                self.circuit_breaker.record_failure()
                
                # Call error handler if provided
                if error_handler:
                    error_handler(e)
                
                # Check if we should retry
                if self.retry_strategy.should_retry(e, attempt):
                    # Calculate delay for next retry
                    delay = self.retry_strategy.get_delay(attempt)
                    
                    # Check timeout if set
                    if self.retry_strategy.timeout:
                        elapsed = time.time() - start_time
                        if elapsed + delay > self.retry_strategy.timeout:
                            logger.warning(f"Retry timeout exceeded ({self.retry_strategy.timeout}s), giving up")
                            break
                    
                    # Notify about retry
                    if retry_callback:
                        retry_callback(attempt)
                    
                    logger.info(f"Retrying operation in {delay:.2f}s (attempt {attempt}/{self.retry_strategy.max_attempts})")
                    time.sleep(delay)
                    
                    # Continue to next attempt
                    continue
                
                # If we get here, we've exhausted all retries or the exception is not retryable
                logger.error(f"All retries failed or exception not retryable: {str(e)}")
                break
        
        # If we get here, all retries have failed
        return fallback_value