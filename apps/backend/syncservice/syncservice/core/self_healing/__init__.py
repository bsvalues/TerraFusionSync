"""
Self-healing package for TerraFusion SyncService platform.

This package provides components for implementing self-healing capabilities 
in the SyncService, including circuit breakers, retry strategies, and
orchestration of recovery operations.
"""

from .circuit_breaker import CircuitBreaker
from .retry_strategy import RetryStrategy, ExponentialBackoffStrategy
from .orchestrator import SelfHealingOrchestrator