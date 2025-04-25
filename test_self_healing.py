"""
Test script for the TerraFusion SyncService self-healing capabilities.

This script tests the self-healing components to verify their functionality.
"""

import logging
import time
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("self_healing_test")

# Import self-healing components
from apps.backend.syncservice.syncservice.core.self_healing import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    FixedRetryStrategy,
    LinearRetryStrategy,
    ExponentialRetryStrategy,
    ExponentialWithJitterRetryStrategy,
    RetryStrategyType,
    SelfHealingOrchestrator,
    HealthCheck,
    HealthStatus,
    ResourceType
)


def test_circuit_breaker():
    """Test the CircuitBreaker functionality."""
    logger.info("===== Testing Circuit Breaker =====")
    
    # Create a circuit breaker
    cb = CircuitBreaker(
        name="test_circuit",
        failure_threshold=3,
        reset_timeout=5,  # Short timeout for testing
        half_open_success_threshold=2
    )
    
    # Test function that succeeds
    def success_function():
        logger.info("Success function called")
        return "success"
    
    # Test function that fails
    def failure_function():
        logger.error("Failure function called")
        raise ValueError("Simulated failure")
    
    # Test successful execution
    logger.info("Testing successful execution...")
    for i in range(3):
        result = cb.execute(success_function)
        logger.info(f"Result: {result}, Circuit state: {cb.state.value}")
    
    # Test failure execution until circuit opens
    logger.info("Testing failure execution until circuit opens...")
    try:
        for i in range(5):  # More than failure_threshold
            try:
                cb.execute(failure_function)
            except ValueError as e:
                logger.info(f"Expected error: {str(e)}, Circuit state: {cb.state.value}")
    except CircuitOpenError as e:
        logger.info(f"Circuit opened as expected: {str(e)}")
    
    # Wait for reset timeout to allow circuit to transition to half-open
    logger.info(f"Waiting for reset timeout ({cb.reset_timeout} seconds)...")
    time.sleep(cb.reset_timeout + 1)
    
    # Test half-open state with successful calls to close the circuit
    logger.info("Testing half-open state with successful calls...")
    for i in range(cb.half_open_success_threshold):
        try:
            result = cb.execute(success_function)
            logger.info(f"Success in half-open state: {result}, Circuit state: {cb.state.value}")
        except CircuitOpenError as e:
            logger.error(f"Unexpected circuit open error: {str(e)}")
    
    logger.info(f"Final circuit state: {cb.state.value}")
    logger.info("Circuit breaker test complete")


def test_retry_strategies():
    """Test the retry strategies functionality."""
    logger.info("===== Testing Retry Strategies =====")
    
    # Create retry strategies
    fixed = FixedRetryStrategy(wait_time=1.0, max_retries=3)
    linear = LinearRetryStrategy(initial_wait_time=1.0, increment=1.0, max_retries=3)
    exponential = ExponentialRetryStrategy(initial_wait_time=1.0, base=2.0, max_retries=3)
    exponential_jitter = ExponentialWithJitterRetryStrategy(initial_wait_time=1.0, base=2.0, max_retries=3)
    
    # Test function that succeeds after N attempts
    def success_after_attempts(max_failures):
        attempts = [0]  # Use list for mutable closure
        
        def inner_function():
            attempts[0] += 1
            if attempts[0] <= max_failures:
                logger.info(f"Attempt {attempts[0]}/{max_failures+1} failing...")
                raise ValueError(f"Simulated failure on attempt {attempts[0]}")
            logger.info(f"Attempt {attempts[0]}/{max_failures+1} succeeding!")
            return f"success on attempt {attempts[0]}"
        
        return inner_function
    
    # Test function that always fails
    def always_fails():
        logger.error("Function always fails")
        raise ValueError("Simulated failure")
    
    # Test each strategy with a function that succeeds after 2 attempts
    strategies = [
        ("Fixed", fixed),
        ("Linear", linear),
        ("Exponential", exponential),
        ("Exponential with Jitter", exponential_jitter)
    ]
    
    for name, strategy in strategies:
        logger.info(f"Testing {name} retry strategy...")
        try:
            result = strategy.execute(success_after_attempts(2))
            logger.info(f"{name} strategy result: {result}")
            logger.info(f"{name} strategy metrics: {strategy.get_metrics()}")
        except Exception as e:
            logger.error(f"{name} strategy unexpected error: {str(e)}")
    
    # Test max retries exceeded
    logger.info("Testing max retries exceeded...")
    try:
        fixed.execute(always_fails)
    except ValueError as e:
        logger.info(f"Expected error after max retries: {str(e)}")
    
    logger.info("Retry strategies test complete")


