use actix_web::{web, HttpResponse, Responder};
use common::error::{Error, Result};
use common::models::sync_operation::{SyncPair, CreateSyncPairParams};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::middleware::auth::Claims;

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncPairResponse {
    pub sync_pair: SyncPair,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncPairsResponse {
    pub sync_pairs: Vec<SyncPair>,
    pub total_count: i64,
}

#[derive(Debug, Deserialize)]
pub struct SyncPairQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
    pub county_id: Option<String>,
    pub source_system: Option<String>,
    pub target_system: Option<String>,
    pub is_active: Option<bool>,
}

#[derive(Debug, Deserialize)]
pub struct UpdateSyncPairRequest {
    pub name: Option<String>,
    pub description: Option<String>,
    pub source_config: Option<serde_json::Value>,
    pub target_config: Option<serde_json::Value>,
    pub sync_interval_minutes: Option<i32>,
    pub is_active: Option<bool>,
    pub sync_conflict_strategy: Option<String>,
    pub metadata: Option<serde_json::Value>,
}

#[derive(Debug, Deserialize)]
pub struct ToggleSyncPairRequest {
    pub is_active: bool,
}

/// Get all sync pairs with optional filtering
pub async fn get_all_pairs(
    query: web::Query<SyncPairQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Get query parameters
    let county_id = query.county_id.as_deref();
    let source_system = query.source_system.as_deref();
    let target_system = query.target_system.as_deref();
    let is_active = query.is_active;
    let page = query.page;
    let per_page = query.per_page;
    
    // Call the service
    match state.services.sync_service.get_sync_pairs(
        county_id,
        source_system,
        target_system,
        is_active,
        page,
        per_page,
    ).await {
        Ok((sync_pairs, total_count)) => {
            HttpResponse::Ok().json(SyncPairsResponse {
                sync_pairs,
                total_count,
            })
        },
        Err(e) => {
            log::error!("Failed to get sync pairs: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to get sync pairs: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

/// Create a new sync pair
pub async fn create_pair(
    req: web::Json<CreateSyncPairParams>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Create the request with username from claims
    let mut params = req.into_inner();
    params.created_by = claims.sub.clone();
    
    // Call the service
    match state.services.sync_service.create_sync_pair(params).await {
        Ok(sync_pair) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "Sync pair {} created by user {} for county {}",
                sync_pair.id,
                claims.sub,
                sync_pair.county_id
            );
            
            HttpResponse::Created().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(e) => {
            log::error!("Failed to create sync pair: {}", e);
            HttpResponse::BadRequest().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to create sync pair: {}", e),
                    "status": 400
                })
            ))
        }
    }
}

/// Get a specific sync pair by ID
pub async fn get_pair(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Call the service
    match state.services.sync_service.get_sync_pair(*id).await {
        Ok(sync_pair) => {
            HttpResponse::Ok().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(e) => {
            log::error!("Failed to get sync pair {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to get sync pair: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}

/// Update a sync pair
pub async fn update_pair(
    id: web::Path<Uuid>,
    req: web::Json<UpdateSyncPairRequest>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // For this demo, we'll return a not found response
    // In a real implementation, this would call the service
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": format!("Sync pair not found: {}", id),
            "status": 404
        })
    ))
}

/// Toggle a sync pair's active status
pub async fn toggle_pair(
    id: web::Path<Uuid>,
    req: web::Json<ToggleSyncPairRequest>,
    state: web::Data<AppState>,
    extensions: web::ReqData<Claims>,
) -> impl Responder {
    // Get user info from JWT claims
    let claims = extensions.into_inner();
    
    // Call the service
    match state.services.sync_service.toggle_sync_pair(*id, req.is_active).await {
        Ok(sync_pair) => {
            // Create audit log
            // In a real implementation, this would store in the database
            log::info!(
                "Sync pair {} {} by user {}",
                sync_pair.id,
                if req.is_active { "activated" } else { "deactivated" },
                claims.sub
            );
            
            HttpResponse::Ok().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(e) => {
            log::error!("Failed to toggle sync pair {}: {}", id, e);
            
            // Return appropriate error status
            let status_code = match e {
                Error::NotFound(_) => 404,
                _ => 500,
            };
            
            HttpResponse::build(actix_web::http::StatusCode::from_u16(status_code).unwrap())
                .json(web::Json(
                    serde_json::json!({
                        "error": format!("Failed to toggle sync pair: {}", e),
                        "status": status_code
                    })
                ))
        }
    }
}