"""
Retry Strategy implementations for the TerraFusion SyncService platform.

This module provides retry strategy abstractions used by the self-healing
orchestrator to manage retry attempts and backoff algorithms.
"""

import time
import random
import logging
from typing import Callable, Any, Dict, TypeVar, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

# Type variable for retryable functions
T = TypeVar('T')


class RetryStrategy:
    """
    Base class for retry strategies.
    
    Defines the interface for retry strategies, which are used to determine
    when and how to retry operations that have failed.
    """
    
    def should_retry(self, attempt: int, exception: Optional[Exception] = None) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            attempt: The current attempt number (1-based)
            exception: The exception that caused the failure, if any
            
        Returns:
            True if a retry should be attempted, False otherwise
        """
        raise NotImplementedError("Subclasses must implement should_retry")
    
    def get_retry_interval(self, attempt: int) -> float:
        """
        Get the number of seconds to wait before the next retry.
        
        Args:
            attempt: The current attempt number (1-based)
            
        Returns:
            The number of seconds to wait
        """
        raise NotImplementedError("Subclasses must implement get_retry_interval")
    
    def execute_with_retry(
        self, 
        func: Callable[..., T], 
        *args, 
        max_attempts: int = 3,
        on_retry_callback: Optional[Callable[[int, Exception], None]] = None,
        **kwargs
    ) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            func: The function to execute
            *args: Arguments to pass to the function
            max_attempts: Maximum number of attempts to make
            on_retry_callback: Optional callback function called before each retry
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            The last exception encountered if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Try executing the function
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt}/{max_attempts} for {func.__name__}")
                
                return func(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {str(e)}")
                
                # If this was the last attempt, re-raise the exception
                if attempt >= max_attempts or not self.should_retry(attempt, e):
                    logger.error(f"Max retries ({max_attempts}) reached for {func.__name__}")
                    raise
                
                # Call the retry callback if provided
                if on_retry_callback:
                    try:
                        on_retry_callback(attempt, e)
                    except Exception as callback_error:
                        logger.error(f"Error in retry callback: {str(callback_error)}")
                
                # Wait before retrying
                retry_interval = self.get_retry_interval(attempt)
                logger.info(f"Waiting {retry_interval:.2f} seconds before retry")
                time.sleep(retry_interval)
        
        # This should never be reached due to the re-raise in the loop,
        # but just in case:
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError("Unexpected end of retry loop")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy.
        
        Returns:
            Dictionary with retry strategy metrics
        """
        return {
            "type": self.__class__.__name__
        }


