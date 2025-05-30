use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub status: String,
    pub database: String,
    pub sync_engine: String,
    pub version: String,
    pub uptime_seconds: u64,
    pub active_operations: i32,
}

pub async fn health_check(state: web::Data<AppState>) -> impl Responder {
    // Check database connection
    let db_status = match state.database.get_connection() {
        Ok(_) => "up",
        Err(_) => "down",
    };
    
    // Get active operations count for sync engine status
    let active_ops = match state.sync_engine.get_active_operations().await {
        Ok(ops) => ops.len() as i32,
        Err(_) => -1, // Error getting active operations
    };
    
    // Determine sync engine status
    let sync_engine_status = if db_status == "up" && active_ops >= 0 {
        "up"
    } else {
        "degraded"
    };
    
    // Determine overall status
    let status = if db_status == "up" && sync_engine_status == "up" {
        "healthy"
    } else if db_status == "down" {
        "unhealthy"
    } else {
        "degraded"
    };
    
    // Get uptime
    let uptime_seconds = state.telemetry.uptime_seconds();
    
    HttpResponse::Ok().json(HealthCheckResponse {
        status: status.to_string(),
        database: db_status.to_string(),
        sync_engine: sync_engine_status.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        uptime_seconds,
        active_operations: active_ops,
    })
}