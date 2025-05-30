use actix_web::{web, HttpResponse, Responder, get};
use serde_json::json;
use terrafusion_common::{Result, Error};
use terrafusion_common::models::{HealthStatus, HealthCheck, ServiceHealth};
use crate::AppState;

/// Configure system routes
pub fn configure(cfg: &mut web::ServiceConfig) {
    cfg.service(health_check)
       .service(metrics)
       .service(liveness_check)
       .service(readiness_check);
}

/// Health check endpoint
#[get("/health")]
async fn health_check(app_state: web::Data<AppState>) -> Result<impl Responder> {
    let now = chrono::Utc::now();
    
    // Check database connectivity
    let db_status = match sqlx::query("SELECT 1")
        .execute(&app_state.db_pool)
        .await
    {
        Ok(_) => HealthStatus::Up,
        Err(_) => HealthStatus::Down,
    };
    
    // Check export directories
    let dirs_status = if app_state.config.exports_directory.exists() && 
                         app_state.config.temp_directory.exists() {
        HealthStatus::Up
    } else {
        HealthStatus::Down
    };
    
    let services = vec![
        ServiceHealth {
            name: "database".to_string(),
            status: db_status,
            version: None,
            latency_ms: None,
            message: None,
            last_check: now,
        },
        ServiceHealth {
            name: "file_system".to_string(),
            status: dirs_status,
            version: None,
            latency_ms: None,
            message: None,
            last_check: now,
        },
    ];
    
    let overall_status = if services.iter().all(|s| s.status == HealthStatus::Up) {
        HealthStatus::Up
    } else if services.iter().any(|s| s.status == HealthStatus::Up) {
        HealthStatus::Degraded
    } else {
        HealthStatus::Down
    };
    
    let health_check = HealthCheck {
        status: overall_status,
        version: env!("CARGO_PKG_VERSION").to_string(),
        services,
        timestamp: now,
    };
    
    Ok(web::Json(health_check))
}

/// Prometheus metrics endpoint
#[get("/metrics")]
async fn metrics(app_state: web::Data<AppState>) -> Result<impl Responder> {
    let metrics_data = format!(
        "# HELP gis_exports_total Total number of GIS exports\n\
         # TYPE gis_exports_total counter\n\
         gis_exports_total{{status=\"completed\"}} 0\n\
         gis_exports_total{{status=\"failed\"}} 0\n\
         \n\
         # HELP gis_export_file_size_bytes Size of generated export files\n\
         # TYPE gis_export_file_size_bytes histogram\n\
         gis_export_file_size_bytes_bucket{{le=\"1048576\"}} 0\n\
         gis_export_file_size_bytes_bucket{{le=\"10485760\"}} 0\n\
         gis_export_file_size_bytes_bucket{{le=\"104857600\"}} 0\n\
         gis_export_file_size_bytes_bucket{{le=\"+Inf\"}} 0\n\
         gis_export_file_size_bytes_sum 0\n\
         gis_export_file_size_bytes_count 0\n\
         \n\
         # HELP gis_export_duration_seconds Time spent processing exports\n\
         # TYPE gis_export_duration_seconds histogram\n\
         gis_export_duration_seconds_bucket{{le=\"30\"}} 0\n\
         gis_export_duration_seconds_bucket{{le=\"60\"}} 0\n\
         gis_export_duration_seconds_bucket{{le=\"300\"}} 0\n\
         gis_export_duration_seconds_bucket{{le=\"+Inf\"}} 0\n\
         gis_export_duration_seconds_sum 0\n\
         gis_export_duration_seconds_count 0\n"
    );
    
    Ok(HttpResponse::Ok()
        .content_type("text/plain; charset=utf-8")
        .body(metrics_data))
}

/// Kubernetes liveness probe endpoint
#[get("/liveness")]
async fn liveness_check() -> Result<impl Responder> {
    Ok(web::Json(json!({
        "status": "UP",
        "timestamp": chrono::Utc::now()
    })))
}

/// Kubernetes readiness probe endpoint
#[get("/readiness")]
async fn readiness_check(app_state: web::Data<AppState>) -> Result<impl Responder> {
    // Check if the service is ready to handle requests
    let db_ready = sqlx::query("SELECT 1")
        .execute(&app_state.db_pool)
        .await
        .is_ok();
    
    let dirs_ready = app_state.config.exports_directory.exists() && 
                     app_state.config.temp_directory.exists();
    
    if db_ready && dirs_ready {
        Ok(web::Json(json!({
            "status": "READY",
            "checks": {
                "database": "UP",
                "file_system": "UP"
            },
            "timestamp": chrono::Utc::now()
        })))
    } else {
        Err(Error::ServiceUnavailable("Service not ready".to_string()))
    }
}