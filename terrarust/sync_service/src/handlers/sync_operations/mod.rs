use actix_web::{web, HttpResponse, Responder, http::StatusCode};
use common::error::{Error, Result};
use common::models::sync_operation::{SyncOperation, NewSyncOperation, SyncOperationUpdate};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::database::sync_operations::{
    create_sync_operation, 
    get_sync_operation_by_id, 
    get_sync_operations_with_filters, 
    update_sync_operation_status
};

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncOperationResponse {
    pub operation: SyncOperation,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncOperationsResponse {
    pub operations: Vec<SyncOperation>,
    pub total_count: i64,
}

#[derive(Debug, Deserialize)]
pub struct SyncOperationQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
    pub sync_pair_id: Option<Uuid>,
    pub status: Option<String>,
    pub created_by: Option<String>,
    pub from_date: Option<String>,
    pub to_date: Option<String>,
}

pub async fn get_sync_operations(
    query: web::Query<SyncOperationQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    
    match get_sync_operations_with_filters(
        &state.database,
        page,
        per_page,
        query.sync_pair_id,
        query.status.as_deref(),
        query.created_by.as_deref(),
        query.from_date.as_deref(),
        query.to_date.as_deref(),
    ).await {
        Ok((operations, total_count)) => {
            HttpResponse::Ok().json(SyncOperationsResponse {
                operations,
                total_count,
            })
        },
        Err(e) => {
            log::error!("Failed to get sync operations: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to get sync operations: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn create_sync_operation(
    new_operation: web::Json<NewSyncOperation>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Track metrics
    state.telemetry.sync_operations_total.inc();
    state.telemetry.sync_operations_in_progress.inc();
    
    // Create the operation record
    match create_sync_operation(&state.database, new_operation.into_inner()).await {
        Ok(operation) => {
            log::info!("Created sync operation: {}", operation.id);
            
            // Trigger the sync process in the background
            let operation_id = operation.id;
            let sync_engine = state.sync_engine.clone();
            let telemetry = state.telemetry.clone();
            
            // Spawn a task to run the operation
            tokio::spawn(async move {
                if let Err(e) = sync_engine.run_sync_operation(operation_id).await {
                    log::error!("Failed to execute sync operation {}: {}", operation_id, e);
                    telemetry.sync_operations_failed.inc();
                }
                
                // Decrement in-progress counter regardless of outcome
                telemetry.sync_operations_in_progress.dec();
            });
            
            HttpResponse::Created().json(SyncOperationResponse {
                operation,
            })
        },
        Err(e) => {
            // Decrement in-progress counter on error
            state.telemetry.sync_operations_in_progress.dec();
            state.telemetry.sync_operations_failed.inc();
            
            log::error!("Failed to create sync operation: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to create sync operation: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn get_sync_operation(
    id: web::Path<i32>,
    state: web::Data<AppState>,
) -> impl Responder {
    match get_sync_operation_by_id(&state.database, *id).await {
        Ok(operation) => {
            HttpResponse::Ok().json(SyncOperationResponse {
                operation,
            })
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync operation not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to get sync operation: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to get sync operation: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn cancel_sync_operation(
    id: web::Path<i32>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Update operation status to cancelled
    let update = SyncOperationUpdate {
        status: Some("cancelled".to_string()),
        updated_at: Some(chrono::Utc::now()),
        ..Default::default()
    };
    
    match update_sync_operation_status(&state.database, *id, update).await {
        Ok(operation) => {
            // If operation was in progress, decrement the counter
            if operation.status == "in_progress" {
                state.telemetry.sync_operations_in_progress.dec();
            }
            
            log::info!("Cancelled sync operation: {}", id);
            
            // Signal the sync engine to cancel the operation
            let _ = state.sync_engine.cancel_operation(*id).await;
            
            HttpResponse::Ok().json(SyncOperationResponse {
                operation,
            })
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync operation not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to cancel sync operation: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to cancel sync operation: {}", e),
                    "status": 500
                })
            ))
        }
    }
}