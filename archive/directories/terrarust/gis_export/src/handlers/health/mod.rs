use actix_web::{web, HttpResponse, Responder};
use serde::{Deserialize, Serialize};
use crate::AppState;

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub status: String,
    pub database: String,
    pub export_service: String,
    pub version: String,
    pub uptime_seconds: u64,
}

pub async fn health_check(state: web::Data<AppState>) -> impl Responder {
    // Check database connection
    let db_status = match state.database.get_connection() {
        Ok(_) => "up",
        Err(_) => "down",
    };
    
    // Check export service status
    let export_service_status = "up"; // In a real implementation, we would check internal state
    
    // Determine overall status
    let status = if db_status == "up" && export_service_status == "up" {
        "healthy"
    } else {
        "unhealthy"
    };
    
    // In a real implementation, track uptime
    let uptime_seconds = 0;
    
    HttpResponse::Ok().json(HealthCheckResponse {
        status: status.to_string(),
        database: db_status.to_string(),
        export_service: export_service_status.to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        uptime_seconds,
    })
}