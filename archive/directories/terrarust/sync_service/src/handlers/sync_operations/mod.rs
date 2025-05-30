use actix_web::{web, HttpResponse, Responder};
use common::error::{Error, Result};
use common::models::sync_operation::{SyncOperation, CreateSyncOperationParams};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;

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
    pub county_id: Option<String>,
    pub status: Option<String>,
    pub initiated_by: Option<String>,
    pub from_date: Option<String>,
    pub to_date: Option<String>,
}

pub async fn get_all_operations(
    query: web::Query<SyncOperationQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::Ok().json(SyncOperationsResponse {
        operations: Vec::new(),
        total_count: 0,
    })
}

pub async fn start_operation(
    req: web::Json<CreateSyncOperationParams>,
    state: web::Data<AppState>,
) -> impl Responder {
    match state.sync_engine.start_sync_operation(req.0).await {
        Ok(operation) => {
            HttpResponse::Created().json(SyncOperationResponse {
                operation,
            })
        },
        Err(e) => {
            log::error!("Failed to start sync operation: {}", e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to start sync operation: {}", e),
                    "status": 400
                })
            ))
        }
    }
}

pub async fn get_operation(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": format!("Sync operation not found: {}", id),
            "status": 404
        })
    ))
}

pub async fn cancel_operation(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    match state.sync_engine.cancel_sync_operation(*id).await {
        Ok(operation) => {
            HttpResponse::Ok().json(SyncOperationResponse {
                operation,
            })
        },
        Err(e) => {
            log::error!("Failed to cancel sync operation {}: {}", id, e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to cancel sync operation: {}", e),
                    "status": 400
                })
            ))
        }
    }
}