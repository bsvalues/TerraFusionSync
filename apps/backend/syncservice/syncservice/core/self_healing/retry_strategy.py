"""
Retry strategy implementations for TerraFusion SyncService platform.

This module provides robust retry strategies for handling transient failures
and improving resilience of the SyncService operations.
"""

import logging
import random
import time
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

T = TypeVar('T')
logger = logging.getLogger(__name__)


class RetryStrategyType(Enum):
    """Types of retry strategies available."""
    FIXED = auto()
    LINEAR = auto() 
    EXPONENTIAL = auto()  # Standard exponential backoff
    EXPONENTIAL_WITH_JITTER = auto()  # Exponential with randomization to prevent thundering herd


class BaseRetryStrategy:
    """Base class for retry strategies."""
    
    def __init__(
        self,
        max_retries: int = 3,
        max_retry_time: int = 300,  # 5 minutes maximum retry time
        retry_on_exceptions: List[type] = None,
        on_retry_callback: Optional[Callable[[int, Exception, float], None]] = None,
        on_success_callback: Optional[Callable[[int, Any], None]] = None,
        on_failure_callback: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        Initialize the retry strategy.
        
        Args:
            max_retries: Maximum number of retry attempts
            max_retry_time: Maximum time to spend retrying in seconds
            retry_on_exceptions: List of exception types to retry on
            on_retry_callback: Callback called before each retry attempt with (attempt, exception, next_wait_time)
            on_success_callback: Callback called on successful execution with (attempts, result)
            on_failure_callback: Callback called when all retries are exhausted with (attempts, last_exception)
        """
        self.max_retries = max_retries
        self.max_retry_time = max_retry_time
        self.retry_on_exceptions = retry_on_exceptions or [Exception]
        self.on_retry_callback = on_retry_callback
        self.on_success_callback = on_success_callback
        self.on_failure_callback = on_failure_callback
        
        # Metrics for tracking retry performance
        self.total_attempts = 0
        self.total_retries = 0
        self.successful_executions = 0
        self.failed_executions = 0
    
    def execute(self, function: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute a function with retry logic.
        
        Args:
            function: The function to execute
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            The result of the function
            
        Raises:
            Exception: The last exception if all retries are exhausted
        """
        attempts = 0
        start_time = time.time()
        last_exception = None
        
        while attempts <= self.max_retries:
            attempts += 1
            self.total_attempts += 1
            
            try:
                result = function(*args, **kwargs)
                
                # Success! Log it and return the result
                logger.info(f"Operation succeeded after {attempts} attempt(s)")
                self.successful_executions += 1
                
                # Call the success callback if provided
                if self.on_success_callback:
                    try:
                        self.on_success_callback(attempts, result)
                    except Exception as e:
                        logger.error(f"Error in on_success_callback: {str(e)}")
                
                return result
                
            except Exception as e:
                # Check if we should retry this type of exception
                should_retry = False
                for exc_type in self.retry_on_exceptions:
                    if isinstance(e, exc_type):
                        should_retry = True
                        break
                
                if not should_retry:
                    logger.info(f"Not retrying on exception type {type(e).__name__}")
                    raise
                
                last_exception = e
                
                # Check if we've reached max retries
                if attempts > self.max_retries:
                    logger.warning(f"Max retries ({self.max_retries}) reached")
                    self.failed_executions += 1
                    
                    # Call the failure callback if provided
                    if self.on_failure_callback:
                        try:
                            self.on_failure_callback(attempts, last_exception)
                        except Exception as cb_err:
                            logger.error(f"Error in on_failure_callback: {str(cb_err)}")
                    
                    raise
                
                # Check if we've exceeded max retry time
                elapsed_time = time.time() - start_time
                if elapsed_time > self.max_retry_time:
                    logger.warning(f"Max retry time ({self.max_retry_time}s) exceeded")
                    self.failed_executions += 1
                    
                    # Call the failure callback if provided
                    if self.on_failure_callback:
                        try:
                            self.on_failure_callback(attempts, last_exception)
                        except Exception as cb_err:
                            logger.error(f"Error in on_failure_callback: {str(cb_err)}")
                    
                    raise
                
                # We're going to retry, calculate wait time
                self.total_retries += 1
                wait_time = self._calculate_wait_time(attempts, elapsed_time)
                
                logger.warning(f"Retry {attempts}/{self.max_retries} after exception: {str(e)}. "
                              f"Waiting {wait_time:.2f}s before next attempt.")
                
                # Call the retry callback if provided
                if self.on_retry_callback:
                    try:
                        self.on_retry_callback(attempts, last_exception, wait_time)
                    except Exception as cb_err:
                        logger.error(f"Error in on_retry_callback: {str(cb_err)}")
                
                # Wait before the next attempt
                time.sleep(wait_time)
    
    def _calculate_wait_time(self, attempt: int, elapsed_time: float) -> float:
        """
        Calculate the wait time before the next retry attempt.
        
        Args:
            attempt: The current attempt number (1-based)
            elapsed_time: Time elapsed since the first attempt in seconds
            
        Returns:
            The wait time in seconds
        """
        # Default implementation (fixed delay)
        return 1.0
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy's performance.
        
        Returns:
            Dictionary with retry metrics
        """
        return {
            "total_attempts": self.total_attempts,
            "total_retries": self.total_retries,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": (self.successful_executions / self.total_attempts) 
                            if self.total_attempts > 0 else 0.0,
            "type": self.__class__.__name__,
            "max_retries": self.max_retries,
            "max_retry_time": self.max_retry_time
        }
    
    def reset_metrics(self) -> None:
        """Reset the performance metrics."""
        self.total_attempts = 0
        self.total_retries = 0
        self.successful_executions = 0
        self.failed_executions = 0


class FixedRetryStrategy(BaseRetryStrategy):
    """
    Fixed delay retry strategy.
    
    This strategy waits a fixed amount of time between each retry attempt.
    """
    
    def __init__(
        self,
        wait_time: float = 1.0,
        **kwargs
    ):
        """
        Initialize the fixed retry strategy.
        
        Args:
            wait_time: Fixed wait time between retries in seconds
            **kwargs: Additional arguments passed to BaseRetryStrategy
        """
        super().__init__(**kwargs)
        self.wait_time = wait_time
    
    def _calculate_wait_time(self, attempt: int, elapsed_time: float) -> float:
        """
        Calculate the wait time before the next retry attempt.
        
        For fixed strategy, this is always the fixed wait time.
        
        Args:
            attempt: The current attempt number (1-based)
            elapsed_time: Time elapsed since the first attempt in seconds
            
        Returns:
            The wait time in seconds
        """
        return self.wait_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy's performance.
        
        Returns:
            Dictionary with retry metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "wait_time": self.wait_time
        })
        return metrics


class LinearRetryStrategy(BaseRetryStrategy):
    """
    Linear backoff retry strategy.
    
    This strategy increases the wait time linearly with each retry attempt.
    """
    
    def __init__(
        self,
        initial_wait_time: float = 1.0,
        increment: float = 1.0,
        **kwargs
    ):
        """
        Initialize the linear retry strategy.
        
        Args:
            initial_wait_time: Initial wait time for the first retry in seconds
            increment: Amount to increase wait time for each subsequent retry in seconds
            **kwargs: Additional arguments passed to BaseRetryStrategy
        """
        super().__init__(**kwargs)
        self.initial_wait_time = initial_wait_time
        self.increment = increment
    
    def _calculate_wait_time(self, attempt: int, elapsed_time: float) -> float:
        """
        Calculate the wait time before the next retry attempt.
        
        For linear strategy, wait time increases linearly with each attempt:
        wait_time = initial_wait_time + (attempt - 1) * increment
        
        Args:
            attempt: The current attempt number (1-based)
            elapsed_time: Time elapsed since the first attempt in seconds
            
        Returns:
            The wait time in seconds
        """
        return self.initial_wait_time + (attempt - 1) * self.increment
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy's performance.
        
        Returns:
            Dictionary with retry metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "initial_wait_time": self.initial_wait_time,
            "increment": self.increment
        })
        return metrics


class ExponentialRetryStrategy(BaseRetryStrategy):
    """
    Exponential backoff retry strategy.
    
    This strategy increases the wait time exponentially with each retry attempt.
    """
    
    def __init__(
        self,
        initial_wait_time: float = 1.0,
        base: float = 2.0,
        max_wait_time: float = 60.0,  # 1 minute maximum wait time
        **kwargs
    ):
        """
        Initialize the exponential retry strategy.
        
        Args:
            initial_wait_time: Initial wait time for the first retry in seconds
            base: Base of the exponential function
            max_wait_time: Maximum wait time between retries in seconds
            **kwargs: Additional arguments passed to BaseRetryStrategy
        """
        super().__init__(**kwargs)
        self.initial_wait_time = initial_wait_time
        self.base = base
        self.max_wait_time = max_wait_time
    
    def _calculate_wait_time(self, attempt: int, elapsed_time: float) -> float:
        """
        Calculate the wait time before the next retry attempt.
        
        For exponential strategy, wait time increases exponentially with each attempt:
        wait_time = initial_wait_time * (base ^ (attempt - 1))
        
        Args:
            attempt: The current attempt number (1-based)
            elapsed_time: Time elapsed since the first attempt in seconds
            
        Returns:
            The wait time in seconds, capped at max_wait_time
        """
        wait_time = self.initial_wait_time * (self.base ** (attempt - 1))
        return min(wait_time, self.max_wait_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy's performance.
        
        Returns:
            Dictionary with retry metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "initial_wait_time": self.initial_wait_time,
            "base": self.base,
            "max_wait_time": self.max_wait_time
        })
        return metrics


class ExponentialWithJitterRetryStrategy(ExponentialRetryStrategy):
    """
    Exponential backoff with jitter retry strategy.
    
    This strategy adds randomness to the exponential backoff to prevent thundering herd
    problems when multiple clients are retrying simultaneously.
    """
    
    def __init__(
        self,
        jitter_factor: float = 0.2,  # 20% jitter by default
        **kwargs
    ):
        """
        Initialize the exponential with jitter retry strategy.
        
        Args:
            jitter_factor: Factor to determine the range of jitter (0.0 to 1.0)
            **kwargs: Additional arguments passed to ExponentialRetryStrategy
        """
        super().__init__(**kwargs)
        self.jitter_factor = max(0.0, min(1.0, jitter_factor))  # Clamp to [0.0, 1.0]
    
    def _calculate_wait_time(self, attempt: int, elapsed_time: float) -> float:
        """
        Calculate the wait time before the next retry attempt.
        
        For exponential with jitter strategy, we calculate the base exponential wait time
        and then add a random jitter based on the jitter factor.
        
        Args:
            attempt: The current attempt number (1-based)
            elapsed_time: Time elapsed since the first attempt in seconds
            
        Returns:
            The wait time in seconds with added jitter, capped at max_wait_time
        """
        # Get the base exponential wait time
        base_wait_time = super()._calculate_wait_time(attempt, elapsed_time)
        
        # Calculate the jitter range
        jitter_range = base_wait_time * self.jitter_factor
        
        # Apply random jitter within the range [-jitter_range/2, +jitter_range/2]
        jitter = random.uniform(-jitter_range/2, jitter_range/2)
        
        # Apply jitter to wait time but ensure it's not negative
        wait_time = max(0.001, base_wait_time + jitter)
        
        # Cap at max_wait_time
        return min(wait_time, self.max_wait_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get metrics about the retry strategy's performance.
        
        Returns:
            Dictionary with retry metrics
        """
        metrics = super().get_metrics()
        metrics.update({
            "jitter_factor": self.jitter_factor
        })
        return metrics


def create_retry_strategy(
    strategy_type: Union[str, RetryStrategyType] = RetryStrategyType.EXPONENTIAL_WITH_JITTER,
    **kwargs
) -> BaseRetryStrategy:
    """
    Factory function to create retry strategies.
    
    Args:
        strategy_type: Type of retry strategy to create
        **kwargs: Additional arguments to pass to the strategy constructor
        
    Returns:
        The created retry strategy instance
        
    Raises:
        ValueError: If strategy_type is not recognized
    """
    # Convert string to enum if needed
    if isinstance(strategy_type, str):
        try:
            strategy_type = RetryStrategyType[strategy_type.upper()]
        except KeyError:
            valid_types = ", ".join(s.name for s in RetryStrategyType)
            raise ValueError(f"Unknown retry strategy type: {strategy_type}. "
                            f"Valid types are: {valid_types}")
    
    # Create the appropriate strategy
    if strategy_type == RetryStrategyType.FIXED:
        return FixedRetryStrategy(**kwargs)
    elif strategy_type == RetryStrategyType.LINEAR:
        return LinearRetryStrategy(**kwargs)
    elif strategy_type == RetryStrategyType.EXPONENTIAL:
        return ExponentialRetryStrategy(**kwargs)
    elif strategy_type == RetryStrategyType.EXPONENTIAL_WITH_JITTER:
        return ExponentialWithJitterRetryStrategy(**kwargs)
    else:
        valid_types = ", ".join(s.name for s in RetryStrategyType)
        raise ValueError(f"Unknown retry strategy type: {strategy_type}. "
                        f"Valid types are: {valid_types}")