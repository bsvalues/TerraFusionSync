use chrono::{DateTime, Utc};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize, Queryable, Identifiable)]
#[diesel(table_name = crate::schema::sync_operations)]
pub struct SyncOperation {
    pub id: i32,
    pub sync_pair_id: Uuid,
    pub status: String, // pending, in_progress, completed, failed, cancelled
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub execution_details: Option<serde_json::Value>,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub created_by: Option<String>,
    pub correlation_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Insertable)]
#[diesel(table_name = crate::schema::sync_operations)]
pub struct NewSyncOperation {
    pub sync_pair_id: Uuid,
    pub status: String,
    pub created_by: Option<String>,
    pub correlation_id: Option<String>,
}

impl NewSyncOperation {
    pub fn new(sync_pair_id: Uuid, created_by: Option<String>) -> Self {
        Self {
            sync_pair_id,
            status: "pending".to_string(),
            created_by,
            correlation_id: Some(Uuid::new_v4().to_string()),
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, AsChangeset)]
#[diesel(table_name = crate::schema::sync_operations)]
pub struct SyncOperationUpdate {
    pub status: Option<String>,
    pub started_at: Option<DateTime<Utc>>,
    pub completed_at: Option<DateTime<Utc>>,
    pub error_message: Option<String>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub execution_details: Option<serde_json::Value>,
    pub updated_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncOperationResult {
    pub operation_id: i32,
    pub status: String,
    pub records_processed: i32,
    pub records_succeeded: i32,
    pub records_failed: i32,
    pub errors: Vec<SyncError>,
    pub warnings: Vec<String>,
    pub duration_seconds: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncError {
    pub record_id: Option<String>,
    pub error_type: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}