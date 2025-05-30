"""
Self-healing package for TerraFusion SyncService platform.

This package provides components for implementing self-healing capabilities
including circuit breakers, retry strategies, and health monitoring.
"""

from .circuit_breaker import CircuitBreaker, CircuitOpenError, CircuitState
from .retry_strategy import (
    BaseRetryStrategy,
    FixedRetryStrategy,
    LinearRetryStrategy,
    ExponentialRetryStrategy,
    ExponentialWithJitterRetryStrategy,
    RetryStrategyType,
    create_retry_strategy
)
from .orchestrator import (
    SelfHealingOrchestrator,
    HealthCheck,
    HealthStatus,
    ResourceType
)

__all__ = [
    'CircuitBreaker',
    'CircuitOpenError',
    'CircuitState',
    'BaseRetryStrategy',
    'FixedRetryStrategy',
    'LinearRetryStrategy',
    'ExponentialRetryStrategy',
    'ExponentialWithJitterRetryStrategy',
    'RetryStrategyType',
    'create_retry_strategy',
    'SelfHealingOrchestrator',
    'HealthCheck',
    'HealthStatus',
    'ResourceType'
]