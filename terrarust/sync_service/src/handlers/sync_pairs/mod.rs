use actix_web::{web, HttpResponse, Responder, http::StatusCode};
use common::error::{Error, Result};
use common::models::sync_pair::{SyncPair, NewSyncPair, SyncPairUpdate};
use diesel::prelude::*;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;
use crate::database::sync_pairs::{create_sync_pair, get_sync_pair_by_id, get_sync_pairs_with_filters, update_sync_pair_by_id, delete_sync_pair_by_id, toggle_sync_pair_status};

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
    pub source_system: Option<String>,
    pub target_system: Option<String>,
    pub is_active: Option<bool>,
    pub county_id: Option<String>,
}

pub async fn get_sync_pairs(
    query: web::Query<SyncPairQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    let page = query.page.unwrap_or(1);
    let per_page = query.per_page.unwrap_or(20);
    
    match get_sync_pairs_with_filters(
        &state.database,
        page,
        per_page,
        query.source_system.as_deref(),
        query.target_system.as_deref(),
        query.is_active,
        query.county_id.as_deref(),
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

pub async fn create_sync_pair(
    new_pair: web::Json<NewSyncPair>,
    state: web::Data<AppState>,
) -> impl Responder {
    // Track metrics
    state.telemetry.sync_operations_total.inc();
    
    match create_sync_pair(&state.database, new_pair.into_inner()).await {
        Ok(sync_pair) => {
            // Create audit entry
            log::info!("Created sync pair: {}", sync_pair.id);
            
            HttpResponse::Created().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(e) => {
            log::error!("Failed to create sync pair: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to create sync pair: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn get_sync_pair(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    match get_sync_pair_by_id(&state.database, *id).await {
        Ok(sync_pair) => {
            HttpResponse::Ok().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync pair not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to get sync pair: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to get sync pair: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn update_sync_pair(
    id: web::Path<Uuid>,
    update: web::Json<SyncPairUpdate>,
    state: web::Data<AppState>,
) -> impl Responder {
    match update_sync_pair_by_id(&state.database, *id, update.into_inner()).await {
        Ok(sync_pair) => {
            log::info!("Updated sync pair: {}", id);
            
            HttpResponse::Ok().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync pair not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to update sync pair: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to update sync pair: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn delete_sync_pair(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    match delete_sync_pair_by_id(&state.database, *id).await {
        Ok(_) => {
            log::info!("Deleted sync pair: {}", id);
            
            HttpResponse::NoContent().finish()
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync pair not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to delete sync pair: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to delete sync pair: {}", e),
                    "status": 500
                })
            ))
        }
    }
}

pub async fn toggle_sync_pair(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    match toggle_sync_pair_status(&state.database, *id).await {
        Ok(sync_pair) => {
            log::info!("Toggled sync pair status: {}, is_active: {}", id, sync_pair.is_active);
            
            HttpResponse::Ok().json(SyncPairResponse {
                sync_pair,
            })
        },
        Err(Error::NotFound(_)) => {
            HttpResponse::NotFound().json(web::Json(
                serde_json::json!({
                    "error": format!("Sync pair not found: {}", id),
                    "status": 404
                })
            ))
        },
        Err(e) => {
            log::error!("Failed to toggle sync pair status: {}", e);
            HttpResponse::InternalServerError().json(web::Json(
                serde_json::json!({
                    "error": format!("Failed to toggle sync pair status: {}", e),
                    "status": 500
                })
            ))
        }
    }
}