class ExponentialBackoffStrategy(RetryStrategy):
    """
    Exponential backoff retry strategy with jitter.
    
    This strategy increases the wait time exponentially with each retry attempt,
    and adds random jitter to prevent synchronized retries in distributed systems.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter_factor: float = 0.2,
        retryable_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize a new exponential backoff strategy.
        
        Args:
            base_delay: The base delay in seconds
            max_delay: The maximum delay in seconds
            multiplier: The multiplier for each retry
            jitter_factor: The factor by which to apply random jitter (0.0 to 1.0)
            retryable_exceptions: List of exception types that are retryable
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter_factor = min(max(0.0, jitter_factor), 1.0)  # Clamp to [0.0, 1.0]
        self.retryable_exceptions = retryable_exceptions or []
        self.start_time = datetime.utcnow()
        
        logger.info(
            f"Initialized ExponentialBackoffStrategy with base_delay={base_delay}, "
            f"max_delay={max_delay}, multiplier={multiplier}, jitter_factor={jitter_factor}"
        )
    
    def should_retry(self, attempt: int, exception: Optional[Exception] = None) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            attempt: The current attempt number (1-based)
            exception: The exception that caused the failure, if any
            
        Returns:
            True if a retry should be attempted, False otherwise
        """
        # If we have specific retryable exceptions and an exception was provided,
        # only retry if the exception is in the list
        if self.retryable_exceptions and exception:
            should_retry = any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
            if not should_retry:
                logger.info(f"Not retrying due to non-retryable exception: {type(exception).__name__}")
            return should_retry
        
        # Otherwise, always retry
        return True
    
    def get_retry_interval(self, attempt: int) -> float:
        """
        Get the number of seconds to wait before the next retry.
        
        Args:
            attempt: The current attempt number (1-based)
            
        Returns:
            The number of seconds to wait
        """
        # Calculate the exponential delay: base_delay * multiplier^(attempt-1)
        delay = self.base_delay * (self.multiplier ** (attempt - 1))
        
        # Apply a maximum delay cap
        delay = min(delay, self.max_delay)
        
        # Apply jitter: delay * (1 ± jitter_factor * random)
        if self.jitter_factor > 0:
            jitter = delay * self.jitter_factor * random.random()
            # Subtract or add jitter with equal probability
            if random.random() < 0.5:
                delay -= jitter
            else:
                delay += jitter
        
        return delay
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy.
        
        Returns:
            Dictionary with retry strategy metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "base_delay": self.base_delay,
            "max_delay": self.max_delay,
            "multiplier": self.multiplier,
            "jitter_factor": self.jitter_factor,
            "active_since": self.start_time.isoformat() if self.start_time else None,
            "retryable_exceptions": [exc.__name__ for exc in self.retryable_exceptions] if self.retryable_exceptions else []
        })
        return metrics


class LinearBackoffStrategy(RetryStrategy):
    """
    Linear backoff retry strategy.
    
    This strategy increases the wait time linearly with each retry attempt.
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        increment: float = 1.0,
        max_delay: float = 30.0,
        jitter_factor: float = 0.0,
        retryable_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize a new linear backoff strategy.
        
        Args:
            base_delay: The base delay in seconds
            increment: The increment to add for each retry
            max_delay: The maximum delay in seconds
            jitter_factor: The factor by which to apply random jitter (0.0 to 1.0)
            retryable_exceptions: List of exception types that are retryable
        """
        self.base_delay = base_delay
        self.increment = increment
        self.max_delay = max_delay
        self.jitter_factor = min(max(0.0, jitter_factor), 1.0)  # Clamp to [0.0, 1.0]
        self.retryable_exceptions = retryable_exceptions or []
        
        logger.info(
            f"Initialized LinearBackoffStrategy with base_delay={base_delay}, "
            f"increment={increment}, max_delay={max_delay}, jitter_factor={jitter_factor}"
        )
    
    def should_retry(self, attempt: int, exception: Optional[Exception] = None) -> bool:
        """
        Determine if a retry should be attempted.
        
        Args:
            attempt: The current attempt number (1-based)
            exception: The exception that caused the failure, if any
            
        Returns:
            True if a retry should be attempted, False otherwise
        """
        # If we have specific retryable exceptions and an exception was provided,
        # only retry if the exception is in the list
        if self.retryable_exceptions and exception:
            should_retry = any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
            if not should_retry:
                logger.info(f"Not retrying due to non-retryable exception: {type(exception).__name__}")
            return should_retry
        
        # Otherwise, always retry
        return True
    
    def get_retry_interval(self, attempt: int) -> float:
        """
        Get the number of seconds to wait before the next retry.
        
        Args:
            attempt: The current attempt number (1-based)
            
        Returns:
            The number of seconds to wait
        """
        # Calculate the linear delay: base_delay + increment * (attempt-1)
        delay = self.base_delay + self.increment * (attempt - 1)
        
        # Apply a maximum delay cap
        delay = min(delay, self.max_delay)
        
        # Apply jitter: delay * (1 ± jitter_factor * random)
        if self.jitter_factor > 0:
            jitter = delay * self.jitter_factor * random.random()
            # Subtract or add jitter with equal probability
            if random.random() < 0.5:
                delay -= jitter
            else:
                delay += jitter
        
        return delay