def test_self_healing_orchestrator():
    """Test the SelfHealingOrchestrator functionality."""
    logger.info("===== Testing Self-Healing Orchestrator =====")
    
    # Create orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Register a circuit breaker
    cb = orchestrator.register_circuit_breaker(
        name="test_circuit",
        failure_threshold=3,
        reset_timeout=5
    )
    
    # Register a retry strategy
    rs = orchestrator.register_retry_strategy(
        name="test_retry",
        strategy_type=RetryStrategyType.EXPONENTIAL_WITH_JITTER,
        max_retries=3
    )
    
    # Create a mock health check function
    health_state = {"healthy": True}
    
    def check_health():
        return health_state["healthy"]
    
    # Register a health check
    hc = orchestrator.register_health_check(
        resource_type=ResourceType.SYSTEM,
        resource_id="test_system",
        check_function=check_health,
        description="Test health check",
        interval_seconds=1,
        failure_threshold=2,
        recovery_threshold=1
    )
    
    # Register a recovery action
    def recovery_action(resource_type, resource_id, status):
        logger.info(f"Recovery action called for {resource_type.value}:{resource_id} (status: {status.value})")
        health_state["healthy"] = True
        return True
    
    orchestrator.register_recovery_action(
        resource_type=ResourceType.SYSTEM,
        resource_id="test_system",
        recovery_function=recovery_action,
        cooldown_seconds=2
    )
    
    # Test function that succeeds
    def success_function():
        logger.info("Success function called")
        return "success"
    
    # Test function that fails
    def failure_function():
        logger.error("Failure function called")
        raise ValueError("Simulated failure")
    
    # Test execute_with_resilience with success
    logger.info("Testing execute_with_resilience with success...")
    result = orchestrator.execute_with_resilience(
        function=success_function,
        circuit_name="test_circuit",
        retry_name="test_retry"
    )
    logger.info(f"Result: {result}")
    
    # Test health check when healthy
    logger.info("Testing health check when healthy...")
    health_results = orchestrator.run_health_checks(force_run=True)
    logger.info(f"Health results: {health_results}")
    
    # Test health check when unhealthy
    logger.info("Testing health check when unhealthy...")
    health_state["healthy"] = False
    
    # Run multiple health checks to trigger UNHEALTHY state
    for i in range(3):
        health_results = orchestrator.run_health_checks(force_run=True)
        logger.info(f"Health results after {i+1} unhealthy checks: {health_results}")
        time.sleep(0.5)
    
    # Get overall health status
    logger.info("Testing get_health_status...")
    health_status = orchestrator.get_health_status()
    logger.info(f"Health status: {health_status['status']}")
    
    # Check if recovery was attempted
    logger.info("Checking if recovery was attempted...")
    if health_state["healthy"]:
        logger.info("Recovery was successful!")
    else:
        logger.warning("Recovery did not set health back to healthy")
    
    logger.info("Self-healing orchestrator test complete")


def test_integrated_self_healing():
    """Test integrated self-healing functionality."""
    logger.info("===== Testing Integrated Self-Healing =====")
    
    # Create orchestrator
    orchestrator = SelfHealingOrchestrator()
    
    # Register components
    cb = orchestrator.register_circuit_breaker(name="integrated_test", failure_threshold=3)
    rs = orchestrator.register_retry_strategy(name="integrated_test")
    
    # Simulated database with failure probability
    class MockDatabase:
        def __init__(self, failure_rate=0.5):
            self.failure_rate = failure_rate
            self.connected = True
        
        def query(self, sql):
            if not self.connected:
                raise ValueError("Database not connected")
                
            if random.random() < self.failure_rate:
                raise ValueError("Simulated database query failure")
                
            return [{"id": 1, "name": "test"}]
            
        def disconnect(self):
            self.connected = False
            
        def connect(self):
            self.connected = True
    
    db = MockDatabase()
    
    # Register health check and recovery
    def check_db_health():
        return db.connected
    
    def recover_db(resource_type, resource_id, status):
        logger.info(f"Attempting to recover database (status: {status.value})")
        db.connect()
        return True
    
    orchestrator.register_health_check(
        resource_type=ResourceType.DATABASE,
        resource_id="mock_db",
        check_function=check_db_health,
        description="Database connection check"
    )
    
    orchestrator.register_recovery_action(
        resource_type=ResourceType.DATABASE,
        resource_id="mock_db",
        recovery_function=recover_db
    )
    
    # Test function with database query
    def db_operation():
        return db.query("SELECT * FROM test")
    
    # Test successful query with retries and circuit breaker
    logger.info("Testing database operations with retries...")
    
    try:
        for i in range(10):
            try:
                result = orchestrator.execute_with_resilience(
                    function=db_operation,
                    circuit_name="integrated_test",
                    retry_name="integrated_test"
                )
                logger.info(f"Query {i+1} successful: {result}")
            except Exception as e:
                logger.warning(f"Query {i+1} failed: {str(e)}")
    except CircuitOpenError as e:
        logger.info(f"Circuit opened as expected: {str(e)}")
    
    # Disconnect database to trigger recovery
    logger.info("Testing recovery by disconnecting database...")
    db.disconnect()
    
    # Run health checks to detect failure
    health_results = orchestrator.run_health_checks(force_run=True)
    logger.info(f"Health results after disconnect: {health_results}")
    
    # Check if database was reconnected by recovery action
    if db.connected:
        logger.info("Database successfully reconnected by recovery action")
    else:
        logger.warning("Database recovery failed")
    
    # Final health status
    health_status = orchestrator.get_health_status()
    logger.info(f"Final health status: {health_status['status']}")
    
    logger.info("Integrated self-healing test complete")


if __name__ == "__main__":
    try:
        test_circuit_breaker()
        print("\n")
        
        test_retry_strategies()
        print("\n")
        
        test_self_healing_orchestrator()
        print("\n")
        
        test_integrated_self_healing()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}")
        raise