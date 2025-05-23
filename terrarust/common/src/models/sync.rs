use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;
use super::BaseModel;

/// Sync pair represents a configured sync between two systems
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncPair {
    #[serde(flatten)]
    pub base: BaseModel,
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub source_config: serde_json::Value,
    pub target_system: String,
    pub target_config: serde_json::Value,
    pub county_id: String,
    pub is_active: bool,
    pub sync_interval_minutes: i32,
    pub sync_conflict_strategy: SyncConflictStrategy,
    pub last_sync_time: Option<DateTime<Utc>>,
    pub last_sync_status: Option<SyncStatus>,
    pub created_by: String,
    pub updated_by: String,
}

/// Sync operation represents a single execution of a sync
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncOperation {
    #[serde(flatten)]
    pub base: BaseModel,
    pub sync_pair_id: Uuid,
    pub status: SyncStatus,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub error_message: Option<String>,
    pub custom_parameters: Option<serde_json::Value>,
    pub initiated_by: String,
}

/// Sync record represents a single record processed during a sync
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncRecord {
    #[serde(flatten)]
    pub base: BaseModel,
    pub sync_operation_id: Uuid,
    pub source_id: String,
    pub target_id: Option<String>,
    pub record_type: String,
    pub status: SyncRecordStatus,
    pub source_data: serde_json::Value,
    pub target_data: Option<serde_json::Value>,
    pub error_message: Option<String>,
    pub conflict: Option<bool>,
    pub resolution: Option<SyncConflictResolution>,
}

/// Sync diff represents a difference between source and target
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncDiff {
    #[serde(flatten)]
    pub base: BaseModel,
    pub sync_record_id: Uuid,
    pub field_path: String,
    pub source_value: Option<serde_json::Value>,
    pub target_value: Option<serde_json::Value>,
    pub is_conflict: bool,
    pub resolved: bool,
    pub resolution: Option<SyncConflictResolution>,
    pub resolved_by: Option<String>,
    pub resolved_at: Option<DateTime<Utc>>,
}

/// Sync status enum
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum SyncStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Canceled,
}

impl Default for SyncStatus {
    fn default() -> Self {
        Self::Pending
    }
}

/// Sync record status enum
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum SyncRecordStatus {
    Pending,
    Processing,
    Success,
    Failed,
    Conflict,
}

impl Default for SyncRecordStatus {
    fn default() -> Self {
        Self::Pending
    }
}

/// Sync conflict strategy enum
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum SyncConflictStrategy {
    SourceWins,
    TargetWins,
    NewerWins,
    Manual,
}

impl Default for SyncConflictStrategy {
    fn default() -> Self {
        Self::Manual
    }
}

/// Sync conflict resolution enum
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "UPPERCASE")]
pub enum SyncConflictResolution {
    UseSource,
    UseTarget,
    UseCustom,
    Skip,
}

/// SyncPair creation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateSyncPairRequest {
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub source_config: serde_json::Value,
    pub target_system: String,
    pub target_config: serde_json::Value,
    pub county_id: String,
    pub is_active: bool,
    pub sync_interval_minutes: i32,
    pub sync_conflict_strategy: SyncConflictStrategy,
}

/// SyncPair update request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateSyncPairRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub source_system: Option<String>,
    pub source_config: Option<serde_json::Value>,
    pub target_system: Option<String>,
    pub target_config: Option<serde_json::Value>,
    pub is_active: Option<bool>,
    pub sync_interval_minutes: Option<i32>,
    pub sync_conflict_strategy: Option<SyncConflictStrategy>,
}

/// SyncOperation creation request
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateSyncOperationRequest {
    pub sync_pair_id: Uuid,
    pub custom_parameters: Option<serde_json::Value>,
}

/// Sync stats for dashboard
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncStats {
    pub total_operations: i64,
    pub successful_operations: i64,
    pub failed_operations: i64,
    pub total_sync_pairs: i64,
    pub active_sync_pairs: i64,
    pub total_records_processed: i64,
    pub total_records_succeeded: i64,
    pub total_records_failed: i64,
    pub total_conflicts: i64,
    pub resolved_conflicts: i64,
    pub unresolved_conflicts: i64,
}

/// Sync system configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncSystemConfig {
    pub system_type: String,
    pub name: String,
    pub description: String,
    pub schema: serde_json::Value,
    pub supported_operations: Vec<String>,
    pub default_config: serde_json::Value,
    pub is_enabled: bool,
}