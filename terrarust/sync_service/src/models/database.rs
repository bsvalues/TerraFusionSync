use sqlx::{FromRow, Type};
use serde::{Serialize, Deserialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Database model for sync pairs
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct SyncPairRow {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub name: String,
    pub description: Option<String>,
    pub source_system: String,
    pub source_config: serde_json::Value,
    pub target_system: String,
    pub target_config: serde_json::Value,
    pub county_id: String,
    pub is_active: bool,
    pub sync_interval_minutes: i32,
    pub sync_conflict_strategy: String,
    pub last_sync_time: Option<DateTime<Utc>>,
    pub last_sync_status: Option<String>,
    pub created_by: String,
    pub updated_by: String,
}

/// Database model for sync operations
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct SyncOperationRow {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub sync_pair_id: Uuid,
    pub status: String,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub records_processed: Option<i32>,
    pub records_succeeded: Option<i32>,
    pub records_failed: Option<i32>,
    pub error_message: Option<String>,
    pub custom_parameters: Option<serde_json::Value>,
    pub initiated_by: String,
}

/// Database model for sync records
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct SyncRecordRow {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub sync_operation_id: Uuid,
    pub source_id: String,
    pub target_id: Option<String>,
    pub record_type: String,
    pub status: String,
    pub source_data: serde_json::Value,
    pub target_data: Option<serde_json::Value>,
    pub error_message: Option<String>,
    pub conflict: Option<bool>,
    pub resolution: Option<String>,
}

/// Database model for sync diffs
#[derive(Debug, Clone, FromRow, Serialize, Deserialize)]
pub struct SyncDiffRow {
    pub id: Uuid,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub sync_record_id: Uuid,
    pub field_path: String,
    pub source_value: Option<serde_json::Value>,
    pub target_value: Option<serde_json::Value>,
    pub is_conflict: bool,
    pub resolved: bool,
    pub resolution: Option<String>,
    pub resolved_by: Option<String>,
    pub resolved_at: Option<DateTime<Utc>>,
}

/// Database queries for sync operations
pub struct SyncOperationQueries;

impl SyncOperationQueries {
    /// Create a new sync operation
    pub async fn create(
        pool: &sqlx::PgPool,
        operation: &SyncOperationRow,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            INSERT INTO sync_operations (
                id, created_at, updated_at, sync_pair_id, status, start_time,
                end_time, records_processed, records_succeeded, records_failed,
                error_message, custom_parameters, initiated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            "#,
            operation.id,
            operation.created_at,
            operation.updated_at,
            operation.sync_pair_id,
            operation.status,
            operation.start_time,
            operation.end_time,
            operation.records_processed,
            operation.records_succeeded,
            operation.records_failed,
            operation.error_message,
            operation.custom_parameters,
            operation.initiated_by
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Update sync operation status
    pub async fn update_status(
        pool: &sqlx::PgPool,
        operation_id: Uuid,
        status: &str,
        end_time: Option<DateTime<Utc>>,
        error_message: Option<&str>,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE sync_operations 
            SET status = $2, end_time = $3, error_message = $4, updated_at = NOW()
            WHERE id = $1
            "#,
            operation_id,
            status,
            end_time,
            error_message
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Update sync operation progress
    pub async fn update_progress(
        pool: &sqlx::PgPool,
        operation_id: Uuid,
        records_processed: i32,
        records_succeeded: i32,
        records_failed: i32,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE sync_operations 
            SET records_processed = $2, records_succeeded = $3, records_failed = $4, updated_at = NOW()
            WHERE id = $1
            "#,
            operation_id,
            records_processed,
            records_succeeded,
            records_failed
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Get sync operation by ID
    pub async fn get_by_id(
        pool: &sqlx::PgPool,
        operation_id: Uuid,
    ) -> Result<Option<SyncOperationRow>, sqlx::Error> {
        let operation = sqlx::query_as!(
            SyncOperationRow,
            "SELECT * FROM sync_operations WHERE id = $1",
            operation_id
        )
        .fetch_optional(pool)
        .await?;
        
        Ok(operation)
    }
    
    /// List sync operations with pagination and filtering
    pub async fn list(
        pool: &sqlx::PgPool,
        sync_pair_id: Option<Uuid>,
        status: Option<&str>,
        offset: i64,
        limit: i64,
    ) -> Result<Vec<SyncOperationRow>, sqlx::Error> {
        let operations = sqlx::query_as!(
            SyncOperationRow,
            r#"
            SELECT * FROM sync_operations 
            WHERE ($1::uuid IS NULL OR sync_pair_id = $1)
            AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            "#,
            sync_pair_id,
            status,
            limit,
            offset
        )
        .fetch_all(pool)
        .await?;
        
        Ok(operations)
    }
}

/// Database queries for sync pairs
pub struct SyncPairQueries;

impl SyncPairQueries {
    /// Create a new sync pair
    pub async fn create(
        pool: &sqlx::PgPool,
        sync_pair: &SyncPairRow,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            INSERT INTO sync_pairs (
                id, created_at, updated_at, name, description, source_system,
                source_config, target_system, target_config, county_id, is_active,
                sync_interval_minutes, sync_conflict_strategy, last_sync_time,
                last_sync_status, created_by, updated_by
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
            "#,
            sync_pair.id,
            sync_pair.created_at,
            sync_pair.updated_at,
            sync_pair.name,
            sync_pair.description,
            sync_pair.source_system,
            sync_pair.source_config,
            sync_pair.target_system,
            sync_pair.target_config,
            sync_pair.county_id,
            sync_pair.is_active,
            sync_pair.sync_interval_minutes,
            sync_pair.sync_conflict_strategy,
            sync_pair.last_sync_time,
            sync_pair.last_sync_status,
            sync_pair.created_by,
            sync_pair.updated_by
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
    
    /// Get sync pair by ID
    pub async fn get_by_id(
        pool: &sqlx::PgPool,
        sync_pair_id: Uuid,
    ) -> Result<Option<SyncPairRow>, sqlx::Error> {
        let sync_pair = sqlx::query_as!(
            SyncPairRow,
            "SELECT * FROM sync_pairs WHERE id = $1",
            sync_pair_id
        )
        .fetch_optional(pool)
        .await?;
        
        Ok(sync_pair)
    }
    
    /// List active sync pairs due for sync
    pub async fn get_due_for_sync(
        pool: &sqlx::PgPool,
    ) -> Result<Vec<SyncPairRow>, sqlx::Error> {
        let sync_pairs = sqlx::query_as!(
            SyncPairRow,
            r#"
            SELECT * FROM sync_pairs 
            WHERE is_active = true 
            AND (
                last_sync_time IS NULL 
                OR last_sync_time + INTERVAL '1 minute' * sync_interval_minutes <= NOW()
            )
            ORDER BY last_sync_time ASC NULLS FIRST
            "#
        )
        .fetch_all(pool)
        .await?;
        
        Ok(sync_pairs)
    }
    
    /// Update last sync time for a sync pair
    pub async fn update_last_sync(
        pool: &sqlx::PgPool,
        sync_pair_id: Uuid,
        last_sync_time: DateTime<Utc>,
        status: &str,
    ) -> Result<(), sqlx::Error> {
        sqlx::query!(
            r#"
            UPDATE sync_pairs 
            SET last_sync_time = $2, last_sync_status = $3, updated_at = NOW()
            WHERE id = $1
            "#,
            sync_pair_id,
            last_sync_time,
            status
        )
        .execute(pool)
        .await?;
        
        Ok(())
    }
}