"""
Base models for the SyncService.

This module defines the base models and data structures used throughout the SyncService.
"""

from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, TypeVar, Generic, Union
from pydantic import BaseModel, Field, validator


class SyncType(str, Enum):
    """Type of synchronization operation."""
    FULL = "full"
    INCREMENTAL = "incremental"


class SyncStatus(str, Enum):
    """Status of a synchronization operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class EntityType(str, Enum):
    """Type of entity being synchronized."""
    PROPERTY = "property"
    OWNER = "owner"
    ASSESSMENT = "assessment"
    BUILDING = "building"
    LAND = "land"
    PARCEL = "parcel"
    STRUCTURE = "structure"
    ZONE = "zone"
    TRANSACTION = "transaction"
    PAYMENT = "payment"
    ACCOUNT = "account"


class SystemType(str, Enum):
    """Type of system (source or target)."""
    PACS = "pacs"
    CAMA = "cama"
    GIS = "gis"
    ERP = "erp"


class ValidationResult(BaseModel):
    """Result of a validation operation."""
    is_valid: bool
    entity_type: str
    entity_id: str
    errors: List[str] = []
    warnings: List[str] = []


class EntityStats(BaseModel):
    """Statistics for a specific entity type in a sync operation."""
    entity_type: str
    processed: int = 0
    succeeded: int = 0
    failed: int = 0


class SyncOperationDetails(BaseModel):
    """Details of a synchronization operation."""
    records_processed: int = 0
    records_succeeded: int = 0
    records_failed: int = 0
    entities: Dict[str, Dict[str, int]] = {}


class SyncOperation(BaseModel):
    """Model representing a synchronization operation."""
    id: str
    sync_type: SyncType
    sync_pair_id: str
    entity_types: List[str] = []
    status: SyncStatus = SyncStatus.PENDING
    start_time: datetime
    end_time: Optional[datetime] = None
    details: Optional[SyncOperationDetails] = None
    error: Optional[str] = None
    
    @validator('end_time')
    def check_end_time(cls, v, values):
        """Validate that end_time is after start_time."""
        if v and 'start_time' in values and v < values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v


class SourceRecord(BaseModel):
    """Base model for records from source systems."""
    source_id: str
    entity_type: str
    data: Dict[str, Any]
    last_modified: datetime


class TargetRecord(BaseModel):
    """Base model for records in target systems."""
    target_id: str
    entity_type: str
    data: Dict[str, Any]
    source_id: Optional[str] = None
    last_synced: Optional[datetime] = None


class TransformedRecord(BaseModel):
    """Model representing a record after transformation."""
    source_id: str
    target_id: Optional[str] = None
    entity_type: str
    source_data: Dict[str, Any]
    target_data: Dict[str, Any]
    transformation_notes: List[str] = []


class ConflictResolution(str, Enum):
    """Strategy for resolving conflicts between source and target records."""
    SOURCE_WINS = "source_wins"
    TARGET_WINS = "target_wins"
    MANUAL = "manual"
    MERGE = "merge"


class Conflict(BaseModel):
    """Model representing a conflict between source and target records."""
    source_id: str
    target_id: str
    entity_type: str
    field: str
    source_value: Any
    target_value: Any
    resolution: Optional[ConflictResolution] = None
    resolved_value: Optional[Any] = None


class ConfigChangedEvent(BaseModel):
    """Event emitted when configuration changes."""
    config_type: str
    item_id: str
    action: str  # created, updated, deleted
    timestamp: datetime = Field(default_factory=datetime.utcnow)


T = TypeVar('T')


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model."""
    items: List[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Calculate the total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size


class HealthStatus(str, Enum):
    """Health status of a service or component."""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    status: HealthStatus
    latency: Optional[str] = None
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    status: HealthStatus
    service: str
    version: str
    dependencies: Dict[str, Union[str, DependencyHealth]] = {}
    performance: Dict[str, str] = {}