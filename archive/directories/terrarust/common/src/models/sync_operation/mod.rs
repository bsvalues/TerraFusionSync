use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Status of a sync operation
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum SyncStatus {
    Pending,
    Running,
    Completed,
    Failed,
    Canceled,
}

/// Type of change in a sync diff
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum ChangeType {
    Added,
    Modified,
    Deleted,
    Unchanged,
}

/// A sync pair configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncPair {
    pub id: Uuid,
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub source_config: serde_json::Value,
    pub target_system: String,
    pub target_config: serde_json::Value,
    pub county_id: String,
    pub sync_interval_minutes: Option<i32>,
    pub last_sync_time: Option<DateTime<Utc>>,
    pub is_active: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: String,
    pub sync_conflict_strategy: Option<String>,
    pub metadata: Option<serde_json::Value>,
}

/// A sync operation record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncOperation {
    pub id: Uuid,
    pub sync_pair_id: Uuid,
    pub status: SyncStatus,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub total_records: Option<i32>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub error_message: Option<String>,
    pub initiated_by: String,
    pub county_id: String,
    pub execution_logs: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// A sync diff record representing a change between source and target
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncDiff {
    pub id: Uuid,
    pub sync_operation_id: Uuid,
    pub entity_id: String,
    pub entity_type: String,
    pub change_type: ChangeType,
    pub source_data: Option<serde_json::Value>,
    pub target_data: Option<serde_json::Value>,
    pub diff_details: Option<serde_json::Value>,
    pub sync_status: String,
    pub error_message: Option<String>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

/// A validation issue found during sync
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ValidationIssue {
    pub id: Uuid,
    pub sync_operation_id: Uuid,
    pub entity_id: String,
    pub entity_type: String,
    pub field_name: Option<String>,
    pub issue_type: String,
    pub severity: String,
    pub description: String,
    pub source_value: Option<serde_json::Value>,
    pub target_value: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
}

/// Statistics for a completed sync operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncStats {
    pub sync_operation_id: Uuid,
    pub total_records: i32,
    pub added_count: i32,
    pub modified_count: i32,
    pub deleted_count: i32,
    pub unchanged_count: i32,
    pub error_count: i32,
    pub validation_issues_count: i32,
    pub duration_seconds: f64,
    pub avg_record_processing_ms: f64,
    pub created_at: DateTime<Utc>,
}

/// Parameters for creating a new sync operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateSyncOperationParams {
    pub sync_pair_id: Uuid,
    pub initiated_by: String,
    pub custom_parameters: Option<serde_json::Value>,
}

/// Parameters for updating a sync operation
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateSyncOperationParams {
    pub status: Option<SyncStatus>,
    pub end_time: Option<DateTime<Utc>>,
    pub total_records: Option<i32>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub error_message: Option<String>,
    pub execution_logs: Option<serde_json::Value>,
}

/// Parameters for creating a new sync pair
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateSyncPairParams {
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub source_config: serde_json::Value,
    pub target_system: String,
    pub target_config: serde_json::Value,
    pub county_id: String,
    pub sync_interval_minutes: Option<i32>,
    pub is_active: bool,
    pub created_by: String,
    pub sync_conflict_strategy: Option<String>,
    pub metadata: Option<serde_json::Value>,
}