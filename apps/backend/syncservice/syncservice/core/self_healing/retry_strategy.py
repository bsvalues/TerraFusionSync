"""
Retry strategy implementation for the SyncService.

This module provides configurable retry strategies for handling transient failures
when interacting with external systems, including exponential backoff and jitter.
"""

import time
import random
import logging
from typing import Callable, Any, List, Dict, Set, Optional, Type, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryStrategy:
    """
    Configurable retry strategy for handling transient failures.
    
    This class implements different retry patterns including fixed delay,
    exponential backoff, and exponential backoff with jitter for avoiding
    thundering herd problems.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retry_on_exceptions: Optional[Set[Type[Exception]]] = None
    ):
        """
        Initialize a new retry strategy.
        
        Args:
            max_attempts: Maximum number of attempts including the initial one
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Multiplier for exponential backoff
            jitter: Whether to add randomized jitter to delays
            retry_on_exceptions: Set of exception types to retry on (default: all)
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions or {Exception}
        
        self.attempt_logs = []
        
        logger.info(f"RetryStrategy initialized with max_attempts={max_attempts}, "
                   f"initial_delay={initial_delay}, backoff_factor={backoff_factor}")
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """
        Determine if an operation should be retried based on the exception and attempt.
        
        Args:
            exception: The exception that caused the failure
            attempt: Current attempt number (1-based)
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Check if we've exceeded max attempts
        if attempt >= self.max_attempts:
            return False
        
        # Check if the exception is retryable
        for exc_type in self.retry_on_exceptions:
            if isinstance(exception, exc_type):
                return True
        
        return False
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate the delay for a given retry attempt.
        
        Args:
            attempt: Current attempt number (1-based)
            
        Returns:
            Delay in seconds before the next retry
        """
        if attempt <= 1:
            return 0  # No delay for first attempt
        
        # Calculate exponential backoff
        delay = min(self.initial_delay * (self.backoff_factor ** (attempt - 2)), self.max_delay)
        
        # Add jitter if enabled (between 80-120% of calculated delay)
        if self.jitter:
            delay = delay * (0.8 + random.random() * 0.4)
        
        return delay
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with retry logic.
        
        Args:
            func: The function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function if successful
            
        Raises:
            Exception: If all retry attempts fail
        """
        self.attempt_logs = []
        attempt = 1
        last_exception = None
        
        while attempt <= self.max_attempts:
            try:
                start_time = datetime.now()
                
                # Log attempt
                logger.debug(f"Retry attempt {attempt}/{self.max_attempts} for {func.__name__}")
                
                # Execute function
                result = func(*args, **kwargs)
                
                # Record successful attempt
                end_time = datetime.now()
                self.attempt_logs.append({
                    'attempt': attempt,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': (end_time - start_time).total_seconds(),
                    'success': True,
                    'exception': None
                })
                
                return result
                
            except Exception as e:
                end_time = datetime.now()
                last_exception = e
                
                # Record failed attempt
                self.attempt_logs.append({
                    'attempt': attempt,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': (end_time - start_time).total_seconds(),
                    'success': False,
                    'exception': str(e),
                    'exception_type': type(e).__name__
                })
                
                # Check if we should retry
                if self.should_retry(e, attempt):
                    delay = self.calculate_delay(attempt)
                    
                    logger.warning(f"Retry attempt {attempt}/{self.max_attempts} failed: {str(e)}. "
                                  f"Retrying in {delay:.2f} seconds...")
                    
                    # Wait before retry
                    time.sleep(delay)
                    attempt += 1
                else:
                    logger.error(f"All retry attempts failed for {func.__name__}. "
                                f"Last error: {str(e)}")
                    raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        # This should never happen unless max_attempts is set incorrectly
        raise RuntimeError("Retry strategy failed with no exception")
    
    def get_attempt_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of retry attempts.
        
        Returns:
            List of dictionaries with attempt information
        """
        return self.attempt_logs
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about retry attempts.
        
        Returns:
            Dictionary with retry statistics
        """
        total_attempts = len(self.attempt_logs)
        successful_attempts = sum(1 for log in self.attempt_logs if log.get('success', False))
        failed_attempts = total_attempts - successful_attempts
        
        total_duration = 0
        if self.attempt_logs:
            first_start = min(log['start_time'] for log in self.attempt_logs)
            last_end = max(log['end_time'] for log in self.attempt_logs)
            total_duration = (last_end - first_start).total_seconds()
        
        return {
            'total_attempts': total_attempts,
            'successful_attempts': successful_attempts,
            'failed_attempts': failed_attempts,
            'total_duration': total_duration,
            'success_rate': (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
        }