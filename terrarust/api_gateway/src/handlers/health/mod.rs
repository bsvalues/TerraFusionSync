use actix_web::{web, HttpResponse, Responder};
use crate::AppState;
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct HealthCheckResponse {
    pub status: String,
    pub api_gateway: ServiceStatus,
    pub sync_service: ServiceStatus,
    pub database: ServiceStatus,
    pub timestamp: chrono::DateTime<chrono::Utc>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub status: String,
    pub version: Option<String>,
    pub uptime_seconds: Option<i64>,
    pub details: Option<serde_json::Value>,
}

pub async fn health_check(state: web::Data<AppState>) -> impl Responder {
    // Check database connection
    let db_status = match state.database.get_connection() {
        Ok(_) => ServiceStatus {
            status: "up".to_string(),
            version: Some("PostgreSQL 14.0".to_string()), // In a real implementation, get from DB
            uptime_seconds: None,
            details: None,
        },
        Err(e) => ServiceStatus {
            status: "down".to_string(),
            version: None,
            uptime_seconds: None,
            details: Some(serde_json::json!({
                "error": format!("{}", e)
            })),
        },
    };
    
    // Check SyncService connection
    // In a real implementation, this would make an HTTP request to the SyncService health endpoint
    let sync_service_status = ServiceStatus {
        status: "unknown".to_string(), // We would check this in a real implementation
        version: None,
        uptime_seconds: None,
        details: None,
    };
    
    // API Gateway status (we're running, so it's up)
    let api_gateway_status = ServiceStatus {
        status: "up".to_string(),
        version: Some(env!("CARGO_PKG_VERSION").to_string()),
        uptime_seconds: Some(0), // In a real implementation, track uptime
        details: None,
    };
    
    // Overall status depends on components
    let overall_status = if db_status.status == "up" && sync_service_status.status != "down" {
        "healthy"
    } else if db_status.status == "down" {
        "critical"
    } else {
        "degraded"
    };
    
    HttpResponse::Ok().json(HealthCheckResponse {
        status: overall_status.to_string(),
        api_gateway: api_gateway_status,
        sync_service: sync_service_status,
        database: db_status,
        timestamp: chrono::Utc::now(),
    })
}