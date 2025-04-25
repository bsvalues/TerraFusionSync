"""
Core sync engine for the SyncService.

This module provides the main sync engine that orchestrates data transfers
between source and target systems, handling validation, transformation,
and error recovery.
"""

import logging
import json
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, Tuple, Type, Set
from datetime import datetime

from ..models.base import SyncOperation, SyncPair, SyncStatus, OperationType
from .self_healing.circuit_breaker import CircuitBreaker
from .self_healing.retry_strategy import RetryStrategy
from .self_healing.orchestrator import SelfHealingOrchestrator

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Core sync engine for transferring data between systems.
    
    The sync engine coordinates the entire sync process including:
    - Reading data from source systems
    - Transforming data according to mappings
    - Validating data integrity
    - Writing data to target systems
    - Handling errors and recovery
    """
    
    def __init__(
        self,
        orchestrator: Optional[SelfHealingOrchestrator] = None,
        retry_strategy: Optional[RetryStrategy] = None,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialize the sync engine.
        
        Args:
            orchestrator: Self-healing orchestrator to use
            retry_strategy: Default retry strategy for operations
            circuit_breaker: Default circuit breaker for operations
        """
        # Create or use provided components
        self.orchestrator = orchestrator or SelfHealingOrchestrator("SyncEngine")
        self.retry_strategy = retry_strategy or self.orchestrator.register_retry_strategy(
            name="default_sync_retry",
            max_attempts=5,
            initial_delay=2.0,
            max_delay=60.0,
            backoff_factor=2.0,
            jitter=True
        )
        self.circuit_breaker = circuit_breaker or self.orchestrator.register_circuit_breaker(
            name="default_sync_circuit",
            failure_threshold=3,
            recovery_timeout=300,  # 5 minutes
            reset_timeout=1800  # 30 minutes
        )
        
        # Register health check
        self.orchestrator.register_health_check("sync_engine", self._check_health)
        
        # Stats and metrics
        self.operations_completed = 0
        self.operations_failed = 0
        self.last_operation_time = None
        self.last_error = None
        
        logger.info("SyncEngine initialized with self-healing capabilities")
    
    def execute_sync(self, operation: SyncOperation) -> bool:
        """
        Execute a sync operation with self-healing capabilities.
        
        This method handles the entire sync process from start to finish,
        including reading from source, transforming data, and writing to target.
        
        Args:
            operation: The sync operation to execute
            
        Returns:
            True if the operation completed successfully, False otherwise
        """
        logger.info(f"Starting sync operation {operation.id} for pair {operation.sync_pair_id}")
        
        try:
            # Update operation status
            operation.status = SyncStatus.RUNNING
            operation.started_at = datetime.now()
            
            # Get sync pair details
            sync_pair = self._get_sync_pair(operation.sync_pair_id)
            if not sync_pair:
                raise ValueError(f"Sync pair {operation.sync_pair_id} not found")
            
            # Determine what systems we're connecting to
            source_system = sync_pair.source_system
            target_system = sync_pair.target_system
            
            # Create specific circuit breakers for source and target if needed
            source_cb = self.orchestrator.register_circuit_breaker(f"source_{sync_pair.id}")
            target_cb = self.orchestrator.register_circuit_breaker(f"target_{sync_pair.id}")
            
            # Execute each phase with resiliency
            data = self._read_from_source(operation, source_system, source_cb)
            if not data:
                raise ValueError("No data returned from source system")
                
            transformed_data = self._transform_data(operation, data, sync_pair.mappings)
            if not transformed_data:
                raise ValueError("Data transformation failed")
                
            success = self._write_to_target(operation, transformed_data, target_system, target_cb)
            if not success:
                raise ValueError("Failed to write to target system")
            
            # Update operation on success
            operation.status = SyncStatus.COMPLETED
            operation.completed_at = datetime.now()
            self.operations_completed += 1
            self.last_operation_time = datetime.now()
            
            logger.info(f"Sync operation {operation.id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Sync operation {operation.id} failed: {str(e)}")
            
            # Update operation on failure
            operation.status = SyncStatus.FAILED
            operation.completed_at = datetime.now()
            if operation.details:
                operation.details.error = str(e)
            self.operations_failed += 1
            self.last_error = str(e)
            self.last_operation_time = datetime.now()
            
            return False
    
    def _read_from_source(
        self, 
        operation: SyncOperation,
        source_config: Dict[str, Any],
        circuit_breaker: Optional[CircuitBreaker] = None
    ) -> List[Dict[str, Any]]:
        """
        Read data from the source system with resilience.
        
        Args:
            operation: The sync operation being executed
            source_config: Configuration for the source system
            circuit_breaker: Circuit breaker for the source system
            
        Returns:
            List of data records from the source
        """
        # Use the orchestrator to execute with resilience
        try:
            data = self.orchestrator.execute_with_resilience(
                func=lambda: self._execute_read(operation, source_config),
                circuit_name=circuit_breaker.name if circuit_breaker else "default_sync_circuit",
                retry_name="source_retry"
            )
            
            logger.info(f"Successfully read {len(data)} records from source for operation {operation.id}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to read from source for operation {operation.id}: {str(e)}")
            raise
    
    def _execute_read(self, operation: SyncOperation, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the actual read operation to the source system.
        
        This would be implemented with connectors for specific systems.
        
        Args:
            operation: The sync operation being executed
            source_config: Configuration for the source system
            
        Returns:
            List of data records from the source
        """
        # This would actually connect to the source system
        # For demonstration, we return mock data
        logger.info(f"Reading data from source system {source_config.get('type', 'unknown')}")
        
        # This is a placeholder and would be replaced with actual connection code
        # In a real implementation, this would use a connector to read from the source system
        # based on source_config and operation parameters
        
        # Simulate a read operation
        return [{"id": 1, "name": "Example Data"}]
    
    def _transform_data(
        self,
        operation: SyncOperation,
        data: List[Dict[str, Any]],
        mappings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform data according to mappings.
        
        Args:
            operation: The sync operation being executed
            data: Data records from the source
            mappings: Field mappings to apply
            
        Returns:
            Transformed data records
        """
        try:
            logger.info(f"Transforming {len(data)} records for operation {operation.id}")
            
            # This would apply the transformation mappings to convert source format to target format
            # For demonstration, we pass through the data
            transformed = []
            
            for record in data:
                # Apply mappings
                transformed_record = {}
                for mapping in mappings:
                    source_field = mapping.get('source_field')
                    target_field = mapping.get('target_field')
                    
                    if source_field in record:
                        transformed_record[target_field] = record[source_field]
                
                transformed.append(transformed_record)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Data transformation failed for operation {operation.id}: {str(e)}")
            raise
    
    def _write_to_target(
        self,
        operation: SyncOperation,
        data: List[Dict[str, Any]],
        target_config: Dict[str, Any],
        circuit_breaker: Optional[CircuitBreaker] = None
    ) -> bool:
        """
        Write data to the target system with resilience.
        
        Args:
            operation: The sync operation being executed
            data: Transformed data records
            target_config: Configuration for the target system
            circuit_breaker: Circuit breaker for the target system
            
        Returns:
            True if write was successful, False otherwise
        """
        # Use the orchestrator to execute with resilience
        try:
            result = self.orchestrator.execute_with_resilience(
                func=lambda: self._execute_write(operation, data, target_config),
                circuit_name=circuit_breaker.name if circuit_breaker else "default_sync_circuit",
                retry_name="target_retry"
            )
            
            logger.info(f"Successfully wrote {len(data)} records to target for operation {operation.id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to write to target for operation {operation.id}: {str(e)}")
            raise
    
    def _execute_write(
        self,
        operation: SyncOperation,
        data: List[Dict[str, Any]],
        target_config: Dict[str, Any]
    ) -> bool:
        """
        Execute the actual write operation to the target system.
        
        This would be implemented with connectors for specific systems.
        
        Args:
            operation: The sync operation being executed
            data: Transformed data records
            target_config: Configuration for the target system
            
        Returns:
            True if write was successful, False otherwise
        """
        # This would actually connect to the target system
        # For demonstration, we return success
        logger.info(f"Writing {len(data)} records to target system {target_config.get('type', 'unknown')}")
        
        # This is a placeholder and would be replaced with actual connection code
        # In a real implementation, this would use a connector to write to the target system
        # based on target_config and operation parameters
        
        # Simulate a write operation
        return True
    
    def _get_sync_pair(self, sync_pair_id: str) -> Optional[SyncPair]:
        """
        Get a sync pair by ID.
        
        In a real implementation, this would query the database.
        
        Args:
            sync_pair_id: ID of the sync pair
            
        Returns:
            SyncPair if found, None otherwise
        """
        # This is a placeholder and would be replaced with database query
        sync_pair = SyncPair(id=sync_pair_id, name="Demo Sync Pair")
        sync_pair.source_system = {
            "type": "cama",
            "url": "https://cama.example.org/api",
            "auth": "oauth"
        }
        sync_pair.target_system = {
            "type": "pacs",
            "url": "https://pacs.example.org/api",
            "auth": "basic"
        }
        sync_pair.mappings = [
            {"source_field": "id", "target_field": "record_id"},
            {"source_field": "name", "target_field": "record_name"}
        ]
        
        return sync_pair
    
    def _check_health(self) -> bool:
        """
        Health check for the sync engine.
        
        Returns:
            True if healthy, False otherwise
        """
        # Check if we've had too many recent failures
        if self.operations_completed == 0 and self.operations_failed > 5:
            return False
            
        # Check if circuit breakers are healthy
        for name, cb in self.orchestrator.circuit_breakers.items():
            if cb.state != "CLOSED":
                return False
                
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the sync engine.
        
        Returns:
            Dictionary with status information
        """
        return {
            "operations_completed": self.operations_completed,
            "operations_failed": self.operations_failed,
            "last_operation_time": self.last_operation_time.isoformat() if self.last_operation_time else None,
            "last_error": self.last_error,
            "health": self.orchestrator.get_health_status(),
            "circuit_breakers": {name: cb.get_status() for name, cb in self.orchestrator.circuit_breakers.items()}
        }