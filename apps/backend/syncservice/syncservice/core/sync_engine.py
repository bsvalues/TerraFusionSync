"""
Core sync engine for the TerraFusion SyncService platform.

This module provides the main synchronization logic, including data extraction,
transformation, and loading between systems.
"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from .self_healing import (
    SelfHealingOrchestrator,
    ResourceType,
    HealthStatus,
    CircuitBreaker,
    CircuitOpenError,
    ExponentialWithJitterRetryStrategy
)

logger = logging.getLogger(__name__)


class SyncEngine:
    """
    Core synchronization engine for TerraFusion SyncService.
    
    This class handles the core ETL (Extract, Transform, Load) operations
    for data synchronization between systems.
    """
    
    def __init__(self):
        """Initialize the sync engine with self-healing capabilities."""
        # Initialize the self-healing orchestrator
        self.orchestrator = SelfHealingOrchestrator()
        
        # Register circuit breakers for different systems
        self._register_circuit_breakers()
        
        # Register retry strategies for different operations
        self._register_retry_strategies()
        
        # Register health checks for monitoring
        self._register_health_checks()
        
        # Register recovery actions for auto-healing
        self._register_recovery_actions()
        
        logger.info("SyncEngine initialized with self-healing capabilities")
    
    def _register_circuit_breakers(self):
        """Register circuit breakers for different systems and operations."""
        # Source system circuit breaker
        self.orchestrator.register_circuit_breaker(
            name="source_system",
            failure_threshold=5,
            reset_timeout=60,  # 1 minute timeout before half-open
            half_open_success_threshold=2  # Need 2 successful calls to close circuit
        )
        
        # Target system circuit breaker
        self.orchestrator.register_circuit_breaker(
            name="target_system",
            failure_threshold=5,
            reset_timeout=60
        )
        
        # Transformation circuit breaker
        self.orchestrator.register_circuit_breaker(
            name="transformation",
            failure_threshold=3,
            reset_timeout=30  # Shorter timeout for transformation errors
        )
    
    def _register_retry_strategies(self):
        """Register retry strategies for different operations."""
        # Source system retry strategy
        self.orchestrator.register_retry_strategy(
            name="source_read",
            max_retries=3,
            initial_wait_time=2.0,
            max_wait_time=30.0
        )
        
        # Target system retry strategy
        self.orchestrator.register_retry_strategy(
            name="target_write",
            max_retries=5,  # More retries for target system
            initial_wait_time=1.0,
            max_wait_time=60.0
        )
        
        # Transformation retry strategy
        self.orchestrator.register_retry_strategy(
            name="transform",
            max_retries=2,  # Fewer retries for transformation errors
            initial_wait_time=1.0,
            max_wait_time=10.0
        )
    
    def _register_health_checks(self):
        """Register health checks for monitoring system components."""
        # Source system health check
        self.orchestrator.register_health_check(
            resource_type=ResourceType.SOURCE_SYSTEM,
            resource_id="default",
            check_function=self._check_source_system_health,
            description="Source system connectivity and health check",
            interval_seconds=60,
            failure_threshold=3,
            recovery_threshold=2
        )
        
        # Target system health check
        self.orchestrator.register_health_check(
            resource_type=ResourceType.TARGET_SYSTEM,
            resource_id="default",
            check_function=self._check_target_system_health,
            description="Target system connectivity and health check",
            interval_seconds=60,
            failure_threshold=3,
            recovery_threshold=2
        )
        
        # Database health check
        self.orchestrator.register_health_check(
            resource_type=ResourceType.DATABASE,
            resource_id="main",
            check_function=self._check_database_health,
            description="Database connectivity check",
            interval_seconds=120,
            failure_threshold=2,
            recovery_threshold=1
        )
    
    def _register_recovery_actions(self):
        """Register recovery actions for automatic healing."""
        # Source system recovery
        self.orchestrator.register_recovery_action(
            resource_type=ResourceType.SOURCE_SYSTEM,
            resource_id="default",
            recovery_function=self._recover_source_system,
            cooldown_seconds=300  # 5 minutes between recovery attempts
        )
        
        # Target system recovery
        self.orchestrator.register_recovery_action(
            resource_type=ResourceType.TARGET_SYSTEM,
            resource_id="default",
            recovery_function=self._recover_target_system,
            cooldown_seconds=300
        )
        
        # Database recovery
        self.orchestrator.register_recovery_action(
            resource_type=ResourceType.DATABASE,
            resource_id="main",
            recovery_function=self._recover_database,
            cooldown_seconds=180
        )
    
    def _check_source_system_health(self) -> bool:
        """
        Check if the source system is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        # In a real implementation, this would check connectivity to the source system
        try:
            # Placeholder for actual health check
            # e.g. make a lightweight API call to the source system
            return True
        except Exception as e:
            logger.error(f"Source system health check failed: {str(e)}")
            return False
    
    def _check_target_system_health(self) -> bool:
        """
        Check if the target system is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        # In a real implementation, this would check connectivity to the target system
        try:
            # Placeholder for actual health check
            # e.g. make a lightweight API call to the target system
            return True
        except Exception as e:
            logger.error(f"Target system health check failed: {str(e)}")
            return False
    
    def _check_database_health(self) -> bool:
        """
        Check if the database is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        # In a real implementation, this would check database connectivity
        try:
            # Placeholder for actual health check
            # e.g. execute a simple query to verify database connection
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def _recover_source_system(
        self,
        resource_type: ResourceType,
        resource_id: str,
        status: HealthStatus
    ) -> bool:
        """
        Attempt to recover the source system.
        
        Args:
            resource_type: Type of resource being recovered
            resource_id: Identifier for the specific resource
            status: Current health status
            
        Returns:
            True if recovery was successful, False otherwise
        """
        logger.info(f"Attempting to recover source system (status: {status.value})")
        
        try:
            # Placeholder for actual recovery logic
            # e.g. reconnect to the source system, refresh credentials, etc.
            
            # Reset the circuit breaker if it's open
            if "source_system" in self.orchestrator.circuit_breakers:
                self.orchestrator.circuit_breakers["source_system"].reset()
            
            logger.info("Source system recovery successful")
            return True
        except Exception as e:
            logger.error(f"Source system recovery failed: {str(e)}")
            return False
    
    def _recover_target_system(
        self,
        resource_type: ResourceType,
        resource_id: str,
        status: HealthStatus
    ) -> bool:
        """
        Attempt to recover the target system.
        
        Args:
            resource_type: Type of resource being recovered
            resource_id: Identifier for the specific resource
            status: Current health status
            
        Returns:
            True if recovery was successful, False otherwise
        """
        logger.info(f"Attempting to recover target system (status: {status.value})")
        
        try:
            # Placeholder for actual recovery logic
            # e.g. reconnect to the target system, refresh credentials, etc.
            
            # Reset the circuit breaker if it's open
            if "target_system" in self.orchestrator.circuit_breakers:
                self.orchestrator.circuit_breakers["target_system"].reset()
            
            logger.info("Target system recovery successful")
            return True
        except Exception as e:
            logger.error(f"Target system recovery failed: {str(e)}")
            return False
    
    def _recover_database(
        self,
        resource_type: ResourceType,
        resource_id: str,
        status: HealthStatus
    ) -> bool:
        """
        Attempt to recover the database connection.
        
        Args:
            resource_type: Type of resource being recovered
            resource_id: Identifier for the specific resource
            status: Current health status
            
        Returns:
            True if recovery was successful, False otherwise
        """
        logger.info(f"Attempting to recover database (status: {status.value})")
        
        try:
            # Placeholder for actual recovery logic
            # e.g. reconnect to the database, restart connection pool, etc.
            
            logger.info("Database recovery successful")
            return True
        except Exception as e:
            logger.error(f"Database recovery failed: {str(e)}")
            return False
    
    def execute_sync_operation(self, operation_id: int) -> Dict[str, Any]:
        """
        Execute a sync operation with self-healing capabilities.
        
        Args:
            operation_id: ID of the sync operation to execute
            
        Returns:
            Dictionary with operation results
            
        Raises:
            ValueError: If the operation can't be found
            Exception: If the operation fails and can't be recovered
        """
        logger.info(f"Starting sync operation: {operation_id}")
        
        try:
            # Load operation details
            # This would normally query the database for the operation
            operation = self._load_operation(operation_id)
            if not operation:
                raise ValueError(f"Sync operation {operation_id} not found")
            
            # Update operation status
            operation["status"] = "running"
            operation["started_at"] = datetime.utcnow()
            self._update_operation(operation)
            
            # Execute the sync operation with self-healing
            try:
                # Extract data from source
                source_data = self.orchestrator.execute_with_resilience(
                    function=self._read_from_source,
                    circuit_name="source_system",
                    retry_name="source_read",
                    source_config=operation.get("source_config")
                )
                
                # Transform data
                transformed_data = self.orchestrator.execute_with_resilience(
                    function=self._transform_data,
                    circuit_name="transformation",
                    retry_name="transform",
                    data=source_data,
                    mappings=operation.get("mappings")
                )
                
                # Load data to target
                target_result = self.orchestrator.execute_with_resilience(
                    function=self._write_to_target,
                    circuit_name="target_system",
                    retry_name="target_write",
                    data=transformed_data,
                    target_config=operation.get("target_config")
                )
                
                # Update operation with success
                operation["status"] = "completed"
                operation["completed_at"] = datetime.utcnow()
                operation["processed_records"] = len(source_data) if source_data else 0
                operation["successful_records"] = target_result.get("success_count", 0)
                operation["failed_records"] = target_result.get("error_count", 0)
                operation["metrics"] = {
                    "duration_seconds": (operation["completed_at"] - operation["started_at"]).total_seconds(),
                    "extraction_time": target_result.get("extraction_time", 0),
                    "transform_time": target_result.get("transform_time", 0),
                    "load_time": target_result.get("load_time", 0)
                }
                
            except Exception as e:
                # Update operation with failure
                operation["status"] = "failed"
                operation["completed_at"] = datetime.utcnow()
                operation["error_message"] = str(e)
                
                # Check health and attempt recovery
                self.orchestrator.run_health_checks(force_run=True)
                
                # Re-raise the exception
                raise
                
            finally:
                # Save operation state regardless of success or failure
                self._update_operation(operation)
            
            logger.info(f"Sync operation {operation_id} completed successfully")
            return operation
            
        except CircuitOpenError as e:
            logger.error(f"Circuit breaker prevented sync operation {operation_id}: {str(e)}")
            raise
            
        except Exception as e:
            logger.error(f"Error in sync operation {operation_id}: {str(e)}")
            raise
    
    def _load_operation(self, operation_id: int) -> Optional[Dict[str, Any]]:
        """
        Load a sync operation from the database.
        
        Args:
            operation_id: ID of the sync operation to load
            
        Returns:
            Dictionary with operation details, or None if not found
        """
        # In a real implementation, this would query the database
        # Placeholder for demo purposes
        return {
            "id": operation_id,
            "sync_pair_id": 1,
            "operation_type": "full",
            "status": "pending",
            "source_config": {
                "system_type": "pacs",
                "endpoint": "https://source-api.example.com/data",
                "auth": {"type": "bearer", "token": "token123"}
            },
            "target_config": {
                "system_type": "cama", 
                "endpoint": "https://target-api.example.com/data",
                "auth": {"type": "basic", "username": "user", "password": "pass"}
            },
            "mappings": [
                {"source_field": "id", "target_field": "external_id", "transform": "string"},
                {"source_field": "name", "target_field": "full_name", "transform": "string"},
                {"source_field": "value", "target_field": "amount", "transform": "number"}
            ]
        }
    
    def _update_operation(self, operation: Dict[str, Any]) -> None:
        """
        Update a sync operation in the database.
        
        Args:
            operation: Dictionary with operation details to update
        """
        # In a real implementation, this would update the database
        # Just log for demo purposes
        logger.info(f"Updated sync operation {operation['id']} status: {operation['status']}")
    
    def _read_from_source(self, source_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Read data from a source system.
        
        Args:
            source_config: Configuration for the source system
            
        Returns:
            List of data records from the source
            
        Raises:
            Exception: If the source read fails
        """
        logger.info(f"Reading from source: {source_config.get('system_type')}")
        
        try:
            # In a real implementation, this would call the source system API
            # Placeholder for demo purposes
            time.sleep(0.5)  # Simulate API call
            
            # Return dummy data
            return [
                {"id": "1", "name": "John Doe", "value": "100.50"},
                {"id": "2", "name": "Jane Smith", "value": "250.75"},
                {"id": "3", "name": "Bob Johnson", "value": "75.25"}
            ]
            
        except Exception as e:
            logger.error(f"Error reading from source: {str(e)}")
            raise
    
    def _transform_data(
        self,
        data: List[Dict[str, Any]],
        mappings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Transform data according to the specified mappings.
        
        Args:
            data: Data from the source system
            mappings: Field mappings for transformation
            
        Returns:
            Transformed data
            
        Raises:
            Exception: If the transformation fails
        """
        logger.info(f"Transforming {len(data)} records")
        
        try:
            transformed = []
            
            for record in data:
                new_record = {}
                
                for mapping in mappings:
                    source_field = mapping["source_field"]
                    target_field = mapping["target_field"]
                    transform_type = mapping.get("transform", "string")
                    
                    if source_field in record:
                        value = record[source_field]
                        
                        # Apply transformation based on type
                        if transform_type == "number":
                            try:
                                value = float(value)
                            except ValueError:
                                value = 0.0
                        elif transform_type == "boolean":
                            value = value.lower() in ("true", "yes", "1")
                        # else keep as string
                        
                        new_record[target_field] = value
                
                transformed.append(new_record)
            
            return transformed
            
        except Exception as e:
            logger.error(f"Error transforming data: {str(e)}")
            raise
    
    def _write_to_target(
        self,
        data: List[Dict[str, Any]],
        target_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Write data to a target system.
        
        Args:
            data: Transformed data to write
            target_config: Configuration for the target system
            
        Returns:
            Result of the write operation
            
        Raises:
            Exception: If the target write fails
        """
        logger.info(f"Writing {len(data)} records to target: {target_config.get('system_type')}")
        
        try:
            # In a real implementation, this would call the target system API
            # Placeholder for demo purposes
            time.sleep(1.0)  # Simulate API call
            
            # Return result
            return {
                "success": True,
                "success_count": len(data),
                "error_count": 0,
                "extraction_time": 0.5,
                "transform_time": 0.2,
                "load_time": 1.0
            }
            
        except Exception as e:
            logger.error(f"Error writing to target: {str(e)}")
            raise
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of the sync engine and its components.
        
        Returns:
            Dictionary with health status information
        """
        return self.orchestrator.get_health_status()
    
    def seed_demo_data(self) -> List[Dict[str, Any]]:
        """
        Seed demo sync pairs for testing.
        
        Returns:
            List of created sync pairs
        """
        # In a real implementation, this would create entries in the database
        
        pairs = [
            {
                "id": 1,
                "name": "PACS to CAMA Sync",
                "description": "Synchronize image data from PACS to CAMA system",
                "source_system": {
                    "type": "pacs",
                    "name": "County PACS System",
                    "endpoint": "https://pacs.example.gov/api"
                },
                "target_system": {
                    "type": "cama",
                    "name": "County CAMA System",
                    "endpoint": "https://cama.example.gov/api"
                },
                "mappings": [
                    {"source_field": "image_id", "target_field": "external_id"},
                    {"source_field": "image_timestamp", "target_field": "captured_date"},
                    {"source_field": "property_id", "target_field": "parcel_id"}
                ]
            },
            {
                "id": 2,
                "name": "GIS to CAMA Sync",
                "description": "Synchronize GIS data to CAMA system",
                "source_system": {
                    "type": "gis",
                    "name": "County GIS System",
                    "endpoint": "https://gis.example.gov/api"
                },
                "target_system": {
                    "type": "cama",
                    "name": "County CAMA System",
                    "endpoint": "https://cama.example.gov/api"
                },
                "mappings": [
                    {"source_field": "parcel_id", "target_field": "parcel_id"},
                    {"source_field": "location", "target_field": "geo_location"},
                    {"source_field": "zone_code", "target_field": "zoning"}
                ]
            }
        ]
        
        return pairs