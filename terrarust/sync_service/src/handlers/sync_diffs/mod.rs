use actix_web::{web, HttpResponse, Responder};
use common::error::Error;
use common::models::sync_operation::SyncDiff;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncDiffResponse {
    pub diff: SyncDiff,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SyncDiffsResponse {
    pub diffs: Vec<SyncDiff>,
    pub total_count: i64,
}

#[derive(Debug, Deserialize)]
pub struct SyncDiffQuery {
    pub page: Option<i64>,
    pub per_page: Option<i64>,
    pub sync_operation_id: Option<Uuid>,
    pub entity_type: Option<String>,
    pub change_type: Option<String>,
    pub sync_status: Option<String>,
    pub has_error: Option<bool>,
}

pub async fn get_all_diffs(
    query: web::Query<SyncDiffQuery>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::Ok().json(SyncDiffsResponse {
        diffs: Vec::new(),
        total_count: 0,
    })
}

pub async fn get_diff(
    id: web::Path<Uuid>,
    state: web::Data<AppState>,
) -> impl Responder {
    // In a real implementation, this would query the database
    // For now, return a stub response
    HttpResponse::NotFound().json(web::Json(
        serde_json::json!({
            "error": format!("Sync diff not found: {}", id),
            "status": 404
        })
    ))
}