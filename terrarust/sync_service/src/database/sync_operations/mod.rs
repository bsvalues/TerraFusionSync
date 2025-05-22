use common::error::{Error, Result};
use common::models::sync_operation::{SyncOperation, NewSyncOperation, SyncOperationUpdate};
use common::database::Database;
use common::schema::sync_operations;
use diesel::prelude::*;
use diesel::pg::PgConnection;
use uuid::Uuid;
use chrono::Utc;

/// Get all sync operations with optional filtering
pub async fn get_sync_operations_with_filters(
    database: &Database,
    page: i64,
    per_page: i64,
    sync_pair_id: Option<Uuid>,
    status: Option<&str>,
    created_by: Option<&str>,
    from_date: Option<&str>,
    to_date: Option<&str>,
) -> Result<(Vec<SyncOperation>, i64)> {
    use common::schema::sync_operations::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Calculate offset
    let offset = (page - 1) * per_page;
    
    // Build query
    let mut query = sync_operations::table.into_boxed();
    
    // Apply filters
    if let Some(sp_id) = sync_pair_id {
        query = query.filter(sync_pair_id.eq(sp_id));
    }
    
    if let Some(s) = status {
        query = query.filter(status.eq(s));
    }
    
    if let Some(cb) = created_by {
        query = query.filter(created_by.eq(cb));
    }
    
    if let Some(fd) = from_date {
        // Parse date
        if let Ok(from_date_parsed) = fd.parse::<chrono::DateTime<Utc>>() {
            query = query.filter(created_at.ge(from_date_parsed));
        }
    }
    
    if let Some(td) = to_date {
        // Parse date
        if let Ok(to_date_parsed) = td.parse::<chrono::DateTime<Utc>>() {
            query = query.filter(created_at.le(to_date_parsed));
        }
    }
    
    // Execute count query
    let total_count: i64 = query.count().get_result(&conn)?;
    
    // Execute main query with pagination
    let operations: Vec<SyncOperation> = query
        .order(created_at.desc())
        .limit(per_page)
        .offset(offset)
        .load(&conn)?;
    
    Ok((operations, total_count))
}

/// Get a specific sync operation by ID
pub async fn get_sync_operation_by_id(database: &Database, operation_id: i32) -> Result<SyncOperation> {
    use common::schema::sync_operations::dsl::*;
    
    let conn = database.get_connection()?;
    
    let operation = sync_operations
        .filter(id.eq(operation_id))
        .first(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync operation not found: {}", operation_id)))?;
    
    Ok(operation)
}

/// Create a new sync operation
pub async fn create_sync_operation(database: &Database, new_operation: NewSyncOperation) -> Result<SyncOperation> {
    use common::schema::sync_operations::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Verify the sync pair exists
    use common::schema::sync_pairs::dsl as pairs_dsl;
    let pair_exists = diesel::select(diesel::dsl::exists(
        pairs_dsl::sync_pairs.filter(pairs_dsl::id.eq(new_operation.sync_pair_id))
    )).get_result::<bool>(&conn)?;
    
    if !pair_exists {
        return Err(Error::NotFound(format!("Sync pair not found: {}", new_operation.sync_pair_id)));
    }
    
    let now = Utc::now();
    
    let operation = diesel::insert_into(sync_operations)
        .values((
            sync_pair_id.eq(new_operation.sync_pair_id),
            status.eq(&new_operation.status),
            created_at.eq(now),
            updated_at.eq(now),
            created_by.eq(&new_operation.created_by),
            correlation_id.eq(&new_operation.correlation_id),
        ))
        .get_result(&conn)?;
    
    Ok(operation)
}

/// Update a sync operation's status and details
pub async fn update_sync_operation_status(
    database: &Database,
    operation_id: i32,
    update: SyncOperationUpdate,
) -> Result<SyncOperation> {
    use common::schema::sync_operations::dsl::*;
    
    let conn = database.get_connection()?;
    
    // Check if operation exists
    let existing_operation = sync_operations
        .filter(id.eq(operation_id))
        .first::<SyncOperation>(&conn)
        .optional()?
        .ok_or_else(|| Error::NotFound(format!("Sync operation not found: {}", operation_id)))?;
    
    // Build update query
    let mut update_query = diesel::update(sync_operations.filter(id.eq(operation_id)));
    
    // Add fields to update
    let now = update.updated_at.unwrap_or_else(Utc::now);
    let mut updates = vec![(updated_at.eq(now))];
    
    if let Some(s) = update.status {
        updates.push(status.eq(s));
    }
    
    if let Some(sa) = update.started_at {
        updates.push(started_at.eq(sa));
    }
    
    if let Some(ca) = update.completed_at {
        updates.push(completed_at.eq(ca));
    }
    
    if let Some(em) = update.error_message {
        updates.push(error_message.eq(em));
    }
    
    if let Some(rp) = update.records_processed {
        updates.push(records_processed.eq(rp));
    }
    
    if let Some(rs) = update.records_succeeded {
        updates.push(records_succeeded.eq(rs));
    }
    
    if let Some(rf) = update.records_failed {
        updates.push(records_failed.eq(rf));
    }
    
    if let Some(ed) = update.execution_details {
        updates.push(execution_details.eq(ed));
    }
    
    // Execute update
    let updated_operation = update_query
        .set(updates)
        .get_result(&conn)?;
    
    Ok(updated_operation)
}

/// Start a sync operation (update status to in_progress)
pub async fn start_sync_operation(database: &Database, operation_id: i32) -> Result<SyncOperation> {
    let update = SyncOperationUpdate {
        status: Some("in_progress".to_string()),
        started_at: Some(Utc::now()),
        updated_at: Some(Utc::now()),
        ..Default::default()
    };
    
    update_sync_operation_status(database, operation_id, update).await
}

/// Complete a sync operation (update status to completed)
pub async fn complete_sync_operation(
    database: &Database,
    operation_id: i32,
    records_processed: i32,
    records_succeeded: i32,
    records_failed: i32,
    execution_details: Option<serde_json::Value>,
) -> Result<SyncOperation> {
    let update = SyncOperationUpdate {
        status: Some("completed".to_string()),
        completed_at: Some(Utc::now()),
        records_processed: Some(records_processed),
        records_succeeded: Some(records_succeeded),
        records_failed: Some(records_failed),
        execution_details,
        updated_at: Some(Utc::now()),
        ..Default::default()
    };
    
    update_sync_operation_status(database, operation_id, update).await
}

/// Fail a sync operation (update status to failed)
pub async fn fail_sync_operation(
    database: &Database,
    operation_id: i32,
    error_message: String,
    records_processed: Option<i32>,
    records_succeeded: Option<i32>,
    records_failed: Option<i32>,
    execution_details: Option<serde_json::Value>,
) -> Result<SyncOperation> {
    let update = SyncOperationUpdate {
        status: Some("failed".to_string()),
        completed_at: Some(Utc::now()),
        error_message: Some(error_message),
        records_processed,
        records_succeeded,
        records_failed,
        execution_details,
        updated_at: Some(Utc::now()),
        ..Default::default()
    };
    
    update_sync_operation_status(database, operation_id, update).await
}