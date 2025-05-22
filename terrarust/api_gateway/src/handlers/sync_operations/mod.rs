use actix_web::{web, HttpResponse, Responder, http::header};
use common::error::{Error, Result};
use common::models::sync_operation::{SyncOperation, CreateSyncOperationParams};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::middleware::auth::Claims;

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
    pub from_date: Option<String>,
    pub to_date: Option<String>,
}

/// Get all sync operations with optional filtering
pub async fn get_all_operations(
    query: web::Query<SyncOperationQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Get query parameters
    let sync_pair_id = query.sync_pair_id;
    let county_id = query.county_id.as_deref();
    let status = query.status.as_deref();
    let page = query.page;
    let per_page = query.per_page;
    
    // Call the service
    match state.services.sync_service.get_operations(
        sync_pair_id,
        county_id,
        status,
        page,
        per_page,
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

/// Start a new sync operation
pub async fn start_operation(
    req: web::Json<CreateSyncOperationParams>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Create parameters with username from claims
    let params = CreateSyncOperationParams {
        sync_pair_id: req.sync_pair_id,
        initiated_by: claims.sub.clone(),
        custom_parameters: req.custom_parameters.clone(),
    };
    
    // Call the service
    match state.services.sync_service.start_operation(params).await {
        Ok(operation) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "Sync operation {} started by user {} for sync pair {}",
                operation.id,
                claims.sub,
                operation.sync_pair_id
            );
            
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

/// Get a specific sync operation by ID
pub async fn get_operation(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.sync_service.get_operation(*id).await {
        Ok(operation) => {
            HttpResponse::Ok().json(SyncOperationResponse {
                operation,
            })
        },
        Err(e) => {
            log::error!("Failed to get sync operation {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get sync operation: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Cancel a sync operation
pub async fn cancel_operation(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Call the service
    match state.services.sync_service.cancel_operation(*id).await {
        Ok(operation) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "Sync operation {} canceled by user {}",
                operation.id,
                claims.sub
            );
            
            HttpResponse::Ok().json(SyncOperationResponse {
                operation,
            })
        },
        Err(e) => {
            log::error!("Failed to cancel sync operation {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to cancel sync operation: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Get sync diffs for a specific operation
pub async fn get_operation_diffs(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service to get diffs
    match state.services.sync_service.get_diffs(
        *id,
        None,
        None,
        None,
        None,
        None,
        None,
    ).await {
        Ok((diffs, total_count)) => {
            HttpResponse::Ok().json(web::Json(
                serde_json::json!({
                    "diffs": diffs,
                    "total_count": total_count
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to get sync diffs for operation {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get sync diffs: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}