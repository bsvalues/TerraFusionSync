"""
Self-Healing Orchestrator for the SyncService.

This module provides capabilities for automatic detection and recovery of sync
operation failures with progressive retry strategies and circuit breaking.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from enum import Enum

from ...models.base import SyncOperation, SyncStatus, RetryStrategy

logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categories of failure that can be handled differently."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    DATA_FORMAT = "data_format"
    RESOURCE_CONSTRAINT = "resource_constraint"
    SYSTEM_ERROR = "system_error"
    UNKNOWN = "unknown"


class SelfHealingOrchestrator:
    """
    Orchestrates self-healing operations for sync operations.
    
    This class provides capabilities for:
    - Analyzing sync operation failures
    - Determining appropriate recovery strategies
    - Implementing progressive retries with backoff
    - Circuit breaking for persistent failures
    - Logging and auditing recovery attempts
    """
    
    def __init__(self, 
                 on_retry_callback: Optional[Callable[[int, SyncOperation], None]] = None,
                 on_circuit_break_callback: Optional[Callable[[SyncOperation], None]] = None):
        """
        Initialize the self-healing orchestrator.
        
        Args:
            on_retry_callback: Optional callback triggered when a retry is attempted
            on_circuit_break_callback: Optional callback triggered when circuit breaking is activated
        """
        self.on_retry_callback = on_retry_callback
        self.on_circuit_break_callback = on_circuit_break_callback
        self.failure_counts = {}  # Track failures by system/endpoint
        self.circuit_breakers = {}  # Track active circuit breakers
        self.max_failures = 5  # Max failures before circuit breaking
        self.circuit_open_duration = 300  # 5 minutes in seconds
    
    def analyze_failure(self, error: Exception, operation: SyncOperation) -> FailureCategory:
        """
        Analyze a failure to determine the category.
        
        Args:
            error: The exception that caused the failure
            operation: The sync operation that failed
            
        Returns:
            The category of failure
        """
        error_str = str(error).lower()
        
        # Analyze the error message to categorize the failure
        if any(kw in error_str for kw in ["timeout", "connection", "network", "unreachable"]):
            return FailureCategory.NETWORK
        elif any(kw in error_str for kw in ["auth", "unauthorized", "token", "credential"]):
            return FailureCategory.AUTHENTICATION
        elif any(kw in error_str for kw in ["permission", "forbidden", "access denied"]):
            return FailureCategory.PERMISSION
        elif any(kw in error_str for kw in ["format", "parse", "json", "xml", "schema"]):
            return FailureCategory.DATA_FORMAT
        elif any(kw in error_str for kw in ["memory", "disk", "capacity", "limit", "quota"]):
            return FailureCategory.RESOURCE_CONSTRAINT
        elif any(kw in error_str for kw in ["system", "internal", "server error"]):
            return FailureCategory.SYSTEM_ERROR
        else:
            return FailureCategory.UNKNOWN
    
    def determine_retry_strategy(self, 
                                failure_category: FailureCategory, 
                                operation: SyncOperation,
                                attempt: int = 1) -> Optional[RetryStrategy]:
        """
        Determine if and how to retry a failed sync operation.
        
        Args:
            failure_category: The category of failure
            operation: The failed sync operation
            attempt: The current retry attempt number
            
        Returns:
            RetryStrategy with details if retry is recommended, None otherwise
        """
        # Check if circuit breaker is active for the affected systems
        system_key = f"{operation.source_system}-{operation.target_system}"
        if system_key in self.circuit_breakers:
            circuit_open_until = self.circuit_breakers[system_key]
            if datetime.now() < circuit_open_until:
                logger.warning(f"Circuit breaker active for {system_key} until {circuit_open_until}, skipping retry")
                return None
            else:
                # Reset circuit breaker
                logger.info(f"Circuit breaker reset for {system_key}")
                del self.circuit_breakers[system_key]
                self.failure_counts[system_key] = 0
        
        # For these categories, don't retry as they need human intervention
        if failure_category in [FailureCategory.AUTHENTICATION, FailureCategory.PERMISSION]:
            return None
        
        # Define retry strategy based on failure category and attempt
        if failure_category == FailureCategory.NETWORK:
            if attempt <= 5:
                # Exponential backoff for network issues: 2, 4, 8, 16, 32 seconds
                delay = 2 ** attempt
                return RetryStrategy(
                    should_retry=True,
                    delay_seconds=delay,
                    max_attempts=5,
                    retry_subset=False  # Retry the entire operation
                )
        elif failure_category == FailureCategory.DATA_FORMAT:
            if attempt <= 2:
                # Try a couple of times with minimal delay for data format issues
                return RetryStrategy(
                    should_retry=True,
                    delay_seconds=5,
                    max_attempts=2,
                    retry_subset=True  # Only retry the failed records
                )
        elif failure_category == FailureCategory.RESOURCE_CONSTRAINT:
            if attempt <= 3:
                # Longer delays for resource constraints to allow system to recover
                delay = 30 * attempt  # 30, 60, 90 seconds
                batch_size_reduction = 0.5  # Reduce batch size by 50%
                return RetryStrategy(
                    should_retry=True,
                    delay_seconds=delay,
                    max_attempts=3,
                    retry_subset=False,  # Retry the entire operation
                    batch_size_reduction=batch_size_reduction
                )
        elif failure_category == FailureCategory.SYSTEM_ERROR:
            if attempt <= 3:
                # Progressive delays for system errors
                delay = 15 * attempt  # 15, 30, 45 seconds
                return RetryStrategy(
                    should_retry=True,
                    delay_seconds=delay,
                    max_attempts=3,
                    retry_subset=False
                )
        elif failure_category == FailureCategory.UNKNOWN:
            if attempt == 1:
                # Just try once more for unknown issues with a moderate delay
                return RetryStrategy(
                    should_retry=True,
                    delay_seconds=10,
                    max_attempts=1,
                    retry_subset=True
                )
        
        # If no specific strategy was defined, don't retry
        return None
    
    def record_failure(self, operation: SyncOperation) -> None:
        """
        Record a failure and check if circuit breaking is needed.
        
        Args:
            operation: The failed sync operation
        """
        system_key = f"{operation.source_system}-{operation.target_system}"
        self.failure_counts.setdefault(system_key, 0)
        self.failure_counts[system_key] += 1
        
        # Check if circuit breaking threshold is reached
        if self.failure_counts[system_key] >= self.max_failures:
            self._activate_circuit_breaker(system_key, operation)
    
    def _activate_circuit_breaker(self, system_key: str, operation: SyncOperation) -> None:
        """
        Activate circuit breaker for a specific system pair.
        
        Args:
            system_key: The system pair key (source-target)
            operation: The last operation that triggered the circuit breaker
        """
        open_until = datetime.now() + timedelta(seconds=self.circuit_open_duration)
        self.circuit_breakers[system_key] = open_until
        
        logger.warning(
            f"Circuit breaker activated for {system_key} until {open_until} "
            f"after {self.max_failures} consecutive failures"
        )
        
        # Call the callback if provided
        if self.on_circuit_break_callback:
            try:
                self.on_circuit_break_callback(operation)
            except Exception as e:
                logger.error(f"Error in circuit break callback: {str(e)}")
    
    def handle_retry(self, operation: SyncOperation, error: Exception, attempt: int = 1) -> Tuple[bool, int]:
        """
        Handle retry logic for a failed operation.
        
        Args:
            operation: The failed sync operation
            error: The exception that caused the failure
            attempt: Current attempt number
            
        Returns:
            Tuple of (should_retry, delay_seconds)
        """
        # Analyze the failure
        failure_category = self.analyze_failure(error, operation)
        
        # Record failure for circuit breaking
        self.record_failure(operation)
        
        # Determine retry strategy
        strategy = self.determine_retry_strategy(failure_category, operation, attempt)
        
        if not strategy or attempt >= strategy.max_attempts:
            return False, 0
        
        # Log and notify about the retry
        logger.info(
            f"Scheduling retry #{attempt} for operation {operation.id} "
            f"after {strategy.delay_seconds}s delay due to {failure_category.value} failure"
        )
        
        # Call the retry callback if provided
        if self.on_retry_callback:
            try:
                self.on_retry_callback(attempt, operation)
            except Exception as e:
                logger.error(f"Error in retry callback: {str(e)}")
        
        return True, strategy.delay_seconds
    
    def execute_with_self_healing(self, 
                                 operation: SyncOperation, 
                                 execution_func: Callable[[], Any],
                                 error_handler: Optional[Callable[[Exception], None]] = None) -> Any:
        """
        Execute a function with self-healing capabilities.
        
        Args:
            operation: The sync operation being executed
            execution_func: The function to execute (should be a callable with no arguments)
            error_handler: Optional function to call with the last error if all retries fail
            
        Returns:
            The result of the execution function, or None if it fails after all retries
        """
        attempt = 1
        max_attempts = 5  # Default max attempts
        
        while attempt <= max_attempts:
            try:
                return execution_func()
            except Exception as e:
                logger.error(f"Error during sync operation {operation.id} (attempt {attempt}): {str(e)}")
                
                should_retry, delay_seconds = self.handle_retry(operation, e, attempt)
                
                if should_retry and attempt < max_attempts:
                    logger.info(f"Retrying in {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                    attempt += 1
                else:
                    logger.warning(f"All retry attempts failed or retry not advised for operation {operation.id}")
                    if error_handler:
                        error_handler(e)
                    return None
        
        return None